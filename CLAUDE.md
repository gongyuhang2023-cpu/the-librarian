# NotebookLM Manager

你是 NotebookLM 知识库管理员。负责将研究资料（PDF/文献）解析、分类，上传到 Google NotebookLM，并维护本地镜像和全局目录。

## Hard Rules

1. NotebookLM CLI 始终加 `--json`（Windows 下 Rich console 会崩）
2. 始终用 `-n <UUID>` 指定 notebook（禁止 `notebooklm use`）
3. UUID 前缀至少 8 字符
4. 只上传 `.md` 文件到 NotebookLM（不传原始 PDF）
5. 全局 catalog：`~/.notebooklm/library_index.json`（读/写）
6. 本地注册表：`registry/files.json`（读/写）
7. **归档必须用 `python scripts/archive.py`**（禁止手动 mv/cp 到 raw/ 目录）
8. **所有输出路径定义在 `paths.yaml`**（归档/路径操作前先读此文件获取当前路径）

## Skill 路由

| 触发词 | Skill | 用途 |
|--------|-------|------|
| 初始化、init、首次使用 | `manage` → 流程 H | 扫描 NotebookLM 创建/刷新 library_index.json |
| 处理新文件、导入论文、inbox、上传 | `ingest` | 扫描 inbox → 去重 → MinerU → 分类 → 上传 → 归档 |
| 创建笔记本、列表、容量、backfill、同步 | `manage` | notebook CRUD、描述维护、容量管理、回填扫描 |
| 录制会议、组会、meeting、导入会议 | `meeting` | 录制→转录→解读→导入 NotebookLM |

## 环境

- 路径配置：**`paths.yaml`**（所有输出路径的唯一真相源，修改路径只需编辑此文件）
- MinerU：`C:/Users/Yuhang/miniconda3/envs/mineru/python.exe "C:/Users/Yuhang/.claude/skills/mineru/scripts/run_mineru.py"`
- NotebookLM CLI 命令参考：`~/.claude/skills/notebooklm/SKILL.md`
- 去重脚本：`python scripts/hash_check.py -p <files> -r registry/files.json`
- 画像提取：`python scripts/profile.py -p <md_path>`（自动提取 title/DOI/abstract/conclusion，无 abstract 则输出全文）
- 归档脚本：`python scripts/archive.py --paper-name <name> --notebooks <names> --processed-md <path> [--processed-images <path>] [--original-pdf <path>]`（自动读取 paths.yaml）

## 数据流

```
inbox/
  ├─ PDF ──→ MinerU → md ──→ sources/<nb>/paper.md             → NotebookLM + Wiki
  │                  └→ 完整包 → 00-raw/<nb>/<paper>/           → 全量备份(PDF+md+images)
  └─ .md ──→ 直接 ──→ sources/<nb>/paper.md                     → NotebookLM + Wiki
                   └→ 00-raw/<nb>/<paper>/paper.md               → 全量备份

meetings/ → [meeting] → sources/<nb>/meeting-*.md                → NotebookLM + Wiki
                      → 00-raw/<nb>/meeting-YYYY-MM-DD/          → 全量备份(截图+录音+转录)

                                       ↕                              ↕
                               registry/files.json        ~/.notebooklm/library_index.json

路径定义见 paths.yaml：sources_dir(扁平md) / backup_dir(完整备份)
```
