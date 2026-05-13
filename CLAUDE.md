# CLAUDE.md — 统一工程操作系统 V3

## 前置环境约束（每次自动生效）

### 硬件基线
- 目标机器：2000元级别笔记本，8GB内存，百兆宽带
- 所有代码必须适配低配环境：冷启动<30秒，内存占用<500MB
- 禁止假设用户有GPU/大内存/高速SSD

### 网络约束（国内环境）
- GitHub直连大概率失败，所有 git clone 自动加 ghproxy.com 前缀
- npm 强制使用 npmmirror.com 镜像
- pip 强制使用清华源 pypi.tuna.tsinghua.edu.cn
- 所有外部URL访问需考虑超时和fallback策略
- BlockChain RPC默认使用国内可通的测试网节点

### 输出强制规范
- 代码必须是"复制即运行"级别：完整依赖声明 + 环境检测 + 配置文件
- 禁止省略 import/require/错误处理
- 禁止用注释代替实现
- 每个输出末尾附带测试命令和预期结果

### 自我迭代循环
- 代码执行失败 → 自动捕获错误 → 分析根因 → 修复 → 重试
- 每次修复需说明：错误原因 + 修复策略 + 预防措施
- 三轮迭代仍失败 → 切换策略，不做无效重复

## 元技能生态
- **gstack** (46 SKILL.md): 23角色虚拟工程团队，按场景编排
- **find-skills**: 智能技能发现
- **fullstack-assistant**: V3 统一系统指令

## 工作流
CheckEnv → Think → Plan → Build → Test → Fix → Ship → Reflect

## 质量门禁
9项：编译/Lint/类型/单测/集成/安全/性能/文档/Commit规范
