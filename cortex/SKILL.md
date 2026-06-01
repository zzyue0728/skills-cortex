---
name: cortex
description: cortex 技能体系主调度器。接收 -c -d -i -m 参数并分发到对应的子技能执行。无参数时初始化目录结构并输出技能教程
---

# cortex — 主调度器

cortex 是项目上下文管理技能体系的统一入口。通过参数分发到对应的子技能。

## 技能体系

五个技能为同级目录，拷贝到任意 AI 编程终端的 skills 目录下即可使用。

| 技能 | 目录 | 职责 |
|------|------|------|
| **cortex-context** | `cortex-context/` | 保存快照到 .cortex/ |
| **cortex-docsync** | `cortex-docsync/` | 同步 docs 文档和 CORTEX.md 索引 |
| **cortex-index** | `cortex-index/` | 审查并压缩快照 |
| **cortex-memory** | `cortex-memory/` | 加载快照和 CORTEX.md 到上下文 |

> 所有路径引用均基于"五个技能目录互为兄弟目录"的约定。当前技能文件所在目录为 `cortex/`，兄弟目录通过 `../<skill-name>/` 访问。

## 触发条件

用户输入 `cortex` 或 `cortex -[参数]` 时执行。

## 参数映射

| 参数 | 映射技能 | 行为 |
|------|----------|------|
| `-c` | cortex-context | 保存上下文快照 |
| `-d` | cortex-docsync | 同步 docs 文档 |
| `-i` | cortex-index | 审查并压缩快照 |
| `-m` | cortex-memory | 加载上下文 |

支持空格分隔组合，如 `cortex -c -d`。

## 执行规则

**当用户输入了参数时：**

1. 收集所有参数中的标志（如 `-c`、`-d`、`-i`、`-m`）
2. 去重：重复参数只执行一次
3. 按固定顺序排列：`c → d → i → m`（无论用户输入顺序如何）
4. 忽略非法参数并输出警告：
   ```
   ⚠️ 未知参数：-x，已忽略
   只支持 -c、-d、-i、-m
   ```
5. 按排列后的顺序依次加载对应的子技能

**执行顺序约定：** `-c → -d → -i → -m`

示例：
- `cortex -c` → 加载 cortex-context 技能
- `cortex -d` → 加载 cortex-docsync 技能
- `cortex -c -d` → 先加载 cortex-context，完成后加载 cortex-docsync
- `cortex -d -c` → 同样先 c 后 d（按固定顺序，不按输入顺序）
- `cortex -c -d -i -m` → 顺序执行全部四个技能

## 无参数时

当用户只输入 `cortex` 不带任何参数时，先初始化目录结构，再输出教程。

### 第一步：初始化

检查以下路径，缺失则创建：

- `.cortex/` 目录 → 创建（如果不存在）
- `.cortex/_index.md` → 创建基础索引模板（如果不存在）：
  ```markdown
  # 时间戳索引

  | 文件名 | 项目层级 | 类别 | 描述 | 状态 |
  |--------|----------|------|------|------|
  ```
- `CORTEX.md` → 创建基础模板（如果不存在）：
  ```markdown
  # CORTEX

  ## 用户规则

  <!-- 用户可在此区域写入自定义规则、偏好 -->

  ---

  ## 文档索引表

  | 编号 | 文件名 | 相对路径 | 简介 | 状态 | 最后同步 |
  |------|--------|----------|------|------|----------|
  ```
- `docs/` 目录 → 创建（如果不存在）
- `.cortex/collate/` 目录 → 创建（如果不存在），从兄弟目录 `cortex-index/scripts/` 下找到 `server.py`，拷贝到 `.cortex/collate/server.py`（源文件路径：当前 SKILL.md 所在目录的 `../cortex-index/scripts/server.py`）

检查 `.gitignore`，如果未包含 `.cortex/` 则追加一行。追加前确保文件末尾有换行符（如末尾无换行则先补换行再追加）。

### 第二步：输出教程

```
📋 cortex — 项目上下文管理技能体系

▸ 用法
  cortex             初始化目录 + 输出教程
  cortex -c          保存上下文快照
  cortex -d          同步 docs 文档
  cortex -i          审查并压缩快照
  cortex -m          加载上下文
  支持组合：cortex -c -d -i（顺序固定 c→d→i→m）

▸ 技能说明

  1. cortex-context（cortex -c）
     从对话提取 5 维度信息，保存为 .cortex/ 目录下的时间戳快照文件，并追加索引。
     保存时机：完成一个功能、做出重要决策、发现坑位、准备结束对话。

  2. cortex-docsync（cortex -d）
     分析当前对话中的文档变更，推荐需要同步的 docs 文档，
     经用户确认后更新 docs 文件及 CORTEX.md 中的文档索引表。
     只同步已确认的事实，不将讨论中的假设写入文档。

  3. cortex-index（cortex -i）
     读取 active 快照，交叉对比去重后打开审查页面，逐条勾选删除/全局后
     生成压缩快照，可选的全局条目写入 CORTEX.md。

  4. cortex-memory（cortex -m）
     加载 .cortex/ 下所有 active 快照和 CORTEX.md 到当前上下文，
     让 AI 了解项目设计意图、历史决策、已知坑位和当前状态。
     在开始新会话或接手项目时使用。

▸ 推荐工作流
  开始工作 → cortex -m（加载项目上下文）
  完成阶段 → cortex -c（保存上下文快照）
  改动文档 → cortex -c -d（保存快照 + 同步文档）
  定期维护 → cortex -i（审查并压缩快照）
  首次使用 → cortex（初始化目录结构）
```