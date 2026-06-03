---
name: memo-review
description: 读取 active 快照交叉对比去重，结合项目状态分析建议，生成审查页面供用户确认后执行修改
---

# memo-review — 审查与压缩

读取所有 active 快照，交叉对比去重，结合项目状态（docs/ + MEMO.md）逐条给出 AI 建议，生成审查页面供用户确认删除/保留/提全局，最终写入新快照。

## 触发条件

- 用户直接输入 `memo-review`
- 主技能 `memo -r` 分发调用

## 执行流程

### 第一步：读取所有 active 快照

读取 `.memo/_index.md`，获取所有 status=active 的条目。

如果 _index.md 不存在或无 active 条目，输出：
```
❌ 未找到 active 的快照
请先使用 memo -c 保存快照。
```
并结束流程。

### 第二步：交叉对比去重

读取每条 active 快照的完整内容，按 5 维度分别处理：

**设计意图 / 已否决方案 / 方向约束**：
- 去重合并（语义相同保留最详细版本），新建条目赋予唯一 id

**已知坑位**：
- 去重合并（语义相同保留最详细版本），新建条目赋予唯一 id
- 标记"已修复"：对每条坑位，按顺序检查以下条件，符合任一即视为已修复：
  1. 后续快照的"已知坑位"中出现该坑位 + "已解决/已修复/已绕过"等明确标记
  2. 后续快照的"设计意图"中提到"改用 X 替代"或"采用新方案"，且 X 与该坑位的解法语义匹配
  3. 后续快照的"当前断点"中提到"修复了 X"或"解决了 X"，且 X 包含该坑位
- 已修复的坑位不进入压缩快照（保留在原快照文件中，不物理删除）
- 未命中任何条件的坑位进入压缩快照

**当前断点**：
- 只取最新快照的内容

### 第三步：加载项目状态

自动加载以下两个参考源（无需用户选择）：
1. 扫描 `docs/` 目录，读取所有 `.md` 文件完整内容
2. 读取 `MEMO.md` 全部内容（用户规则、设计意图、已否决方案、已知坑位、方向约束、文档索引表）

### 第四步：读取 MEMO.md 全局条目

解析 `MEMO.md` 中的 5 维度区块（`## 设计意图`、`## 已否决方案`、`## 已知坑位`、`## 方向约束`），提取所有条目。

每条标注 `source: "memo"`，与快照来源的 `source: "snapshot"` 区分。

### 第五步：逐条分析，生成 AI 建议

将**快照去重后的条目**和 **MEMO.md 全局条目**分别结合项目状态分析。

**快照条目建议逻辑**：

| 建议 | 判定条件 |
|------|----------|
| **保留** | 该条目与当前项目状态一致，仍有效 |
| **删除** | 已过时、已被后续内容覆盖、与实际项目不符 |
| **提全局** | 属于长期有效的架构/设计决策，适合沉淀到 MEMO.md |
| **待核实** | 信息不足以判断，需用户人工确认 |

**MEMO.md 条目建议逻辑**：

| 建议 | 判定条件 |
|------|----------|
| **保留** | 条目与当前项目状态一致，仍有效 |
| **删除** | 已过时、已被项目实际走向推翻、与当前代码/文档不符 |
| **待核实** | 信息不足以判断，需用户人工确认 |

注意：MEMO.md 条目已经是全局的，"提全局"选项无意义，不出现。

### 第六步：生成审查数据

1. 将对比结果按以下结构写入 `.memo/collate/review_data.json`：
```json
{
  "source_files": ["<来源快照1>", "<来源快照2>"],
  "dimensions": {
    "设计意图": [
      {
        "id": 1,
        "text": "完整文本",
        "deleted": false,
        "global": false,
        "source": "snapshot",
        "suggestion": "保留",
        "reason": "参考源显示项目当前仍使用此方案"
      }
    ],
    "已否决方案": [...],
    "已知坑位": [...],
    "当前断点": [...],
    "方向约束": [...]
  }
}
```
字段说明：
- `source: "snapshot"` → 来自快照去重
- `source: "memo"` → 来自 MEMO.md 全局条目
- `suggestion`：AI 建议（保留/删除/提全局/待核实）
- `reason`：建议理由

2. 拷贝模板文件到输出目录：
   ```bash
   cp ../memo-review/scripts/review.html .memo/collate/review.html
   ```
   `server.py` 的 `do_GET` 会在 serve 时从 `review_data.json` 读取数据，动态注入到占位符位置（Python 端读写 UTF-8 编码正确，无乱码问题）。

### 第七步：启动审查

所有命令使用 bash 语法，兼容 Windows Git Bash / Linux / macOS。

0. 确保 `.memo/collate/server.py` 已就位。初始化阶段（`memo` 无参数）已自动拷贝，但若跳过初始化直接跑 `memo -r`，需手动补上：
   ```bash
   test -f .memo/collate/server.py || cp ../memo-review/scripts/server.py .memo/collate/server.py
   ```
   > 路径使用兄弟目录约定（`../memo-review/scripts/`），假设当前在项目根目录。

