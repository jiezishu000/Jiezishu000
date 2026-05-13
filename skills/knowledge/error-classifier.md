# 错误自动分类器

## 错误分类

| 类型 | 匹配模式 | 修复策略 |
|------|----------|----------|
| network_timeout | timeout/ConnectionError/ETIMEDOUT | 切换镜像源/代理 |
| dependency_missing | No module named/ImportError | 补全依赖安装命令 |
| git_clone_failed | Failed to connect to github.com/443 | 加ghproxy前缀 |
| npm_install_fail | npm ERR!/ECONNREFUSED | 切npmmirror源 |
| pip_install_fail | pip._vendor.urllib3/RetryError | 切清华源+增加timeout |
| memory_oom | MemoryError/killed | 减小批处理/gc回收 |
| rate_limit | 429/Too Many Requests | 降低并发/加延迟 |
| dns_fail | Name or service not known/getaddrinfo | 换DNS(114.114.114.114) |

## 修复流程
```
捕获错误 → 正则匹配分类 → 查表选策略 → 应用修复 → 重试
三轮迭代仍失败 → 切换Plan B（如离线模式）
```
