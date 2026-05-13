# 环境自检模块 — 每次启动自动执行

## 检测顺序
1. 网络诊断 → 2. 工具链检查 → 3. 镜像源配置 → 4. 输出报告

## 网络检测
```
ping github.com → 通/不通
ping registry.npmmirror.com → 通/不通  
ping pypi.tuna.tsinghua.edu.cn → 通/不通
```

## 模式切换
- **全通** → 直连模式
- **GitHub不通其余通** → 镜像模式（ghproxy + npmmirror + 清华源）
- **全不通** → 离线模式（纯本地，预缓存清单）

## 镜像Fallback清单
| 服务 | 默认 | Fallback |
|------|------|----------|
| git clone | github.com | ghproxy.com/https://github.com/xxx |
| npm | npmjs.org | registry.npmmirror.com |
| pip | pypi.org | pypi.tuna.tsinghua.edu.cn |
| Docker | docker.io | registry.cn-hangzhou.aliyuncs.com |
