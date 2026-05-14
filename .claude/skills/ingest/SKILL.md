---
name: ingest
description: |
  文件摄入工作流。当用户提到"处理新文件"、"导入论文"、"inbox"、"上传到NotebookLM"、
  "ingest"、"扫描新文件"时触发。
  扫描 inbox → 去重 → MinerU → 分类 → 上传 → 归档。
---

# 文件摄入工作流

inbox → 去重 → MinerU → 画像 → 分类 → 上传 NotebookLM → archive.py 归档 → 注册 → 清理

---

## Step 1: 扫描 inbox

列出 `inbox/` 所有文件（忽略 `.gitkeep`），按类型分组（PDF / .md / 其他）。空则结束。

## Step 2: 去重

```bash
python scripts/hash_check.py -p "inbox/file1.pdf" "inbox/file2.pdf" -r registry/files.json
```

- `duplicate: true` → 问用户是否分配到新 notebook，是则跳到 Step 5，否则跳过
- `duplicate: false` → 继续 Step 3

## Step 3: MinerU（仅 PDF）

**必须用绝对路径：**

```bash
C:/Users/Yuhang/miniconda3/envs/mineru/python.exe \
  "C:/Users/Yuhang/.claude/skills/mineru/scripts/run_mineru.py" \
  -p "C:/Users/Yuhang/Library/the-librarian/inbox/<filename>.pdf" \
  -o "C:/Users/Yuhang/Library/the-librarian/library/_processing/"
```

完成后用 `ls library/_processing/*.md` 确认产出文件名（MinerU 会清洗文件名）。

非 PDF 文件直接 `cp` 到 `library/_processing/`。MinerU 失败时让用户选择跳过或直接上传原始 PDF。

## Step 4: 生成画像

```bash
python scripts/profile.py -p "library/_processing/<sanitized>.md"
```

脚本自动提取 title、DOI、authors、abstract、conclusion（有则用，无则输出全文）。
基于脚本输出生成：title / summary（中文）/ type / keywords（英文 3-5 个）。AskUserQuestion 让用户确认。

## Step 5: 分类

1. 读 `~/.notebooklm/library_index.json`
2. 按 keywords vs tags、summary vs description 匹配 notebooks
3. AskUserQuestion 多选目标 notebooks（可新建 → 委托 manage skill 流程 B）

## Step 6: 容量检查

读 catalog 中 `source_count`，-1 则 `notebooklm source list -n <UUID> --json` 获取实际数。接近 300 → 委托 manage skill 流程 D 创建分卷。

## Step 7: 上传

```bash
notebooklm source add "<library/_processing/xxx.md>" -n <UUID> --json
```

失败记录错误，继续下一个。

## Step 8: 归档与注册

### 8a. 归档（必须用 archive.py）

> **⚠️ 禁止手动 mv/cp 文件到 raw/ 目录。必须调用此脚本。**

生成 PAPER_NAME：`作者年份_关键词` 格式，snake_case，≤40 字符。
NOTEBOOK_NAME：从 library_index.json 读 `name` 字段。

```bash
python scripts/archive.py \
  --paper-name "<PAPER_NAME>" \
  --notebooks "<NOTEBOOK_NAME_1>" "<NOTEBOOK_NAME_2>" \
  --processed-md "library/_processing/<sanitized>.md" \
  --processed-images "library/_processing/<sanitized>_images/" \
  --original-pdf "inbox/<original>.pdf"
```

无图片省略 `--processed-images`，非 PDF 源省略 `--original-pdf`。
确认输出 JSON 的 `status` 为 `ok`。

### 8b. 更新注册表

从 archive.py 输出取 `content_paths` 和 `pdf_path`，向 `registry/files.json` 追加：

```json
{
  "hash": "<sha256>", "filename": "<原始文件名>",
  "title": "<标题>", "summary": "<中文摘要>",
  "type": "<paper/book/...>", "keywords": ["kw1", "kw2"],
  "notebooks": ["uuid1", "uuid2"],
  "content_paths": ["PhD/raw/sources/<notebook>/<paper>/"],
  "pdf_path": "PhD/raw/pdfs/<notebook>/<paper>.pdf",
  "processed": true, "added": "<today>"
}
```

### 8c. 更新 catalog

`~/.notebooklm/library_index.json` 中对应 notebook 的 `source_count` +1，`updated` 改为今天。

### 8d. 清理

```bash
rm -rf library/_processing/*
rm "inbox/<已处理的文件>"
# 保留 inbox/.gitkeep
```

### 8e. 报告

```
处理完成：N 个新文件 / X 个跳过 / Y 个上传成功 → K 本 notebook / Z 个失败
```
