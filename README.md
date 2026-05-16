# The Librarian

**AI-native research knowledge manager** — a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) project that bridges the gap between raw research materials and usable knowledge, serving both AI and human comprehension through a dual-layer architecture.

**AI 原生的研究知识管理员** — 一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 项目，在原始研究资料与可用知识之间架起桥梁，通过双层架构同时服务 AI 和人类的知识需求。

---

## Design Philosophy | 设计哲学

### The Idea | 核心思想

This project is a concrete implementation of the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern proposed by Andrej Karpathy. The core insight: instead of retrieving from raw documents every time (RAG), have the LLM **incrementally build and maintain a persistent wiki** — a structured, interlinked knowledge base that compounds with every source you add. As Karpathy puts it:

本项目是 Andrej Karpathy 提出的 [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式的一个具体实现。核心洞察：不要每次都从原始文档中检索（RAG），而是让 LLM **增量构建和维护一个持久化的 wiki**——一个结构化、互相链接的知识库，随着每份新资料的加入持续复利增长。如 Karpathy 所说：

> "The human's job is to curate sources, direct the analysis, ask good questions, and think about what it all means. The LLM's job is everything else."

### Cognitive Division | 认知分工

Every research task involves four stages. Humans and AI have different strengths at each:

每个研究任务都包含四个认知阶段，人类和 AI 各有所长：

| Stage | Primary | Role of AI | 阶段 | 主导 | AI 角色 |
|-------|---------|------------|------|------|---------|
| **Comprehend** | Human | Provide structured knowledge | **理解** | 人类 | 提供结构化知识 |
| **Think** | AI-assisted | Retrieve evidence, find connections | **思考** | AI 辅助 | 检索证据、发现关联 |
| **Decide** | Human | Present options with trade-offs | **决策** | 人类 | 呈现选项与权衡 |
| **Execute** | AI | Parse, cross-reference, maintain | **执行** | AI | 解析、交叉引用、维护 |

AI is not a replacement for the brain — it's a **plug-in that extends it**. Humans retain direction and judgment; AI amplifies processing bandwidth.

AI 不是大脑的替代品——而是大脑的**增强插件**。人类保留方向感和判断力，AI 放大处理带宽。

### Why Two Layers | 为什么需要双层架构

This division naturally produces two tools serving two consumers:

这种分工自然产生了服务两个消费者的两个工具：

| | **NotebookLM** | **LLM Wiki** |
|---|---|---|
| **Serves** | AI thinking & execution | Human comprehension & decision |
| **Why** | Grounded in full source text — reduces hallucination, enables precise reasoning | Structured accumulation — turns scattered reading into lasting mental models |
| **Format** | Complete parsed markdown | Synthesized, interlinked wiki pages |
| **Access** | Claude Code queries via API | Human reads in Obsidian |

| | **NotebookLM** | **LLM Wiki** |
|---|---|---|
| **服务** | AI 的思考与执行 | 人类的理解与决策 |
| **原因** | 基于全文——减少幻觉，精确推理 | 结构化积累——把碎片阅读变成持久心智模型 |
| **格式** | 完整解析后的 markdown | 综合生成的互联 wiki 页面 |
| **访问** | Claude Code 通过 API 查询 | 人类在 Obsidian 中阅读 |

### The Librarian's Role | 管理员的角色

The Librarian is the **intake hub** — it ensures every piece of research material flows correctly into both layers. You drop a PDF into `inbox/`; it handles parsing, deduplication, classification, upload to NotebookLM, and archiving to wiki raw. The human never touches the bookkeeping.

The Librarian 是这个系统的**入口枢纽**——确保每份研究资料正确流入两层系统。你把 PDF 丢进 `inbox/`，它负责解析、去重、分类、上传 NotebookLM、归档到 wiki raw。人类不碰簿记工作。

| **Human** | **AI (The Librarian)** |
|---|---|
| Drop files into `inbox/` | Parse, deduplicate, classify |
| Choose which notebooks | Upload to NotebookLM |
| Start/stop meeting recording | Transcribe, interpret slides, summarize |
| Ask questions, guide direction | Archive, cross-reference, maintain catalog |
| Read wiki, build understanding | Everything else |

| **人类** | **AI（管理员）** |
|---|---|
| 把文件扔进 `inbox/` | 解析、去重、分类 |
| 选择目标笔记本 | 上传到 NotebookLM |
| 开始/停止会议录制 | 转录、逐页解读、生成总结 |
| 提问、引导方向 | 归档、交叉引用、维护目录 |
| 阅读 wiki，构建理解 | 其余一切 |

---

## Features | 功能

### Ingest — File Processing | 文献摄入

PDF → MinerU parsing → deduplication → interactive classification → upload to NotebookLM → archive to Wiki raw

PDF → MinerU 解析 → hash 去重 → 交互式分类 → 上传 NotebookLM → 归档到 Wiki raw

```
inbox/paper.pdf
  → MinerU extracts markdown + images
  → SHA-256 dedup check against registry
  → Claude generates file profile (title, summary, keywords)
  → User selects target notebooks (multi-select)
  → Upload .md to NotebookLM
  → Archive md to sources/<notebook>/paper.md       (→ flat md-only, for LLM)
  → Archive full package to 00-raw/<notebook>/<paper>/  (→ PDF + md + images backup)
  → Update registry + catalog
```

### Meeting — Record & Import | 会议录制

Auto-screenshot + audio recording → transcription → per-slide interpretation → summary → import to NotebookLM

自动截图 + 录音 → 转录 → 逐页 PPT 解读 → 总结 → 导入 NotebookLM

```
"录制会议"
  → Select software, sensitivity, mic mode
  → Enter meeting title & presenter
  → Background recording (screenshots + audio)
"结束了"
  → Transcribe audio (Qwen3-ASR)
  → Generate interpretation.md (per-slide analysis)
  → Generate summary.md (key takeaways)
  → Classify & upload to NotebookLM
  → Archive md to sources/<notebook>/              (→ flat md-only, for LLM)
  → Archive full data to 00-raw/<notebook>/meeting-YYYY-MM-DD/  (→ screenshots + audio + transcript backup)
```

### Manage — Notebook Administration | 笔记本管理

- **Init**: Scan NotebookLM account, build/refresh `library_index.json` catalog
- **Create**: New notebook + auto-backfill related existing files
- **Capacity**: Monitor 300-source limit, auto-create volumes when full
- **Sync**: Compare remote vs local catalog, resolve differences

- **初始化**：扫描 NotebookLM 账号，构建/刷新全局目录
- **创建**：新建笔记本 + 自动回填相关旧文献
- **容量**：监控 300 source 上限，满时自动分卷
- **同步**：对比远端与本地目录差异

### Global Routing | 全局路由

`~/.notebooklm/library_index.json` serves as a global catalog. Any Claude Code project can read it to automatically route queries to the right notebook by matching tags and descriptions.

`~/.notebooklm/library_index.json` 作为全局目录，任何 Claude Code 项目都可以读取它，按标签和描述自动匹配到正确的笔记本。

---

## Data Flow | 数据流

```
inbox/
  ├─ PDF → MinerU → md ──→ sources/<nb>/paper.md             → NotebookLM + Wiki
  │                └→ 完整包 → 00-raw/<nb>/<paper>/           → full backup (PDF+md+images)
  └─ .md ──→ 直接 ──→ sources/<nb>/paper.md                   → NotebookLM + Wiki
                   └→ 00-raw/<nb>/<paper>/paper.md             → full backup

meetings/ → [meeting] → sources/<nb>/meeting-*.md              → NotebookLM + Wiki
                      → 00-raw/<nb>/meeting-YYYY-MM-DD/        → full backup (screenshots+audio+transcript)

                                       ↕                              ↕
                               registry/files.json        ~/.notebooklm/library_index.json

                                         ↓
                              LLM Wiki reads raw/sources/
                                         ↓
                              Generates wiki/ pages (Obsidian vault)
                                         ↓
                              Human reads in Obsidian

Path config: paths.yaml (single source of truth for all output paths)
```

---

## Quick Start | 快速开始

```bash
# 1. Clone | 克隆
git clone https://github.com/gongyuhang2023-cpu/the-librarian.git
cd the-librarian

# 2. Initialize directories | 初始化目录
mkdir inbox library meetings registry
echo "[]" > registry/files.json

# 3. Authenticate NotebookLM | 认证
notebooklm login

# 4. Launch Claude Code | 启动
claude --dangerously-skip-permissions --model claude-opus-4-6

# 5. First run: scan NotebookLM, build catalog | 首次：构建目录
> 初始化

# 6. Daily use: drop PDFs into inbox/ | 日常：放文件到 inbox/
> 处理新文件

# 7. Record a meeting | 录制会议
> 录制会议
```

---

## Project Structure | 项目结构

```
the-librarian/
├── CLAUDE.md                  # Entry point: hard rules + skill routing
├── .claude/
│   ├── settings.json          # Project-level permissions
│   └── skills/
│       ├── ingest/SKILL.md    # File processing workflow (9 steps)
│       ├── manage/SKILL.md    # Notebook admin (8 sub-flows A–H)
│       └── meeting/SKILL.md   # Meeting recording & import
├── inbox/                     # Drop files here (gitignored)
├── meetings/                  # Recording data (gitignored)
├── library/                   # Processing staging area (gitignored)
├── registry/
│   └── files.json             # File profile registry (gitignored)
├── scripts/
│   └── hash_check.py          # SHA-256 deduplication
└── the-librarian.ico          # Desktop shortcut icon
```

### Key Data Files | 核心数据文件

| File | Location | Purpose |
|------|----------|---------|
| `library_index.json` | `~/.notebooklm/` | Global notebook catalog — shared across all Claude Code projects |
| `files.json` | `registry/` | Local file registry — hash, title, summary, notebook assignments |

| 文件 | 位置 | 作用 |
|------|------|------|
| `library_index.json` | `~/.notebooklm/` | 全局笔记本目录——所有 Claude Code 项目共享 |
| `files.json` | `registry/` | 本地文件注册表——hash、标题、摘要、所属笔记本 |

---

## Dependencies | 依赖

### Required | 必需

| Dependency | Purpose | Verify |
|------------|---------|--------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | AI runtime | `claude --version` |
| [notebooklm-py](https://github.com/nicholasgasior/notebooklm-py) (>=0.3.4) | NotebookLM CLI | `notebooklm --version` |
| Python (>=3.10) | Dedup script | `python --version` |

### Optional | 可选

| Dependency | Purpose |
|------------|---------|
| [MinerU](https://github.com/opendatalab/MinerU) | High-quality PDF → Markdown parsing |
| GPU (CUDA) | MinerU acceleration |
| MeetingMind | Auto screenshot + recording + transcription |
| [LLM Wiki](https://github.com/nashsu/llm_wiki) | Wiki generation from raw sources (human-readable layer) |

---

## Customization | 定制

Paths in `CLAUDE.md` and `.claude/skills/` need to be adapted to your environment:

`CLAUDE.md` 和 `.claude/skills/` 中的路径需要根据你的环境调整：

- **Output paths**: edit `paths.yaml` (single source of truth for all archive paths)
- MinerU path (`CLAUDE.md` → Environment section)
- MeetingMind script path (`.claude/skills/meeting/SKILL.md`)
- Permission allowlist (`.claude/settings.json`)

