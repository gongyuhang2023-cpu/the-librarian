---
name: manage
description: |
  NotebookLM 笔记本管理。当用户提到"创建笔记本"、"笔记本列表"、"容量检查"、
  "回填"、"backfill"、"更新描述"、"同步目录"、"manage"、"初始化"、"init"时触发。
---

# NotebookLM 笔记本管理

所有操作围绕 `~/.notebooklm/library_index.json`。按用户意图选择子流程。

---

## A. 查看笔记本

读 `~/.notebooklm/library_index.json`，按 category 分组展示。有关键词时按 tags/description 过滤。

## B. 创建笔记本

1. AskUserQuestion：名称、分类(project/method/standard/tool)、描述(中文)、标签(英文 3-5 个)

2. ```bash
   notebooklm create "<name>" --json
   ```

3. 从 JSON 提取 UUID，生成 slug（kebab-case ASCII），写入 catalog：
   ```json
   {
     "uuid": "<uuid>", "name": "<name>", "slug": "<slug>",
     "category": "<cat>", "tags": ["..."], "description": "...",
     "volumes": [{"uuid": "<uuid>", "source_count": 0}],
     "updated": "<today>"
   }
   ```

4. 提示用户是否执行流程 E（backfill）

## C. 更新描述/标签

用户指定 notebook → AskUserQuestion 获取新 description/tags → 更新 catalog。纯本地操作。

## D. 容量检查

```bash
notebooklm source list -n <UUID> --json
```

更新 catalog `source_count`。阈值：<280 正常 / 280-299 警告 / 300 已满。

**创建分卷**（满时，用户确认后）：
```bash
notebooklm create "<原名>-vol2" --json
```
向原 notebook 的 `volumes` 数组追加 `{"uuid": "<new>", "source_count": 0}`。后续 ingest 用最新 volume。

## E. Backfill 扫描

1. 读 `registry/files.json` 全部文件 + 新 notebook 的 tags/description

2. 匹配：file keywords vs notebook tags + summary vs description 语义相关性

3. 过滤：跳过通用知识类（type=other / keywords 含 general/tutorial）、跳过已在该 notebook 中的

4. AskUserQuestion 展示候选（标题+摘要+当前所属），用户勾选

5. 选中文件：
   - `notebooklm source add "<content.md>" -n <UUID> --json`
   - 复制到 `PhD/raw/sources/<notebook-name>/<paper-name>/`
   - 更新 files.json（notebooks 追加 UUID，content_paths 追加路径）
   - 更新 catalog source_count

## F. 同步远端

```bash
notebooklm list --json
```

与 catalog 对比：
- 远端有本地无 → 补充描述/标签加入 catalog
- 本地有远端无 → 提示是否移除
- source_count 不一致 → 更新

## G. 注册表维护

遍历 `registry/files.json` 和 `PhD/raw/sources/`，报告：孤立记录（registry 有文件无）、未注册文件（文件有 registry 无）、无效 notebook 引用。用户确认后清理。

## H. 初始化

1. 验证认证：`notebooklm auth check --json`（未认证 → 提示在真实终端运行 `notebooklm login`）

2. 扫描远端：`notebooklm list --json`

3. **catalog 不存在**（全新）：
   - 按标题启发式分类：含实验编号/菌名→project，含方法/protocol→method，含规范/guide→standard，含工具名→tool，其余→uncategorized
   - 生成 slug，初始化 volumes（source_count: -1）
   - AskUserQuestion 展示分类结果，允许批量调整
   - 写入 catalog

4. **catalog 已存在**（刷新）：执行流程 F

5. 检查本地目录（inbox/library/registry/files.json），缺失则创建

6. 报告：N 本 notebook 已索引（按 category 统计）
