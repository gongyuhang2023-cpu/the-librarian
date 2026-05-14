# The Librarian

**AI-native research knowledge manager** — a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) project that bridges the gap between raw research materials and usable knowledge, serving both AI and human comprehension through a dual-layer architecture.

**AI 原生的研究知识管理员** — 一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 项目，在原始研究资料与可用知识之间架起桥梁，通过双层架构同时服务 AI 和人类的知识需求。

---

## Design Philosophy | 设计哲学

### The Problem | 问题

Research materials accumulate fast — papers, meeting notes, protocols. But raw PDFs sitting in folders aren't knowledge. They need to be parsed, organized, cross-referenced, and made accessible. Humans shouldn't do this bookkeeping. AI should.

研究资料积累很快——论文、会议记录、实验方案。但堆在文件夹里的 PDF 不是知识，它们需要被解析、分类、交叉引用、变得可检索。人类不该做这些簿记工作，AI 应该来做。

### Two Consumers, Two Formats | 两种消费者，两种格式

AI and humans consume knowledge differently. This project serves both:

AI 和人类消费知识的方式完全不同。本项目同时服务两者：

| | **AI (Claude Code)** | **Human (Researcher)** |
|---|---|---|
| **Needs** | Full-text, precise, searchable | Distilled, structured, narrative |
| **Platform** | Google NotebookLM | LLM Wiki (Obsidian vault) |
| **Format** | Parsed markdown (complete) | Synthesized wiki pages (curated) |
| **Access** | API query | Read in Obsidian |

| | **AI (Claude Code)** | **人类（研究者）** |
|---|---|---|
| **需要** | 全文、精确、可检索 | 提炼、结构化、叙事性 |
| **平台** | Google NotebookLM | LLM Wiki（Obsidian 知识库） |
| **格式** | 解析后的 markdown（完整） | 综合生成的 wiki 页面（策展） |
| **访问** | API 查询 | Obsidian 阅读 |

### The Knowledge Loop | 知识飞轮

```
Raw Literature ──→ NotebookLM (AI knowledge base)
                        │
                   Claude Code queries
                        │
                   LLM Wiki generates Synthesis
                        │
                   Human reads & understands
                        │
                   Better questions & mental models
                        │
                   Higher quality Synthesis ──→ Deeper understanding
                        │
                        └──→ (cycle continues)
```

The Librarian is the **intake hub** of this loop — it ensures every piece of research material flows into both layers:

The Librarian 是这个飞轮的**入口枢纽**——确保每份研究资料都流入两层系统：

1. **NotebookLM** (L2 cache) — full source text for AI verification and deep queries
2. **Wiki raw** (L1 cache) — local markdown for LLM Wiki to generate human-readable synthesis

### Human–AI Division of Labor | 人机分工

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
  → Archive md + images to raw/sources/<notebook>/  (→ Wiki + Drive)
  → Archive original PDF to raw/pdfs/<notebook>/    (→ local only)
  → Insert PDF link into content.md header
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
  → Archive to PhD/raw/sources/<notebook-name>/
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
  ├─ PDF → MinerU → md + images → raw/sources/<notebook>/  → NotebookLM + Wiki + Drive
  │                └ original.pdf → raw/pdfs/<notebook>/    → local only
  └─ .md ─────────────────────── → raw/sources/<notebook>/  → NotebookLM + Wiki + Drive

meetings/ → [meeting] ─────────→ raw/sources/<notebook>/  → NotebookLM + Wiki + Drive

                                         ↕                            ↕
                                 registry/files.json      ~/.notebooklm/library_index.json

                                         ↓
                              LLM Wiki reads raw/sources/
                                         ↓
                              Generates wiki/ pages (Obsidian vault)
                                         ↓
                              Human reads in Obsidian
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

- MinerU path (`CLAUDE.md` → Environment section)
- MeetingMind script path (`.claude/skills/meeting/SKILL.md`)
- Wiki raw storage path (default: `~/Library/PhD/raw/sources/`)
- Permission allowlist (`.claude/settings.json`)

---

## License

MIT
