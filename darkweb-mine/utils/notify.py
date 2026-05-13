"""
暗网帝国 - 通知模块
日志 + 可选Telegram通知
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(log_file: str = "data/miner.log",
                 level: str = "INFO") -> logging.Logger:
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)

    logger = logging.getLogger("EmpireMiner")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        fmt = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger


class DiscoveryReport:
    """发现报告格式化"""

    @staticmethod
    def format_table(discoveries: list) -> str:
        """将发现列表格式化为可读表格"""
        if not discoveries:
            return "本轮无新发现。"

        lines = [
            "=" * 72,
            f"  暗网帝国数字考古报告 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 72,
        ]

        for i, d in enumerate(discoveries, 1):
            lines.append(f"\n--- 发现 #{i} ---")
            lines.append(f"  模块:     {d.get('module', '?')}")
            lines.append(f"  分类:     {d.get('category', '?')}")
            lines.append(f"  类型:     {d.get('asset_type', '?')}")
            lines.append(f"  价值:     {d.get('asset_value', '?')}")
            lines.append(f"  置信度:   {d.get('confidence', 0):.0%}")
            lines.append(f"  来源:     {d.get('source_url', '?')}")
            lines.append(f"  时间:     {d.get('discovered_at', '?')}")

        lines.append("\n" + "=" * 72)
        return "\n".join(lines)
