# The Librarian

**AI-native research knowledge manager** — a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) project that bridges the gap between raw research materials and usable knowledge, serving both AI and human comprehension through a dual-layer architecture.

[中文版](README_zh.md)

---

## Design Philosophy

### The Idea

This project is a concrete implementation of the [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) pattern proposed by Andrej Karpathy. The core insight: instead of retrieving from raw documents every time (RAG), have the LLM **incrementally build and maintain a persistent wiki** — a structured, interlinked knowledge base that compounds with every source you add. As Karpathy puts it:

> "The human's job is to curate sources, direct the analysis, ask good questions, and think about what it all means. The LLM's job is everything else."

### Cognitive Division

Every research task involves four stages. Humans and AI have different strengths at each:

| Stage | Primary | Role of AI |
|-------|---------|------------|
| **Comprehend** | Human | Provide structured knowledge |
| **Think** | AI-assisted | Retrieve evidence, find connections |
| **Decide** | Human | Present options with trade-offs |
| **Execute** | AI | Parse, cross-reference, maintain |

AI is not a replacement for the brain — it's a **plug-in that extends it**. Humans retain direction and judgment; AI amplifies processing bandwidth.

### Why Two Layers

This division naturally produces two tools serving two consumers:

| | **NotebookLM** | **LLM Wiki** |
|---|---|---|
| **Serves** | AI thinking & execution | Human comprehension & decision |
| **Why** | Grounded in full source text — reduces hallucination, enables precise reasoning | Structured accumulation — turns scattered reading into lasting mental models |
| **Format** | Complete parsed markdown | Synthesized, interlinked wiki pages |
| **Access** | Claude Code queries via API | Human reads in Obsidian |

### The Librarian's Role

The Librarian is the **intake hub** — it ensures every piece of research material flows correctly into both layers. You drop a PDF into `inbox/`; it handles parsing, deduplication, classification, upload to NotebookLM, and archiving to wiki raw. The human never touches the bookkeeping.

| **Human** | **AI (The Librarian)** |
|---|---|
| Drop files into `inbox/` | Parse, deduplicate, classify |
| Choose which notebooks | Upload to NotebookLM |
| Start/stop meeting recording | Transcribe, interpret slides, summarize |
| Ask questions, guide direction | Archive, cross-reference, maintain catalog |
| Read wiki, build understanding | Everything else |

---

## Features

### Ingest — File Processing

PDF → MinerU parsing → deduplication → interactive classification → upload to NotebookLM → archive to Wiki raw

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

### Meeting — Record & Import

Auto-screenshot + audio recording → transcription → per-slide interpretation → summary → import to NotebookLM

```
"Start recording"
  → Select software, sensitivity, mic mode
  → Enter meeting title & presenter
  → Background recording (screenshots + audio)
"Done"
  → Transcribe audio (Qwen3-ASR)
  → Generate interpretation.md (per-slide analysis)
  → Generate summary.md (key takeaways)
  → Classify & upload to NotebookLM
  → Archive md to sources/<notebook>/              (→ flat md-only, for LLM)
  → Archive full data to 00-raw/<notebook>/meeting-YYYY-MM-DD/  (→ screenshots + audio + transcript backup)
```

### Manage — Notebook Administration

- **Init**: Scan NotebookLM account, build/refresh `library_index.json` catalog
- **Create**: New notebook + auto-backfill related existing files
- **Capacity**: Monitor 300-source limit, auto-create volumes when full
- **Sync**: Compare remote vs local catalog, resolve differences

### Global Routing

`~/.notebooklm/library_index.json` serves as a global catalog. Any Claude Code project can read it to automatically route queries to the right notebook by matching tags and descriptions.

---

## Data Flow

```
inbox/
  ├─ PDF → MinerU → md ──→ sources/<nb>/paper.md             → NotebookLM + Wiki
  │                └→ full package → 00-raw/<nb>/<paper>/     → full backup (PDF+md+images)
  └─ .md ──→ direct ──→ sources/<nb>/paper.md                 → NotebookLM + Wiki
                     └→ 00-raw/<nb>/<paper>/paper.md           → full backup

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

## Quick Start

```bash
# 1. Clone
git clone https://github.com/gongyuhang2023-cpu/the-librarian.git
cd the-librarian

# 2. Initialize directories
mkdir inbox library meetings registry
echo "[]" > registry/files.json

# 3. Authenticate NotebookLM
notebooklm login

# 4. Launch Claude Code
claude --dangerously-skip-permissions --model claude-opus-4-6

# 5. First run: scan NotebookLM, build catalog
> 初始化

# 6. Daily use: drop PDFs into inbox/
> 处理新文件

# 7. Record a meeting
> 录制会议
```

---

## Project Structure

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

### Key Data Files

| File | Location | Purpose |
|------|----------|---------|
| `library_index.json` | `~/.notebooklm/` | Global notebook catalog — shared across all Claude Code projects |
| `files.json` | `registry/` | Local file registry — hash, title, summary, notebook assignments |

---

## Dependencies

### Required

| Dependency | Purpose | Verify |
|------------|---------|--------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | AI runtime | `claude --version` |
| [notebooklm-py](https://github.com/nicholasgasior/notebooklm-py) (>=0.3.4) | NotebookLM CLI | `notebooklm --version` |
| Python (>=3.10) | Dedup script | `python --version` |

### Optional

| Dependency | Purpose |
|------------|---------|
| [MinerU](https://github.com/opendatalab/MinerU) | High-quality PDF → Markdown parsing |
| GPU (CUDA) | MinerU acceleration |
| MeetingMind | Auto screenshot + recording + transcription |
| [LLM Wiki](https://github.com/nashsu/llm_wiki) | Wiki generation from raw sources (human-readable layer) |

---

## Customization

Paths in `CLAUDE.md` and `.claude/skills/` need to be adapted to your environment:

- **Output paths**: edit `paths.yaml` (single source of truth for all archive paths)
- MinerU path (`CLAUDE.md` → Environment section)
- MeetingMind script path (`.claude/skills/meeting/SKILL.md`)
- Permission allowlist (`.claude/settings.json`)
