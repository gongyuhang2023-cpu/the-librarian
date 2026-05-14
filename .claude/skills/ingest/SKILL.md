---
name: ingest
description: |
  文件摄入工作流。当用户提到"处理新文件"、"导入论文"、"inbox"、"上传到NotebookLM"、
  "ingest"、"扫描新文件"时触发。
  扫描 inbox → 去重 → MinerU 处理 → 分类 → 上传 → 归档。
---

# 文件摄入工作流

将 inbox 中的新文件处理后分类上传到 NotebookLM，同时维护本地镜像。

---

## Step 1: 扫描 inbox

1. 列出 `inbox/` 下所有文件（忽略 `.gitkeep`）
2. 按类型分组：
   - **PDF** → 需 MinerU 处理
   - **Markdown (.md)** → 直接可用，跳过 MinerU
   - **其他** (.txt/.docx) → 可直接上传 NotebookLM，但无需 MinerU
3. 如果 inbox 为空，告知用户并结束
4. 报告："发现 N 个文件：X 个 PDF，Y 个 Markdown，Z 个其他"

---

## Step 2: 去重检查

运行去重脚本：

```bash
python scripts/hash_check.py -p "inbox/file1.pdf" "inbox/file2.pdf" -r registry/files.json
```

解析 JSON 输出：

- **`duplicate: true`**：该文件已在系统中
  - 显示已有记录：标题、所属 notebooks
  - 询问用户："此文件已存在，是否分配到新的 notebook？"
  - 是 → **跳到 Step 5**（分类），使用已有的 content.md
  - 否 → 跳过此文件
  
- **`duplicate: false`**：新文件，继续 Step 3

---

## Step 3: MinerU 处理（仅 PDF）

对每个新 PDF 文件：

```bash
C:/Users/Yuhang/miniconda3/envs/mineru/python.exe \
  "C:/Users/Yuhang/.claude/skills/mineru/scripts/run_mineru.py" \
  -p "<inbox/filename.pdf>" -o "library/_processing/"
```

产出结构（在 `library/_processing/` 下）：
```
filename.md
filename_images/
```

**异常处理**：
- MinerU 失败 → 提示用户，提供两个选项：
  1. 跳过此文件
  2. 直接上传原始 PDF 到 NotebookLM（`notebooklm source add "inbox/file.pdf" -n <UUID> --json`）
- 大文件（>50页）→ 预警处理时间可能较长

**非 PDF 文件**：
- `.md` 文件：直接复制到 `library/_processing/`，无需 MinerU
- `.txt/.docx`：直接使用，标注 type 为对应格式

---

## Step 4: 生成文件画像

对每个处理后的文件：

1. 读取 `.md` 文件前 100 行
2. 提取/生成：
   - **title**：论文标题（通常在 md 前几行）
   - **summary**：1-2 句中文描述，说明论文研究了什么
   - **type**：`paper` / `report` / `protocol` / `other`
   - **keywords**：3-5 个英文关键词
3. 用 AskUserQuestion 向用户展示画像，允许修改后确认

---

## Step 5: 分类（交互式）

1. 读 `~/.notebooklm/library_index.json` 获取当前所有 notebook

2. 对每个文件，基于 keywords 和 summary 匹配合适的 notebooks：
   - 将文件 keywords 与每本 notebook 的 tags 比对
   - 将文件 summary 与 notebook description 做语义关联判断
   - 同时考虑 category：方法论论文优先匹配 method 类 notebook，项目文献优先匹配对应 project 类

3. 用 AskUserQuestion 展示建议：
   - 列出推荐的 notebook（附描述），支持多选
   - 提供"创建新笔记本"选项
   - 提供"跳过此文件"选项

4. 如用户选择创建新 notebook → **委托 manage skill 的流程 B**，获取新 UUID 后返回

5. 一篇文件可以选择多个 notebook（例如同时选 project 和 method 类）

---

## Step 6: 容量检查

对每个目标 notebook：

1. 读 catalog 中的 `volumes` 数组，取最新 volume 的 `source_count`
2. 若 `source_count` 为 -1（未同步）→ 运行 `notebooklm source list -n <UUID> --json` 获取实际数量
3. 若接近或达到 300 → **委托 manage skill 的流程 D** 创建分卷
4. 确保后续上传使用最新 volume 的 UUID

---

## Step 7: 上传到 NotebookLM

对每个 文件-notebook 配对：

```bash
notebooklm source add "<content.md 路径>" -n <UUID> --json
```

- 解析返回 JSON 确认上传成功
- 失败时记录错误，继续处理下一个，最后汇总报告
- 不等待 source processing 完成（fire-and-forget）

---

## Step 8: 归档与注册

### 8a. 整理三件套到 Wiki raw

Wiki raw 根目录：`C:/Users/Yuhang/Library/PhD/raw/sources/`

对每个目标 notebook，从 `~/.notebooklm/library_index.json` 读取 notebook 的 `name` 字段，将文件移入对应文件夹：

```
C:/Users/Yuhang/Library/PhD/raw/sources/<notebook-name>/<paper-name>/
├── original.pdf       ← 从 inbox 移入
├── content.md         ← 从 _processing 移入
└── images/            ← 从 _processing 移入（重命名 *_images/ → images/）
```

**notebook-name**：直接使用 notebook 的显示名称（如 `PC047 粘液螺旋菌`、`噬菌体递送`），文件夹不存在时自动创建。

**paper-name** 生成规则：
- 取 `作者年份_关键词` 格式（如 `Smith2024_phage_therapy`）
- kebab-case，限 40 字符内
- 若同名已存在，追加 `-2`

**多 notebook 时**：复制到每个对应 notebook-name 目录

### 8b. 更新注册表

向 `registry/files.json` 追加条目：
```json
{
  "hash": "<sha256>",
  "filename": "<原始文件名>",
  "title": "<提取的标题>",
  "summary": "<中文摘要>",
  "type": "<paper/report/...>",
  "keywords": ["kw1", "kw2"],
  "notebooks": ["uuid1", "uuid2"],
  "local_paths": ["PhD/raw/sources/notebook-name/paper-name/"],
  "processed": true,
  "added": "<today>"
}
```

### 8c. 更新全局 catalog

对每个受影响的 notebook，在 `~/.notebooklm/library_index.json` 中：
- 将最新 volume 的 `source_count` +1
- 更新 `updated` 日期

### 8d. 清理

- 删除 `library/_processing/` 中已归档的临时文件
- 删除 `inbox/` 中已处理完成的文件

### 8e. 报告

输出处理摘要：
```
处理完成：
- 新文件：N 个（M 个 PDF 经 MinerU 解析）
- 重复跳过：X 个
- 上传成功：Y 个（分布到 K 本 notebook）
- 上传失败：Z 个（列出原因）
```