1. 在 `.memo/collate/` 目录后台启动 server.py：
   ```bash
   cd .memo/collate && python server.py . &
   ```
   服务器默认监听 `127.0.0.1:18888`，端口被占用时自动递增（最多尝试 100 个），实际 URL 输出到终端。

2. 稍等 1 秒后，打开浏览器：
   ```bash
   start http://127.0.0.1:18888
   ```
   > Windows：`start` 在 Git Bash 中可用。Linux：替换为 `xdg-open`，macOS：替换为 `open`。

3. 提示用户：
   ```
   📋 审查页面已在浏览器中打开

   在页面中逐条操作：
     [删除/恢复] 切换 → 从快照或 MEMO.md 中移除或保留
     [全局/局部] 切换 → 全局则移入 MEMO.md，局部则保留在快照（仅快照来源条目）
     [MEMO.md 条目] → 只能删除或保留，无全局切换
   完成后点击 [确认保存]，回到这里告诉我"好了"。
   ```

### 第八步：等待用户确认

等待用户操作完成后告知"好了"或"继续"。

- 用户点击 [确认保存]：server.py 自动停止（保存后 2 秒关闭），无需手动干预
- 用户点击 [取消]：server.py 仍在运行，执行以下命令优雅关闭：
  ```bash
  curl -s -X POST http://127.0.0.1:18888/shutdown
  ```
  如果 curl 不可用，通过 PID 文件结束：
  ```bash
  kill $(cat .memo/collate/server.pid) 2>/dev/null
  ```

### 第九步：处理审查结果

1. 读取 `.memo/collate/save_result.json`
2. 按每条记录的标记处理：

| source | 标记 | 操作 |
|--------|------|------|
| snapshot | `deleted: true` | 从压缩快照中移除 |
| snapshot | `deleted: false, global: false` | 保留在压缩快照中 |
| snapshot | `deleted: false, global: true` | 写入 MEMO.md 对应区块，快照中移除 |
| memo | `deleted: true` | 从 MEMO.md 对应区块中移除该条目 |
| memo | `deleted: false` | 保留在 MEMO.md 中（不做修改） |

**全局条目 → MEMO.md 映射：**

| 维度 | MEMO.md 区块 |
|------|---------------|
| 设计意图 | `## 设计意图`（不存在则创建） |
| 已否决方案 | `## 已否决方案`（不存在则创建） |
| 已知坑位 | `## 已知坑位`（不存在则创建） |
| 当前断点 | 不适用（该维度无全局选项） |
| 方向约束 | `## 方向约束`（不存在则创建） |

写入/删除 MEMO.md 时做语义去重，避免重复或误删。

### 第十步：写入新快照与更新索引

1. 检查保留在快照中的条目数（source=snapshot 且 deleted=false 的条目）：
   - 如果全部删除或提全局（保留条目为 0），跳过写入新快照文件，仅更新索引（将原 active 条目改为 compressed，不追加新条目）
   - 如果有保留条目，按 5 维度格式写入新快照文件 `.memo/YYYY-MM-DD_HH-MM.md`

2. 更新 `.memo/_index.md`：
   - 如写入了新快照，追加新条目：`<文件名> | <取来源中最宽泛的层级> | 压缩 | 压缩合并 X 条快照 | active`
   - 将原 active 条目的 status 改为 `compressed`

### 第十一步：更新 MEMO.md

根据第九步的处理结果：
- 新增的全局条目（snapshot 来源，global=true）→ 追加到 MEMO.md 对应维度区块
- 删除的 MEMO.md 条目（memo 来源，deleted=true）→ 从 MEMO.md 对应维度区块移除
- 语义去重：写入前检查 MEMO.md 中是否已有相同语义的条目

### 第十二步：清理

1. 停止 server.py 进程（如果仍在运行，比如用户点击了取消但未手动停止）：
   ```bash
   curl -s -X POST http://127.0.0.1:18888/shutdown 2>/dev/null || \
     kill $(cat .memo/collate/server.pid) 2>/dev/null || true
   ```
2. 删除 `.memo/collate/` 下的临时文件，仅保留 `server.py`：
   - 删除 `review.html`
   - 删除 `review_data.json`
   - 删除 `save_result.json`（如果存在）
   - 删除 `server.pid`（如果存在）
   - 删除 `server.port`（如果存在）

### 第十三步：输出摘要

```
✅ 审查完成

新快照：.memo/YYYY-MM-DD_HH-MM.md（压缩合并 X 条快照，保留 Y 条条目）
已移入 MEMO.md：Z 条全局条目
已从 MEMO.md 删除：W 条过时条目
旧快照状态：compressed（X 条）
```

## 注意事项

- 所有路径引用基于"五个技能目录互为兄弟目录"约定
- `review.html` 和 `server.py` 位于 `memo-review/scripts/`
- 中文编码：HTML `<meta charset="UTF-8">` + server.py 的 `Content-Type: text/html; charset=utf-8`
