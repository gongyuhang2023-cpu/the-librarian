---
name: meeting
description: |
  会议录制与资料导入。当用户提到"录制会议"、"开始录制"、"组会"、"meeting"、
  "会议录制"、"导入会议"、"会议记录"时触发。
  录制 → 转录 → 解读 → 导入 NotebookLM。
---

# 会议录制与导入工作流

录制学术会议，生成逐页 PPT 解读和会议总结，并导入 NotebookLM 知识库。

会议原始数据（音频、截图、转录）保留在 `meetings/YYYY-MM-DD/`，只将生成的 `.md` 文件导入 NotebookLM。

---

## Phase 0: 首次使用检测

1. Read `~/.claude/skills/meeting_mind/config.yaml`
2. If `output.base_dir` is empty → **首次使用**:
   - Read `~/.claude/skills/meeting_mind/SETUP_GUIDE.md`
   - Follow the guide: check environment, troubleshoot if needed, ask ASR preference
   - Write choices back to config.yaml（`transcription.engine`）
   - `output.base_dir` 不需要设置 — 本项目固定使用 `meetings/` 目录
   - Then continue to Phase 1
3. If `output.base_dir` is set → **非首次**, skip directly to Phase 1

---

## Phase 1: 参数确认

读取 `~/.claude/skills/meeting_mind/config.yaml` 获取音频/转录默认设置。

Use **AskUserQuestion** with 3 questions:

Question 1 — Meeting software:
- header: "会议软件"
- Options: "Teams" (default), "Zoom", "腾讯会议"

Question 2 — Screenshot settings:
- header: "截图设置"
- Options:
  - "默认 (间隔5s, 阈值5%)" — recommended
  - "敏感 (间隔3s, 阈值3%)" — fast presentations
  - "宽松 (间隔10s, 阈值8%)" — slow discussions

Question 3 — Microphone recording:
- header: "麦克风"
- Options:
  - "仅系统声音" — recommended, only record what others say (loopback)
  - "系统 + 麦克风" — also record your voice, mixed into one file

---

## Phase 2: 启动录制

1. Output path: `meetings/YYYY-MM-DD/`（the-librarian 项目内，使用绝对路径）

2. Map settings to CLI args:
   - 默认 → `--interval 5 --threshold 5`
   - 敏感 → `--interval 3 --threshold 3`
   - 宽松 → `--interval 10 --threshold 8`
   - Teams → `--meeting teams`, Zoom → `--meeting zoom`, 腾讯会议 → `--meeting tencent`
   - 系统 + 麦克风 → `--mic`
   - config `audio.virtual_cable.enabled` is true → `--virtual-cable "<keyword>"` (keyword from config)

3. **Launch in background**:
   ```bash
   python ~/.claude/skills/meeting_mind/scripts/run.py session.py \
     --meeting <software> --interval <N> --threshold <N> \
     [--mic] \
     [--virtual-cable "<audio.virtual_cable.keyword>"] \
     --output "C:/Users/Yuhang/Library/the-librarian/meetings/YYYY-MM-DD"
   ```
   Use `run_in_background: true`.

4. Inform user: software, interval, threshold, virtual cable status, output path, task ID.

---

## Phase 3: 停止 + 后处理

When user says "结束了"、"会议结束"、"停止录制"、"stop":

### Step 1: 停止录制

1. **Graceful stop**: Create a STOP file in the output directory:
   ```bash
   touch "meetings/YYYY-MM-DD/STOP"
   ```
   Wait up to 10 seconds for the task to finish (TaskOutput block=true timeout=10000).
   If still running, **TaskStop** as fallback.
2. **Parse JSON** between `===JSON_OUTPUT===` and `===END_JSON===`

### Step 2: 转录

If config `transcription.engine` is not "skip":
```bash
python ~/.claude/skills/meeting_mind/scripts/run.py transcribe.py \
  --audio "<audio_path>" --output "meetings/YYYY-MM-DD/transcript" \
  --vocabulary "~/.claude/skills/meeting_mind/vocabulary.txt"
```
Use `run_in_background: true`, wait for completion.

### Step 3: 读取转录文本

Read `meetings/YYYY-MM-DD/transcript/transcript.md` into memory.

### Step 4: 分批读取截图 + 生成解读 (interpretation.md)

1. **Filter unique slides** from JSON: only entries where `"type"` is absent. Skip `"type": "revisit"`.

2. **Split into batches of 5 slides each**.

3. **Spawn sub-agents in parallel** (one Agent per batch). Each agent receives:
   - The 5 slide image paths
   - The full transcript.md text
   - The slide timestamps + revisit timestamps for this batch's time range
   - Instructions (same as global skill)

4. **Collect all agent results**, concatenate in slide order.

5. **Write `interpretation.md`** to `meetings/YYYY-MM-DD/`:

