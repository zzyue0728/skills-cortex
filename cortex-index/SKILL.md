---
name: cortex-index
description: 读取 .cortex/ 下所有 active 快照，按 5 维度交叉对比去重后生成审查页面，用户确认后压缩快照，原快照标记为 compressed
---

# cortex-index — 压缩整理

读取 `.cortex/` 下所有 status=active 的快照内容，按 5 维度交叉对比去重，生成审查 HTML 页面供用户逐条确认（删除/全局），确认后生成压缩快照并更新索引。

## 触发条件

- 用户直接输入 `cortex-index`
- 主技能 `cortex -i` 分发调用

## 执行流程

### 第一步：读取所有 active 快照

读取 `.cortex/_index.md`，获取所有 status=active 的条目。

如果 _index.md 不存在或无 active 条目，输出：
```
❌ 未找到 active 的快照
请先使用 cortex -c 保存快照。
```
并结束流程。

如果 active 条目 ≤ 1，输出：
```
ℹ️ active 快照只有 X 条，无需压缩
```
并结束流程。

### 第二步：交叉对比去重

读取每条 active 快照的完整内容，按 5 维度分别处理：

**设计意图 / 已否决方案 / 方向约束**：
- 去重合并（语义相同保留最详细版本），新建条目赋予唯一 id

**已知坑位**：
- 去重合并，检查后续快照中是否已修复 → 初步排除已修复的坑位

**当前断点**：
- 只取最新快照的内容

### 第三步：生成审查数据

1. 将对比结果按以下结构写入 `.cortex/collate/review_data.json`：
```json
{
  "source_files": ["<来源快照1>", "<来源快照2>"],
  "dimensions": {
    "设计意图": [{"id": 1, "text": "完整文本", "deleted": false, "global": false}],
    "已否决方案": [...],
    "已知坑位": [...],
    "当前断点": [...],
    "方向约束": [...]
  }
}
```
每条记录的默认状态均为 `deleted: false, global: false`。

2. 读取当前 SKILL.md 同级目录下的 `scripts/review.html`（即 `./scripts/review.html`，相对于本技能文件所在目录），将 `__REVIEW_DATA__` 替换为 review_data.json 的完整 JSON 字符串，生成 `.cortex/collate/review.html`。

### 第四步：启动审查

所有命令使用 bash 语法，兼容 Windows Git Bash / Linux / macOS。

1. 在 `.cortex/collate/` 目录后台启动 server.py：
```bash
cd .cortex/collate && python server.py . &
```
服务器默认监听 `127.0.0.1:18888`，端口被占用时自动递增，实际 URL 输出到终端。

2. 稍等 1 秒后，打开浏览器：
```bash
start http://127.0.0.1:18888
```
> Windows：`start` 在 Git Bash 中可用。Linux：替换为 `xdg-open`，macOS：替换为 `open`。

3. 提示用户：
```
📋 审查页面已在浏览器中打开

在页面中逐条操作：
  [删除/恢复] 切换 → 从快照中移除或保留
  [全局/局部] 切换 → 全局则移入 CORTEX.md，局部则保留在快照
完成后点击 [确认保存]，回到这里告诉我"好了"。
```

### 第五步：等待用户确认

等待用户操作完成后告知"好了"或"继续"。

- 用户点击 [确认保存]：server.py 自动停止（保存后 2 秒关闭），无需手动干预
- 用户点击 [取消]：server.py 仍在运行，执行以下命令优雅关闭：
  ```bash
  curl -s -X POST http://127.0.0.1:18888/shutdown
  ```
  如果 curl 不可用，通过 PID 文件结束：
  ```bash
  kill $(cat .cortex/collate/server.pid) 2>/dev/null
  ```

### 第六步：处理审查结果

1. 读取 `.cortex/collate/save_result.json`
2. 按每条记录的标记处理：

| 标记 | 操作 |
|------|------|
| `deleted: true` | 从压缩快照中移除 |
| `deleted: false, global: false` | 保留在压缩快照中 |
| `deleted: false, global: true` | 写入 CORTEX.md 对应区块，快照中移除 |
| `deleted: true, global: any` | 直接移除（删除优先） |

**全局条目 → CORTEX.md 映射：**

| 维度 | CORTEX.md 区块 |
|------|---------------|
| 设计意图 | `## 设计意图`（不存在则创建） |
| 已否决方案 | `## 已否决方案`（不存在则创建） |
| 已知坑位 | `## 已知坑位`（不存在则创建） |
| 当前断点 | 不适用（该维度无全局选项） |
| 方向约束 | `## 方向约束`（不存在则创建） |

写入 CORTEX.md 时做语义去重，避免重复。

### 第七步：写入压缩快照与更新索引

1. 检查保留在快照中的条目数：如果全部条目均被删除或移入 CORTEX.md（保留条目为 0），跳过写入新快照文件，仅更新索引（将原 active 条目改为 compressed，不追加新条目）。
2. 如果有保留条目，按 5 维度格式写入新快照文件 `.cortex/YYYY-MM-DD_HH-MM.md`
3. 更新 `.cortex/_index.md`：
   - 如写入了新快照，追加新条目：`<文件名> | <取来源中最宽泛的层级> | 压缩 | 压缩合并 X 条快照 | active`
   - 将原 active 条目的 status 改为 `compressed`

### 第八步：清理

1. 停止 server.py 进程（如果仍在运行，比如用户点击了取消但未手动停止）：
   ```bash
   curl -s -X POST http://127.0.0.1:18888/shutdown 2>/dev/null || \
     kill $(cat .cortex/collate/server.pid) 2>/dev/null || true
   ```
2. 删除 `.cortex/collate/` 下的临时文件，仅保留 `server.py`：
   - 删除 `review.html`
   - 删除 `review_data.json`
   - 删除 `save_result.json`（如果存在）
   - 删除 `server.pid`（如果存在）
   - 删除 `server.port`（如果存在）

### 第九步：输出摘要

```
✅ 压缩整理完成

新快照：.cortex/YYYY-MM-DD_HH-MM.md（压缩合并 X 条快照，保留 Y 条条目）
已移入 CORTEX.md：Z 条全局条目
旧快照状态：compressed（X 条）
```
