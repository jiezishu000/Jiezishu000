#!/usr/bin/env python3
"""
============================================
 暗网帝国数字考古矿机 - 主控制器
 全自动运行 · 7×24无人值守
============================================

用法:
  python main.py              # 运行一轮全部扫描
  python main.py --once       # 单次运行后退出
  python main.py --report     # 仅查看最近发现
  python main.py --stats      # 查看扫描统计
  python main.py --setup      # 初始化环境
"""

import sys
import os
import time
import argparse
import yaml
from pathlib import Path

from utils.db import EmpireDB
from utils.notify import setup_logger, DiscoveryReport
from scanners.github_secrets import GitHubSecretScanner
from scanners.chain_assets import ChainAssetScanner
from scanners.domain_heritage import DomainHeritageScanner


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if not os.path.exists(config_path):
        print(f"[错误] 配置文件不存在: {config_path}")
        print("请先复制 config.yaml 并填写必要参数")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def print_banner():
    """打印帝国Banner"""
    banner = r"""
    ╔══════════════════════════════════════════════════════╗
    ║       暗 网 帝 国 数 字 考 古 矿 机  v1.0           ║
    ║     Empire Digital Archaeology Mining Engine        ║
    ║       全自动 · 无人值守 · 7×24 · 永不停机           ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)


def run_once(config: dict, db: EmpireDB, logger) -> dict:
    """执行一轮全模块扫描"""
    results = {}

    # 模块1: GitHub密钥扫描
    if config.get("github", {}).get("enabled", True):
        try:
            scanner = GitHubSecretScanner(config, db, logger)
            results["github"] = scanner.run()
        except Exception as e:
            logger.error(f"GitHub扫描器异常: {e}")
            results["github"] = {"error": str(e)}

    # 模块2: 链上资产检漏
    if config.get("chain", {}).get("enabled", True):
        try:
            scanner = ChainAssetScanner(config, db, logger)
            results["chain"] = scanner.run()
        except Exception as e:
            logger.error(f"链上检漏器异常: {e}")
            results["chain"] = {"error": str(e)}

    # 模块3: 域名遗产监控
    if config.get("domain", {}).get("enabled", True):
        try:
            scanner = DomainHeritageScanner(config, db, logger)
            results["domain"] = scanner.run()
        except Exception as e:
            logger.error(f"域名扫描器异常: {e}")
            results["domain"] = {"error": str(e)}

    return results


def show_report(db: EmpireDB):
    """显示最近发现"""
    discoveries = db.get_recent_discoveries(50)
    formatted = []
    for d in discoveries:
        formatted.append({
            "id": d[0],
            "module": d[1],
            "category": d[2],
            "source_url": d[3],
            "asset_type": d[5],
            "asset_value": d[6],
            "confidence": d[8],
            "discovered_at": d[9],
        })
    print(DiscoveryReport.format_table(formatted))


def show_stats(db: EmpireDB):
    """显示统计信息"""
    stats = db.get_scan_stats()
    print("\n  ╔══════════════════════════════════╗")
    print("  ║     帝 国 矿 机 统 计           ║")
    print("  ╚══════════════════════════════════╝\n")
    print(f"  {'模块':<20} {'扫描次数':>8} {'累计发现':>8}")
    print(f"  {'-'*40}")
    total_scans = 0
    total_finds = 0
    for module, scans, found in stats:
        print(f"  {module:<20} {scans:>8} {found or 0:>8}")
        total_scans += scans
        total_finds += (found or 0)
    print(f"  {'-'*40}")
    print(f"  {'总计':<20} {total_scans:>8} {total_finds:>8}")


def setup_environment():
    """初始化运行环境"""
    print("\n[帝国矿机] 初始化环境...\n")

    # 创建目录
    for d in ["data", "scanners", "utils"]:
        os.makedirs(d, exist_ok=True)
        print(f"  ✓ 目录: {d}")

    # 检查Python版本
    v = sys.version_info
    if v.major >= 3 and v.minor >= 8:
        print(f"  ✓ Python: {v.major}.{v.minor}.{v.micro}")
    else:
        print(f"  ✗ Python版本过低: {v.major}.{v.minor} (需要3.8+)")
        sys.exit(1)

    # 安装依赖
    print("\n  安装依赖...")
    ret = os.system(
        "pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q"
    )
    if ret == 0:
        print("  ✓ 依赖安装完成")
    else:
        print("  ✗ 依赖安装失败，请手动执行: pip install -r requirements.txt")

    # 检查配置文件
    if os.path.exists("config.yaml"):
        print("  ✓ 配置文件: config.yaml")
    else:
        print("  ✗ 需要 config.yaml 配置文件")

    print("\n[帝国矿机] 初始化完成。运行 'python main.py' 启动。\n")


def main():
    parser = argparse.ArgumentParser(
        description="暗网帝国数字考古矿机",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--once", action="store_true", help="单次运行后退出")
    parser.add_argument("--report", action="store_true", help="查看最近发现")
    parser.add_argument("--stats", action="store_true", help="查看扫描统计")
    parser.add_argument("--setup", action="store_true", help="初始化环境")
    parser.add_argument("--loop", action="store_true", help="持续循环运行")
    parser.add_argument(
        "--interval", type=int, default=3600,
        help="循环间隔(秒), 默认3600"
    )

    args = parser.parse_args()

    # 环境初始化
    if args.setup:
        setup_environment()
        return

    print_banner()

    # 加载配置
    config = load_config()
    log_level = config.get("output", {}).get("log_level", "INFO")
    log_file = config.get("output", {}).get("log_file", "data/miner.log")

    # 初始化
    logger = setup_logger(log_file, log_level)
    db = EmpireDB(config.get("output", {}).get("db_file", "data/empire.db"))

    # 报表模式
    if args.report:
        show_report(db)
        db.close()
        return

    # 统计模式
    if args.stats:
        show_stats(db)
        db.close()
        return

    # 运行模式
    logger.info("=" * 50)
    logger.info("帝国矿机启动")
    logger.info("=" * 50)

    try:
        if args.loop:
            logger.info(f"持续运行模式，间隔 {args.interval} 秒")
            while True:
                results = run_once(config, db, logger)
                total_found = sum(r.get("found", 0) for r in results.values())
                logger.info(f"本轮完成，共发现 {total_found} 条。等待 {args.interval} 秒...")
                time.sleep(args.interval)
        else:
            results = run_once(config, db, logger)

        # 显示本轮汇总
        total_found = sum(r.get("found", 0) for r in results.values())
        print(f"\n  >>> 本轮扫描完成，共发现 {total_found} 条新线索 <<<\n")

    except KeyboardInterrupt:
        logger.info("收到中断信号，安全退出")
        print("\n帝国矿机已安全停机。")
    except Exception as e:
        logger.error(f"主循环异常: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