```markdown
# 组会解读 — YYYY-MM-DD

## 会议信息
- 日期: YYYY-MM-DD
- 时长: XX 分钟 (HH:MM ~ HH:MM)
- 独立幻灯片: N 张

## Slide 1 (HH:MM:SS)
**视觉内容**: [...]
**对应转录**: [...]
**内容解读**: [...]

...

## 关键术语
- Term: 定义
```

### Step 5: 生成总结 (summary.md)

Based on interpretation.md, write `summary.md` to `meetings/YYYY-MM-DD/`:

```markdown
# 组会总结 — YYYY-MM-DD

> 共 N 张独立幻灯片 | 录音时长 XX:XX | HH:MM ~ HH:MM

## 整体概要
[2-3 sentences]

## 关键要点
- ...

## 方法与结果
- ...

## 待跟进问题
- ...
```

---

## Phase 4: 导入 NotebookLM

会议处理完成后，将 `interpretation.md` 和 `summary.md` 作为资料导入知识库。

### Step 1: 生成文件画像

读取两个 .md 文件内容，生成一个统一的会议画像：

- **title**: `组会 — YYYY-MM-DD: [从内容提取的会议主题]`
- **summary**: 1-2 句中文摘要，描述会议讨论了什么
- **type**: `meeting`
- **keywords**: 3-5 个英文关键词，从 slide 内容提取

用 AskUserQuestion 向用户展示画像，允许修改后确认。

### Step 2: 分类（交互式）

1. 读 `~/.notebooklm/library_index.json` 获取所有 notebook
2. 基于会议内容的 keywords 和 summary 匹配合适的 notebooks
3. AskUserQuestion 让用户选择目标 notebooks（支持多选）
4. `interpretation.md` 和 `summary.md` 进入同一组 notebooks
5. 用户可选"创建新笔记本" → 委托 manage skill 流程 B

### Step 3: 容量检查

对每个目标 notebook：
1. 读 catalog 中的 `volumes` 数组，取最新 volume 的 `source_count`
2. 若 `source_count` 为 -1 → `notebooklm source list -n <UUID> --json` 获取实际数量
3. 若接近或达到 300 → 委托 manage skill 流程 D 创建分卷
4. 注意：每个会议占 2 个 source（interpretation + summary）

### Step 4: 上传

对每个目标 notebook：
```bash
notebooklm source add "meetings/YYYY-MM-DD/interpretation.md" -n <UUID> --json
notebooklm source add "meetings/YYYY-MM-DD/summary.md" -n <UUID> --json
```

解析返回 JSON 确认成功。

### Step 5: 归档与注册

**5a. 归档到 library/**

对每个目标 notebook，复制到 `library/<notebook-slug>/meeting-YYYY-MM-DD/`：
```
library/<notebook-slug>/meeting-YYYY-MM-DD/
├── interpretation.md
└── summary.md
```
多 notebook 时复制到每个对应目录。

**5b. 更新 files.json**

向 `registry/files.json` 追加条目（一个会议一条记录）：
```json
{
  "hash": "meeting:YYYY-MM-DD",
  "filename": "meeting-YYYY-MM-DD",
  "title": "组会 — YYYY-MM-DD: [主题]",
  "summary": "[中文摘要]",
  "type": "meeting",
  "keywords": ["kw1", "kw2"],
  "notebooks": ["uuid1", "uuid2"],
  "local_paths": ["library/slug1/meeting-YYYY-MM-DD/", "library/slug2/meeting-YYYY-MM-DD/"],
  "source_files": ["interpretation.md", "summary.md"],
  "processed": true,
  "added": "YYYY-MM-DD"
}
```

**5c. 更新 library_index.json**

对每个受影响的 notebook：
- `source_count` += 2（两个文件）
- `updated` 更新为今天

**5d. 会议原始数据保留在 `meetings/YYYY-MM-DD/`，不删除不移动。**

### Step 6: 报告

```
会议处理完成：
- 日期: YYYY-MM-DD
- 时长: XX 分钟
- 幻灯片: N 张
- 已上传: interpretation.md + summary.md → K 本 notebook
- 会议数据: meetings/YYYY-MM-DD/
- 归档位置: library/<slugs>/meeting-YYYY-MM-DD/
```

---

## 附：导入已有会议记录

如果用户已有会议的 `interpretation.md` 和 `summary.md`（例如之前在其他项目录制的），可直接进入 Phase 4：

1. 将文件放入 `meetings/YYYY-MM-DD/`（手动创建日期文件夹）
2. 告知 Claude："导入 meetings/YYYY-MM-DD 的会议记录"
3. 直接执行 Phase 4 的 Step 1-6

---

## 最终目录结构

```
meetings/YYYY-MM-DD/
├── interpretation.md    ← 导入 NotebookLM
├── summary.md           ← 导入 NotebookLM
├── audio/
│   └── recording.wav
├── slides/
│   ├── slide_001.png
│   └── ...
├── transcript/
│   └── transcript.md
└── metadata.json
```
