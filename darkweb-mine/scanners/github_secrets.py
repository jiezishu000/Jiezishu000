"""
暗网帝国 - GitHub密钥泄漏扫描器
扫描公开仓库中意外提交的私钥/API Key/助记词/RPC端点
"""

import re
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path

from utils.db import EmpireDB
from utils.validator import classify_finding


class GitHubSecretScanner:
    """GitHub代码库密钥考古引擎"""

    BASE_SEARCH = "https://api.github.com/search/code"
    BASE_CONTENT = "https://api.github.com/repos"

    def __init__(self, config: dict, db: EmpireDB, logger):
        self.cfg = config
        self.db = db
        self.log = logger
        self.token = config.get("github", {}).get("token", "")
        self.keywords = config.get("github", {}).get("keywords", [])
        self.max_repos = config.get("github", {}).get("max_repos_per_scan", 50)
        self.session_count = 0

    def _api_request(self, url: str) -> dict:
        """带限流保护的GitHub API请求"""
        headers = {
            "User-Agent": "Empire-Miner/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                remaining = resp.headers.get("X-RateLimit-Remaining", "?")
                self.log.debug(f"API剩余限额: {remaining}")
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                reset_time = int(e.headers.get("X-RateLimit-Reset", 0))
                wait = max(reset_time - time.time(), 0) + 1
                if wait > 300:
                    self.log.warning(f"API限额耗尽，需等待 {wait:.0f}秒")
                    return {}
                self.log.info(f"触发限流，等待 {wait:.0f} 秒...")
                time.sleep(min(wait, 60))
                return self._api_request(url)
            elif e.code == 422:
                self.log.debug(f"搜索查询过长，跳过")
                return {}
            else:
                self.log.error(f"API错误 HTTP {e.code}: {url[:80]}")
                return {}
        except Exception as e:
            self.log.error(f"请求失败: {e}")
            return {}

    def scan_keyword(self, keyword: str) -> list:
        """扫描单个关键词，返回发现列表"""
        findings = []
        quoted_kw = urllib.parse.quote(f'"{keyword}"')
        url = f"{self.BASE_SEARCH}?q={quoted_kw}+language:python+language:javascript+language:typescript+language:solidity+language:go+language:rust&per_page=30"

        result = self._api_request(url)
        if not result:
            return findings

        items = result.get("items", [])
        self.session_count += 1

        for item in items:
            repo_full = item.get("repository", {}).get("full_name", "")
            path = item.get("path", "")
            html_url = item.get("html_url", "")
            repo_url = f"https://github.com/{repo_full}"

            # 获取文件内容
            content = self._get_file_content(repo_full, path)
            if not content:
                continue

            # AI分类
            classification = classify_finding(content)
            if classification["confidence"] < 0.3:
                continue

            # 去重检查
            if self._is_duplicate(html_url, classification["type"]):
                continue

            finding = {
                "module": "github_secrets",
                "category": classification["type"],
                "source_url": html_url,
                "raw_data": {
                    "repo": repo_url,
                    "file": path,
                    "matched": classification.get("matched", ""),
                    "snippet": content[:500],
                    "keyword": keyword,
                },
                "asset_type": classification["type"],
                "asset_value": classification["potential_value"],
                "confidence": classification["confidence"],
                "discovered_at": datetime.now().isoformat()
            }

            self.log.info(f"  发现! {classification['type']} -> {html_url}")
            findings.append(finding)

        time.sleep(2)  # 礼貌限速
        return findings

    def _get_file_content(self, repo_full: str, path: str) -> str:
        """获取仓库文件原始内容"""
        url = f"{self.BASE_CONTENT}/{repo_full}/contents/{urllib.parse.quote(path)}"
        result = self._api_request(url)
        if not result or "content" not in result:
            return ""

        import base64
        try:
            return base64.b64decode(result["content"]).decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _is_duplicate(self, url: str, asset_type: str) -> bool:
        """检查是否已记录过"""
        try:
            cur = self.db.conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM discoveries WHERE source_url=? AND asset_type=?",
                (url, asset_type)
            )
            return cur.fetchone()[0] > 0
        except Exception:
            return False

    def run(self) -> dict:
        """执行一轮完整扫描"""
        if not self.token:
            self.log.warning("[GitHub扫描器] 未配置token，跳过。请在config.yaml中填写github.token")
            self.log.warning("  获取免费token: https://github.com/settings/tokens (无需任何权限)")
            return {"found": 0, "errors": 0}

        self.log.info(f"[GitHub扫描器] 启动，{len(self.keywords)}个关键词")
        scan_id = self.db.start_scan("github_secrets")
        total_found = 0
        error_count = 0

        for kw in self.keywords[:20]:  # 每轮只扫前20个关键词以免超时
            try:
                findings = self.scan_keyword(kw)
                for f in findings:
                    self.db.add_discovery(**f)
                    total_found += 1
            except Exception as e:
                error_count += 1
                self.log.error(f"扫描'{kw}'出错: {e}")
                if error_count > 5:
                    self.log.error("错误过多，中止本轮")
                    break

        self.db.finish_scan(scan_id, total_found, scanned=len(self.keywords[:20]))
        self.log.info(f"[GitHub扫描器] 完成: 发现 {total_found} 条, 错误 {error_count}")
        return {"found": total_found, "errors": error_count}
