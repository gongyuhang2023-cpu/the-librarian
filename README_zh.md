# The Librarian

**AI 原生的研究知识管理员** — 一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 项目，在原始研究资料与可用知识之间架起桥梁，通过双层架构同时服务 AI 和人类的知识需求。

[English](README.md)

---

## 设计哲学

### 核心思想

本项目是 Andrej Karpathy 提出的 [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式的一个具体实现。核心洞察：不要每次都从原始文档中检索（RAG），而是让 LLM **增量构建和维护一个持久化的 wiki**——一个结构化、互相链接的知识库，随着每份新资料的加入持续复利增长。如 Karpathy 所说：

> "The human's job is to curate sources, direct the analysis, ask good questions, and think about what it all means. The LLM's job is everything else."

### 认知分工

每个研究任务都包含四个认知阶段，人类和 AI 各有所长：

| 阶段 | 主导 | AI 角色 |
|------|------|---------|
| **理解** | 人类 | 提供结构化知识 |
| **思考** | AI 辅助 | 检索证据、发现关联 |
| **决策** | 人类 | 呈现选项与权衡 |
| **执行** | AI | 解析、交叉引用、维护 |

AI 不是大脑的替代品——而是大脑的**增强插件**。人类保留方向感和判断力，AI 放大处理带宽。

### 为什么需要双层架构

这种分工自然产生了服务两个消费者的两个工具：

| | **NotebookLM** | **LLM Wiki** |
|---|---|---|
| **服务** | AI 的思考与执行 | 人类的理解与决策 |
| **原因** | 基于全文——减少幻觉，精确推理 | 结构化积累——把碎片阅读变成持久心智模型 |
| **格式** | 完整解析后的 markdown | 综合生成的互联 wiki 页面 |
| **访问** | Claude Code 通过 API 查询 | 人类在 Obsidian 中阅读 |

### 管理员的角色

The Librarian 是这个系统的**入口枢纽**——确保每份研究资料正确流入两层系统。你把 PDF 丢进 `inbox/`，它负责解析、去重、分类、上传 NotebookLM、归档到 wiki raw。人类不碰簿记工作。

| **人类** | **AI（管理员）** |
|---|---|
| 把文件扔进 `inbox/` | 解析、去重、分类 |
| 选择目标笔记本 | 上传到 NotebookLM |
| 开始/停止会议录制 | 转录、逐页解读、生成总结 |
| 提问、引导方向 | 归档、交叉引用、维护目录 |
| 阅读 wiki，构建理解 | 其余一切 |

---

## 功能

### 文献摄入

PDF → MinerU 解析 → hash 去重 → 交互式分类 → 上传 NotebookLM → 归档到 Wiki raw

```
inbox/paper.pdf
  → MinerU 提取 markdown + 图片
  → SHA-256 去重检查
  → Claude 生成文件档案（标题、摘要、关键词）
  → 用户选择目标笔记本（多选）
  → 上传 .md 到 NotebookLM
  → 归档 md 到 sources/<notebook>/paper.md       (→ 扁平纯 md，供 LLM 消费)
  → 归档完整包到 00-raw/<notebook>/<paper>/        (→ PDF + md + 图片备份)
  → 更新注册表 + 目录
```

### 会议录制

自动截图 + 录音 → 转录 → 逐页 PPT 解读 → 总结 → 导入 NotebookLM

```
"录制会议"
  → 选择软件、灵敏度、麦克风模式
  → 输入会议标题和主讲人
  → 后台录制（截图 + 录音）
"结束了"
  → 转录音频（Qwen3-ASR）
  → 生成 interpretation.md（逐页解读）
  → 生成 summary.md（要点总结）
  → 分类并上传到 NotebookLM
  → 归档 md 到 sources/<notebook>/              (→ 扁平纯 md，供 LLM 消费)
  → 归档原始数据到 00-raw/<notebook>/meeting-YYYY-MM-DD/  (→ 截图 + 录音 + 转录备份)
```

### 笔记本管理

- **初始化**：扫描 NotebookLM 账号，构建/刷新全局目录
- **创建**：新建笔记本 + 自动回填相关旧文献
- **容量**：监控 300 source 上限，满时自动分卷
- **同步**：对比远端与本地目录差异

### 全局路由

`~/.notebooklm/library_index.json` 作为全局目录，任何 Claude Code 项目都可以读取它，按标签和描述自动匹配到正确的笔记本。

---

## 数据流

```
inbox/
  ├─ PDF → MinerU → md ──→ sources/<nb>/paper.md             → NotebookLM + Wiki
  │                └→ 完整包 → 00-raw/<nb>/<paper>/           → 全量备份 (PDF+md+图片)
  └─ .md ──→ 直接 ──→ sources/<nb>/paper.md                   → NotebookLM + Wiki
                   └→ 00-raw/<nb>/<paper>/paper.md             → 全量备份

meetings/ → [meeting] → sources/<nb>/meeting-*.md              → NotebookLM + Wiki
                      → 00-raw/<nb>/meeting-YYYY-MM-DD/        → 全量备份 (截图+录音+转录)

                                       ↕                              ↕
                               registry/files.json        ~/.notebooklm/library_index.json

                                         ↓
                              LLM Wiki 读取 raw/sources/
                                         ↓
                              生成 wiki/ 页面 (Obsidian vault)
                                         ↓
                              人类在 Obsidian 中阅读

路径配置：paths.yaml（所有输出路径的唯一真相源）
```

---

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/gongyuhang2023-cpu/the-librarian.git
cd the-librarian

# 2. 初始化目录
mkdir inbox library meetings registry
echo "[]" > registry/files.json

# 3. 认证 NotebookLM
notebooklm login

# 4. 启动 Claude Code
claude --dangerously-skip-permissions --model claude-opus-4-6

# 5. 首次运行：扫描 NotebookLM，构建目录
> 初始化

# 6. 日常使用：放 PDF 到 inbox/
> 处理新文件

# 7. 录制会议
> 录制会议
```

---

## 项目结构

```
the-librarian/
├── CLAUDE.md                  # 入口：硬性规则 + skill 路由
├── .claude/
│   ├── settings.json          # 项目级权限
│   └── skills/
│       ├── ingest/SKILL.md    # 文件处理流程（9 步）
│       ├── manage/SKILL.md    # 笔记本管理（8 个子流程 A–H）
│       └── meeting/SKILL.md   # 会议录制与导入
├── inbox/                     # 放文件到这里（gitignored）
├── meetings/                  # 录制数据（gitignored）
├── library/                   # 处理暂存区（gitignored）
├── registry/
│   └── files.json             # 文件档案注册表（gitignored）
├── scripts/
│   └── hash_check.py          # SHA-256 去重
└── the-librarian.ico          # 桌面快捷方式图标
```

### 核心数据文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `library_index.json` | `~/.notebooklm/` | 全局笔记本目录——所有 Claude Code 项目共享 |
| `files.json` | `registry/` | 本地文件注册表——hash、标题、摘要、所属笔记本 |

---

## 依赖

### 必需

| 依赖 | 用途 | 验证 |
|------|------|------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | AI 运行时 | `claude --version` |
| [notebooklm-py](https://github.com/nicholasgasior/notebooklm-py) (>=0.3.4) | NotebookLM CLI | `notebooklm --version` |
| Python (>=3.10) | 去重脚本 | `python --version` |

### 可选

| 依赖 | 用途 |
|------|------|
| [MinerU](https://github.com/opendatalab/MinerU) | 高质量 PDF → Markdown 解析 |
| GPU (CUDA) | MinerU 加速 |
| MeetingMind | 自动截图 + 录制 + 转录 |
| [LLM Wiki](https://github.com/nashsu/llm_wiki) | 从原始资料生成 wiki（人类可读层） |

---

## 定制

`CLAUDE.md` 和 `.claude/skills/` 中的路径需要根据你的环境调整：

- **输出路径**：编辑 `paths.yaml`（所有归档路径的唯一真相源）
- MinerU 路径（`CLAUDE.md` → 环境段）
- MeetingMind 脚本路径（`.claude/skills/meeting/SKILL.md`）
- 权限白名单（`.claude/settings.json`）
