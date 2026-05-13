"""
暗网帝国 - 域名/TLS遗产监控器
监控: 即将过期的高价值域名、过期SSL证书对应的存活服务
"""

import json
import ssl
import socket
import urllib.request
from datetime import datetime, timedelta

from utils.db import EmpireDB


class DomainHeritageScanner:
    """域名遗产考古引擎"""

    def __init__(self, config: dict, db: EmpireDB, logger):
        self.cfg = config.get("domain", {})
        self.db = db
        self.log = logger

    def check_ssl_expiry(self, domain: str) -> dict:
        """检查域名的SSL证书到期时间"""
        result = {"domain": domain, "expired": False, "expires_in_days": 0, "issuer": ""}
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    expiry_str = cert.get("notAfter", "")
                    if expiry_str:
                        expiry = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                        result["expires_in_days"] = (expiry - datetime.now()).days
                        result["expired"] = result["expires_in_days"] <= 0
                        issuer = cert.get("issuer", [])
                        for item in issuer:
                            if item[0][0] == "organizationName":
                                result["issuer"] = item[0][1]
        except Exception as e:
            self.log.debug(f"SSL检查 {domain} 失败: {e}")
        return result

    def check_domain_whois(self, domain: str) -> dict:
        """查询域名WHOIS到期信息 (简化版)"""
        result = {"domain": domain, "expires_in_days": 999, "registered": True}
        try:
            # 使用RDAP协议获取域名信息
            url = f"https://rdap.verisign.com/domain/v1/{domain}"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                for event in data.get("events", []):
                    if event.get("eventAction") == "expiration":
                        expiry = datetime.fromisoformat(
                            event["eventDate"].replace("Z", "+00:00")
                        )
                        result["expires_in_days"] = (
                            expiry.replace(tzinfo=None) - datetime.now()
                        ).days
        except Exception as e:
            self.log.debug(f"WHOIS查询 {domain} 失败: {e}")
        return result

    def generate_candidate_domains(self) -> list:
        """生成候选高价值域名列表"""
        candidates = []
        tlds = self.cfg.get("tlds", [".com", ".io", ".ai"])
        keywords = self.cfg.get("keywords", ["defi", "swap", "chain", "nft"])

        for kw in keywords[:5]:
            for tld in tlds[:3]:
                candidates.append(f"{kw}{tld}")

        return candidates

    def scan_domains(self) -> list:
        """扫描候选域名"""
        findings = []
        expire_threshold = self.cfg.get("expire_days_before", 7)
        candidates = self.generate_candidate_domains()

        for domain in candidates:
            self.log.debug(f"  检查域名: {domain}")
            whois = self.check_domain_whois(domain)

            if whois["expires_in_days"] <= expire_threshold:
                findings.append({
                    "module": "domain_heritage",
                    "category": "expiring_domain",
                    "source_url": f"https://www.whois.com/whois/{domain}",
                    "raw_data": whois,
                    "asset_type": "domain",
                    "asset_value": domain,
                    "confidence": 0.6,
                    "discovered_at": datetime.now().isoformat()
                })
                self.log.info(f"  发现即将过期域名: {domain} ({whois['expires_in_days']}天后)")

            # 同时检查SSL证书
            ssl_info = self.check_ssl_expiry(domain)
            if ssl_info["expires_in_days"] <= 30 and ssl_info["expires_in_days"] > -365:
                findings.append({
                    "module": "domain_heritage",
                    "category": "expiring_ssl",
                    "source_url": f"https://{domain}",
                    "raw_data": ssl_info,
                    "asset_type": "ssl_cert",
                    "asset_value": f"{domain} SSL证书 {ssl_info['expires_in_days']}天后过期",
                    "confidence": 0.4,
                    "discovered_at": datetime.now().isoformat()
                })

        return findings

    def run(self) -> dict:
        """执行一轮域名遗产扫描"""
        self.log.info("[域名遗产扫描器] 启动")
        scan_id = self.db.start_scan("domain_heritage")
        findings = self.scan_domains()
        total_found = 0

        for f in findings:
            self.db.add_discovery(**f)
            total_found += 1

        self.db.finish_scan(scan_id, total_found, scanned=len(self.generate_candidate_domains()))
        self.log.info(f"[域名遗产扫描器] 完成: 发现 {total_found} 条")
        return {"found": total_found, "errors": 0}
