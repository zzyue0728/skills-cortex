# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**cortex** 是一个面向 AI 编程终端的项目上下文管理技能体系，解决跨会话的上下文丢失问题。由 5 个技能组成，通过 `cortex` 主调度器统一入口。五个技能目录互为兄弟目录，拷贝到任意 AI 编程终端的 skills 目录下即可使用。

核心能力：从对话中提取结构化上下文信息（设计意图、已否决方案、已知坑位、当前断点、方向约束），保存为快照文件，并支持跨会话加载、压缩整理和文档同步。

## 技能架构

```
skills/
├── cortex/SKILL.md          主调度器，解析 -c -d -i -m 参数并分发
├── cortex-context/SKILL.md  从对话提取 5 维度信息，保存快照到 .cortex/
├── cortex-docsync/SKILL.md  同步 docs/ 文档与 CORTEX.md 索引
├── cortex-index/SKILL.md    审查并压缩快照，全局条目写入 CORTEX.md
│   └── scripts/
│       ├── server.py        HTTP 服务器（提供审查页面 + 接收保存结果）
│       └── review.html      审查页面（纯前端，逐条标记删除/全局）
└── cortex-memory/SKILL.md   加载 .cortex/ 快照 + CORTEX.md 到上下文
```

**路径约定**：所有文件引用基于"五个技能目录互为兄弟目录"的约定。当前技能通过 `../<skill-name>/` 访问兄弟目录。

### 数据流

```
对话 → cortex-context → .cortex/YYYY-MM-DD_HH-MM.md（快照文件）
                          └── .cortex/_index.md（索引表）
                          └── CORTEX.md（全局条目 + 文档索引）

.cortex/ 快照 → cortex-index → 审查页面（浏览器）→ 压缩快照 + 全局条目写入 CORTEX.md

.cortex/ 快照 + CORTEX.md → cortex-memory → 注入 AI 上下文
```

### 项目运行时目录

| 路径 | 说明 |
|------|------|
| `.cortex/` | 快照存储目录（初始化时创建） |
| `.cortex/_index.md` | 快照索引表，追踪元信息和状态（active / compressed） |
| `.cortex/YYYY-MM-DD_HH-MM.md` | 单个快照文件，5 维度 Markdown 格式 |
| `.cortex/collate/` | 压缩审查工作目录，server.py 在此运行，临时文件在此生成 |
| `.cortex/collate/server.py` | 从 cortex-index/scripts/ 拷贝而来 |
| `.cortex/collate/server.pid` | server.py 运行时 PID（启动时创建，退出时清理） |
| `.cortex/collate/server.port` | server.py 实际监听端口（启动时创建，退出时清理） |
| `CORTEX.md` | 项目级用户规则 + 全局条目 + 文档索引表 |
| `docs/` | 项目文档目录 |

## 5 维度上下文模型

每个快照包含以下维度，判断标准：缺少该信息是否会让 AI 做出错误决策？

| 维度 | 用途 | 防什么 |
|------|------|--------|
| 设计意图 | 记录方案选择背后的原因 | 防止 AI 重构看似"奇怪"的代码 |
| 已否决方案 | 记录明确拒绝过的方案 | 防止 AI 重复提议已否决的方向 |
| 已知坑位 | 记录踩过的坑和解决方案 | 防止 AI 用同样方式再踩一次 |
| 当前断点 | 记录做到哪了、停在哪了 | 防止 AI 不清楚从哪接手 |
| 方向约束 | 记录未成文的边界约定 | 防止 AI 提议违背既定方向 |

## 开发指南

- **技能文件格式**：每个 SKILL.md 包含 YAML 前端元数据（name、description）和 Markdown 正文。
- **Shell 命令**：所有可执行命令使用 bash 语法，兼容 Windows Git Bash / Linux / macOS。不依赖 PowerShell cmdlet。
- **脚本语言**：`server.py` 使用 Python 标准库（`http.server` + `json`），无需外部依赖。启动时写入 PID 到 `server.pid`、端口到 `server.port`，退出时自动清理。
- **审查页面**：`review.html` 纯前端 HTML，无框架依赖，通过 `__REVIEW_DATA__` 占位符注入 JSON 数据。支持 POST `/save` 保存结果和 POST `/shutdown` 手动关闭服务器。
- **零构建依赖**：本项目不含 `package.json`、`requirements.txt` 或任何构建工具。
- **路径自发现**：技能间引用通过兄弟目录相对路径约定完成，不硬编码任何绝对路径（如 `~/.config/`、`$env:USERPROFILE`）。

## 常用操作

### 初始化 cortex 目录结构
```
cortex  # 无参数 → 创建 .cortex/, .cortex/_index.md, CORTEX.md, docs/, .cortex/collate/
```

### 完整工作流
```
cortex -m        # 开始工作：加载项目上下文
cortex -c        # 完成阶段：保存上下文快照
cortex -c -d     # 改动文档：保存快照 + 同步文档
cortex -i        # 定期维护：审查并压缩快照
```

### 调试：手动启动/停止审查服务器
```bash
# 启动
cd .cortex/collate && python server.py .

# 优雅关闭
curl -s -X POST http://127.0.0.1:18888/shutdown

# 强制关闭（通过 PID 文件）
kill $(cat .cortex/collate/server.pid)
```

### 添加新技能
1. 创建新目录 `cortex-<name>/SKILL.md`
2. 按现有格式编写 SKILL.md（YAML 前端元数据 + Markdown 正文，所有路径引用使用兄弟目录约定）
3. 在 `cortex/SKILL.md` 的技能体系表格和参数映射中添加条目
