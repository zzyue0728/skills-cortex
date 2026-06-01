# cortex — 让 AI 编程终端记住你的项目

项目上下文管理技能体系。解决跨会话的上下文丢失问题。

## 痛点

- 在 AI 编程终端开发项目，每次开新会话，AI 都不记得上次的决策、踩过的坑、当前进度
- `docs/` 写满了"项目长什么样"，但 AI 看不到"为什么这么写""放弃了什么方案""上次停在哪"
- 每次都得重新解释背景，效率极低

## 它是什么

cortex 从对话中提取 5 维度结构化上下文（设计意图、已否决方案、已知坑位、当前断点、方向约束），保存为快照文件，并支持跨会话加载、压缩整理和文档同步。

由 5 个技能组成，通过 `cortex` 主调度器统一入口。**五个技能目录必须互为兄弟目录**，拷贝到 AI 编程终端的 skills 目录下即可使用。

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

## 安装

### 支持的 AI 编程终端

| 工具 | 拷贝目标目录 | 说明 |
|------|--------------|------|
| Claude Code | `~/.claude/skills/` | 官方支持 SKILL.md 格式 |
| OpenCode | `~/.config/opencode/skills/` | 官方支持 SKILL.md 格式 |
| Codex CLI | `~/.codex/skills/` | 官方支持 SKILL.md 格式 |

> Cursor、Aider、Continue 等工具使用不同的扩展机制（RULES、CONVENTIONS、config），不直接兼容 SKILL.md 格式。
>
> Cline 通过 `.clinerules/` 适配，需自行调整 SKILL.md 格式。

### 步骤

1. 克隆本仓库到本地任意位置：
   ```bash
   git clone https://github.com/zzyue0728/skills-cortex.git
   ```
2. 将仓库内的五个目录（`cortex/`、`cortex-context/`、`cortex-docsync/`、`cortex-index/`、`cortex-memory/`）拷贝到目标 skills 目录下，**保持兄弟目录结构**。

   以 OpenCode 为例（Windows Git Bash / Linux / macOS）：
   ```bash
   cp -r skills-cortex/cortex skills-cortex/cortex-context \
         skills-cortex/cortex-docsync skills-cortex/cortex-index \
         skills-cortex/cortex-memory ~/.config/opencode/skills/
   ```

   Windows PowerShell：
   ```powershell
   Copy-Item -Recurse skills-cortex\cortex, skills-cortex\cortex-context, `
             skills-cortex\cortex-docsync, skills-cortex\cortex-index, `
             skills-cortex\cortex-memory ~/.config/opencode/skills/
   ```

3. 重启 AI 编程终端，技能即可加载。

## 快速开始

在你的项目根目录执行：

```bash
# 首次使用：初始化 .cortex/ 目录 + 输出教程
cortex

# 开始工作：加载项目上下文
cortex -m

# 完成一个阶段：保存上下文快照
cortex -c

# 改动文档后：保存快照 + 同步 docs
cortex -c -d

# 定期维护：审查并压缩快照（自动打开浏览器）
cortex -i
```

## 用法

| 命令 | 功能 |
|------|------|
| `cortex` | 初始化目录 + 输出教程 |
| `cortex -c` | 保存上下文快照 |
| `cortex -d` | 同步 docs 文档 |
| `cortex -i` | 审查并压缩快照 |
| `cortex -m` | 加载项目上下文 |

支持组合：`cortex -c -d -i -m`，按固定顺序执行（`c → d → i → m`）。

## 兼容性

- **Python**：3.7+（`server.py` 仅依赖 `http.server` + `json`）
- **操作系统**：Windows / Linux / macOS
- **Shell**：Git Bash / bash（命令使用 bash 语法，兼容 Windows Git Bash / Linux / macOS）

## 开发与测试

```bash
python -m unittest discover -s tests
```

测试覆盖 `cortex-index/scripts/server.py` 的核心路径：启动、HTML 渲染、`__REVIEW_DATA__` 占位符注入、`/save` 端点、`/shutdown` 端点、临时文件清理。零外部依赖，仅使用标准库。

## 许可证

本项目仅供个人学习与使用，**禁止任何形式的商业用途**。详见 [LICENSE](LICENSE)。
