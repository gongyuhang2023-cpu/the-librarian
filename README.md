# The Librarian

NotebookLM 知识库管理员 — 一个 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 项目，将研究资料（PDF/文献/会议记录）解析、分类后上传到 Google NotebookLM，维护本地镜像与全局目录索引。

## 功能

- **文献摄入**：PDF → MinerU 解析 → 交互式分类 → 上传 NotebookLM → 本地归档
- **会议录制**：自动截图 + 录音 → 转录 → 逐页 PPT 解读 → 导入 NotebookLM
- **笔记本管理**：初始化/创建/容量监控/分卷/回填/远端同步
- **全局路由**：维护 `library_index.json` 目录，其他 Claude Code 项目可按标签自动匹配 notebook

## 依赖

### 必需

| 依赖 | 用途 | 安装验证 |
|------|------|----------|
| [notebooklm-py](https://github.com/nicholasgasior/notebooklm-py) (>=0.3.4) | NotebookLM CLI | `notebooklm --version` |
| Python (>=3.10) | 去重脚本 | `python --version` |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | AI 运行环境 | `claude --version` |

### 可选

| 依赖 | 用途 |
|------|------|
| [MinerU](https://github.com/opendatalab/MinerU) | PDF → Markdown 高质量解析 |
| GPU (CUDA) | MinerU 加速 |
| MeetingMind 录制脚本 | 会议自动截图 + 录音 + 转录 |

### 认证

NotebookLM CLI 需要 Google 账号认证：

```bash
notebooklm login
```

## 快速开始

```bash
# 1. 克隆并进入项目
git clone https://github.com/<your-username>/the-librarian.git
cd the-librarian

# 2. 初始化本地目录和 NotebookLM catalog
mkdir inbox library meetings registry
echo "[]" > registry/files.json

# 3. 启动 Claude Code
claude

# 4. 首次使用：扫描 NotebookLM 账号，构建 catalog
> 初始化

# 5. 日常使用：把 PDF 放进 inbox/，然后
> 处理新文件
```

## 项目结构

```
the-librarian/
├── CLAUDE.md              # Claude Code 入口（硬规则 + skill 路由）
├── .claude/
│   ├── settings.json      # 项目级权限
│   └── skills/
│       ├── ingest/        # 文件摄入流程（8 步）
│       ├── manage/        # 笔记本管理（8 个子流程 A-H）
│       └── meeting/       # 会议录制与导入
├── inbox/                 # 用户放入待处理文件（gitignored）
├── meetings/              # 会议录制数据（gitignored）
├── library/               # 加工后归档，NotebookLM 镜像（gitignored）
├── registry/
│   └── files.json         # 文件画像注册表（gitignored）
└── scripts/
    └── hash_check.py      # SHA-256 去重
```

## 核心数据文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `library_index.json` | `~/.notebooklm/` | 全局 notebook 目录，所有 Claude Code 项目可通过此文件路由查询 |
| `files.json` | `registry/` | 本地文件注册表，记录 hash、标题、摘要、所属 notebooks |

## 工作流

### 摄入新文件 (ingest)

1. 把 PDF/MD 文件放入 `inbox/`
2. 告诉 Claude "处理新文件"
3. Claude 自动：扫描 → hash 去重 → MinerU 解析 → 生成文件画像 → 交互式分类 → 上传 → 归档
4. 一篇论文可同时放入多个 notebook（项目 + 方法论）

### 录制会议 (meeting)

1. 告诉 Claude "录制会议"
2. 选择会议软件、截图灵敏度、麦克风模式
3. 会议结束后说 "结束了"
4. Claude 自动：转录 → 逐页 PPT 解读 → 生成总结 → 交互式分类 → 上传 NotebookLM

### 管理笔记本 (manage)

- **初始化**：扫描 NotebookLM 账号，构建/刷新 catalog
- **创建**：新建 notebook + 自动 backfill 相关旧文献
- **容量**：监控 300 source 上限，自动分卷
- **同步**：对比远端与本地 catalog 差异

## 定制

`CLAUDE.md` 和 `.claude/skills/` 中的路径需要根据你的环境调整：

- MinerU 路径（`CLAUDE.md` 中的 `环境` 部分）
- MeetingMind 脚本路径（`.claude/skills/meeting/SKILL.md`）
- `.claude/settings.json` 中的权限白名单

## License

MIT
