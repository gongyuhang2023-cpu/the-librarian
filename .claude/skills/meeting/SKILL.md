---
name: meeting
description: |
  会议录制与资料导入。当用户提到"录制会议"、"开始录制"、"组会"、"meeting"、
  "会议录制"、"导入会议"、"会议记录"时触发。
  录制 → 转录 → 解读 → 导入 NotebookLM。
---

# 会议录制与导入

录制 → 转录 → 逐页解读 → 总结 → 导入 NotebookLM → 归档到 Wiki raw

---

## Phase 0: 首次使用

1. 读 `~/.claude/skills/meeting_mind/config.yaml`
2. `output.base_dir` 为空 → 读 `SETUP_GUIDE.md`，完成环境检查和 ASR 选择
3. `output.base_dir` 不需要设置（本项目固定用 `meetings/`）
4. 已设置 → 跳到 Phase 1

## Phase 1: 参数确认

先直接询问用户（自由文本）：**会议主题** 和 **报告人**。

然后 AskUserQuestion（3 题）：

1. **会议软件**：Teams / Zoom / 腾讯会议
2. **截图设置**：默认(5s/5%) / 敏感(3s/3%) / 宽松(10s/8%)
3. **麦克风**：仅系统声音 / 系统+麦克风

## Phase 2: 启动录制

设置映射：
- 默认 → `--interval 5 --threshold 5`，敏感 → `--interval 3 --threshold 3`，宽松 → `--interval 10 --threshold 8`
- Teams → `--meeting teams`，Zoom → `--meeting zoom`，腾讯会议 → `--meeting tencent`
- 系统+麦克风 → `--mic`
- config `audio.virtual_cable.enabled` is true → `--virtual-cable "<keyword>"`

```bash
python ~/.claude/skills/meeting_mind/scripts/run.py session.py \
  --meeting <software> --interval <N> --threshold <N> \
  [--mic] [--virtual-cable "<keyword>"] \
  --output "C:/Users/Yuhang/Library/the-librarian/meetings/YYYY-MM-DD"
```

`run_in_background: true`。告知用户参数和 task ID。

## Phase 3: 停止 + 后处理

触发词："结束了"、"会议结束"、"停止录制"、"stop"

### Step 1: 停止录制

```bash
touch "meetings/YYYY-MM-DD/STOP"
```
等 10 秒（TaskOutput block=true timeout=10000），未停则 TaskStop。解析 `===JSON_OUTPUT===` 到 `===END_JSON===` 之间的 JSON。

### Step 2: 转录

config `transcription.engine` 非 "skip" 时：

```bash
python ~/.claude/skills/meeting_mind/scripts/run.py transcribe.py \
  --audio "<audio_path>" --output "meetings/YYYY-MM-DD/transcript" \
  --vocabulary "~/.claude/skills/meeting_mind/vocabulary.txt"
```

`run_in_background: true`，等待完成。

### Step 3: 读取转录

读 `meetings/YYYY-MM-DD/transcript/transcript.md`。

### Step 4: 生成解读 (interpretation.md)

1. 从 JSON 过滤独立幻灯片（跳过 `"type": "revisit"`）
2. 每 5 张一批，**并行 spawn sub-agent**，每个 agent 接收：截图路径 + 完整 transcript + 时间戳
3. Agent 任务：读截图 → 定位对应转录 → 生成视觉内容/对应转录/内容解读
4. 合并结果，写 `meetings/YYYY-MM-DD/interpretation.md`：

```markdown
# 组会解读 — YYYY-MM-DD

## 会议信息
- 主题: <主题>
- 报告人: <报告人>
- 日期/时长/幻灯片数

## Slide 1 (HH:MM:SS)
**视觉内容**: ...
**对应转录**: ...
**内容解读**: ...

## 关键术语
- Term: 定义
```

### Step 5: 生成总结 (summary.md)

基于 interpretation.md 生成 `meetings/YYYY-MM-DD/summary.md`：

```markdown
# 组会总结 — YYYY-MM-DD
- 主题: <主题>
- 报告人: <报告人>
> N 张幻灯片 | XX:XX | HH:MM ~ HH:MM

## 整体概要 / 关键要点 / 方法与结果 / 待跟进问题
```

## Phase 4: 导入 NotebookLM

### Step 1: 画像

从两个 md 生成画像：title（`组会 — YYYY-MM-DD: [主题]`）、summary、type=meeting、keywords。AskUserQuestion 确认。

### Step 2: 分类

读 `~/.notebooklm/library_index.json` → 匹配 notebooks → AskUserQuestion 多选。两个 md 进同一组 notebooks。

### Step 3: 容量检查

`source_count` 接近 300 → 委托 manage skill 流程 D。每个会议占 2 个 source。

### Step 4: 上传

```bash
notebooklm source add "meetings/YYYY-MM-DD/interpretation.md" -n <UUID> --json
notebooklm source add "meetings/YYYY-MM-DD/summary.md" -n <UUID> --json
```

### Step 5: 归档与注册

> 归档前读 `paths.yaml` 获取 `sources_dir` 和 `backup_dir`。

**归档（双输出）**：

- **sources 层**：复制 `interpretation.md` → `sources_dir/<nb>/meeting-YYYY-MM-DD-interpretation.md`，复制 `summary.md` → `sources_dir/<nb>/meeting-YYYY-MM-DD-summary.md`。扁平放置，文件名加日期前缀。多 notebook 复制到每个。
- **backup 层**：复制整个 `meetings/YYYY-MM-DD/` 目录到 `backup_dir/<nb>/meeting-YYYY-MM-DD/`（含截图、录音、转录、md 完整数据）。多 notebook 复制到每个。

**注册**：向 `registry/files.json` 追加：
```json
{
  "hash": "meeting:YYYY-MM-DD", "filename": "meeting-YYYY-MM-DD",
  "title": "组会 — YYYY-MM-DD: [主题]", "summary": "...",
  "type": "meeting", "keywords": [...],
  "notebooks": ["uuid1"],
  "source_paths": ["raw/sources/<nb>/meeting-YYYY-MM-DD-interpretation.md", "raw/sources/<nb>/meeting-YYYY-MM-DD-summary.md"],
  "backup_path": "00-raw/<nb>/meeting-YYYY-MM-DD/",
  "processed": true, "added": "YYYY-MM-DD"
}
```

**更新 catalog**：每个 notebook `source_count` += 2，`updated` = 今天。

**会议原始数据保留在 `meetings/YYYY-MM-DD/`，不删除。**

### Step 6: 报告

```
会议处理完成：YYYY-MM-DD / XX分钟 / N张幻灯片 / → K本notebook
```
