# cortex — 项目上下文管理技能体系

面向 AI 编程终端的项目上下文管理技能，解决跨会话的上下文丢失问题。

## 概述

cortex 从对话中提取结构化上下文信息（设计意图、已否决方案、已知坑位、当前断点、方向约束），保存为快照文件，并支持跨会话加载、压缩整理和文档同步。

由 5 个技能组成，通过 `cortex` 主调度器统一入口。五个技能目录互为兄弟目录，拷贝到任意 AI 编程终端的 skills 目录下即可使用。

## 技能架构

```
skills/
├── cortex/SKILL.md              主调度器，解析 -c -d -i -m 参数并分发
├── cortex-context/SKILL.md      从对话提取 5 维度信息，保存快照到 .cortex/
├── cortex-docsync/SKILL.md      同步 docs/ 文档与 CORTEX.md 索引
├── cortex-index/SKILL.md        审查并压缩快照，全局条目写入 CORTEX.md
│   └── scripts/
│       ├── server.py            HTTP 服务器（提供审查页面 + 接收结果）
│       └── review.html          审查页面（纯前端，逐条标记删除/全局）
└── cortex-memory/SKILL.md       加载 .cortex/ 快照 + CORTEX.md 到上下文
```

## 5 维度上下文模型

| 维度 | 用途 | 防什么 |
|------|------|--------|
| 设计意图 | 记录方案选择背后的原因 | 防止 AI 重构看似"奇怪"的代码 |
| 已否决方案 | 记录明确拒绝过的方案 | 防止 AI 重复提议已否决的方向 |
| 已知坑位 | 记录踩过的坑和解决方案 | 防止 AI 用同样方式再踩一次 |
| 当前断点 | 记录做到哪了、停在哪了 | 防止 AI 不清楚从哪接手 |
| 方向约束 | 记录未成文的边界约定 | 防止 AI 提议违背既定方向 |

## 数据流

```
对话 → cortex-context → .cortex/YYYY-MM-DD_HH-MM.md（快照文件）
                          └── .cortex/_index.md（索引表）
                          └── CORTEX.md（全局条目 + 文档索引）

.cortex/ 快照 → cortex-index → 审查页面（浏览器）→ 压缩快照 + 全局条目写入 CORTEX.md

.cortex/ 快照 + CORTEX.md → cortex-memory → 注入 AI 上下文
```

## 用法

| 命令 | 功能 |
|------|------|
| `cortex` | 初始化目录 + 输出教程 |
| `cortex -c` | 保存上下文快照 |
| `cortex -d` | 同步 docs 文档 |
| `cortex -i` | 审查并压缩快照 |
| `cortex -m` | 加载项目上下文 |

支持组合：`cortex -c -d -i -m`

## 推荐工作流

```
开始工作 → cortex -m（加载项目上下文）
完成阶段 → cortex -c（保存上下文快照）
改动文档 → cortex -c -d（保存快照 + 同步文档）
定期维护 → cortex -i（审查并压缩快照）
首次使用 → cortex（初始化目录结构）
```

## 特性

- **零构建依赖**：无 `package.json`、`requirements.txt` 或任何构建工具
- **纯 Python 标准库**：`server.py` 仅依赖 `http.server` + `json`，无需外部依赖
- **纯前端审查页面**：`review.html` 无框架依赖，通过 `__REVIEW_DATA__` 占位符注入 JSON 数据
- **跨平台兼容**：Shell 命令兼容 Windows Git Bash / Linux / macOS
- **路径自发现**：技能间引用通过兄弟目录相对路径约定完成，不硬编码绝对路径

## 安装

将五个目录（`cortex/`、`cortex-context/`、`cortex-docsync/`、`cortex-index/`、`cortex-memory/`）拷贝到你的 AI 编程终端的 skills 目录下即可。

## 许可证

本项目仅供个人学习与使用，**禁止任何形式的商业用途**。详见 [LICENSE](LICENSE)。

