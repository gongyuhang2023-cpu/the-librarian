---
name: manage
description: |
  NotebookLM 笔记本管理。当用户提到"创建笔记本"、"笔记本列表"、"容量检查"、
  "回填"、"backfill"、"更新描述"、"同步目录"、"manage"、"初始化"、"init"时触发。
---

# NotebookLM 笔记本管理

本 skill 管理 NotebookLM notebooks 的生命周期。所有操作围绕全局 catalog `~/.notebooklm/library_index.json` 进行。

选择下方对应的子流程执行。

---

## A. 查看/浏览笔记本

1. 读 `~/.notebooklm/library_index.json`
2. 按 category 分组展示：名称、UUID 前缀、source_count、描述
3. 若用户指定关键词，按 `tags` 和 `description` 过滤

---

## B. 创建笔记本

1. 用 AskUserQuestion 询问：
   - 笔记本名称
   - 分类：project / method / standard / tool
   - 描述（中文，1-2 句话，清晰说明此 notebook 收录什么内容）
   - 标签（3-5 个英文关键词）

2. 运行：
   ```bash
   notebooklm create "<name>" --json
   ```
   
3. 从返回的 JSON 中提取 UUID

4. 生成 slug（kebab-case，ASCII 安全，如 "PC047-Mucispirillum研究" → `pc047-mucispirillum`）

5. 创建本地镜像目录：`library/<slug>/`

6. 写入 `~/.notebooklm/library_index.json`，追加条目：
   ```json
   {
     "uuid": "<extracted-uuid>",
     "name": "<name>",
     "slug": "<slug>",
     "category": "<category>",
     "tags": ["tag1", "tag2"],
     "description": "<description>",
     "volumes": [{"uuid": "<extracted-uuid>", "source_count": 0}],
     "updated": "<today>"
   }
   ```

7. 提示用户："是否扫描现有文件库，回填相关文献到新笔记本？" → 是则执行流程 E

---

## C. 更新描述/标签

1. 用户指定 notebook（按名称或 UUID 前缀）
2. 在 catalog 中查找对应条目
3. 用 AskUserQuestion 获取新的 description 和/或 tags
4. 更新 `~/.notebooklm/library_index.json` 中对应条目
5. 无需调用 NotebookLM API（catalog 是本地元数据）

---

## D. 容量检查

1. 对目标 notebook 运行：
   ```bash
   notebooklm source list -n <UUID> --json
   ```
   
2. 统计实际 source 数量，更新 catalog 中的 `source_count`

3. 阈值判断：
   - < 280：正常
   - 280-299：警告，提示接近上限
   - 300：已满，建议创建分卷

4. **创建分卷**（用户确认后）：
   - 运行 `notebooklm create "<原名>-vol2" --json`
   - 在 catalog 中找到原 notebook，向 `volumes` 数组追加：
     ```json
     {"uuid": "<new-uuid>", "source_count": 0}
     ```
   - 后续 ingest 只向最新 volume 添加 source

---

## E. Backfill 扫描

新建 notebook 后触发，或用户手动请求。

1. 读 `registry/files.json` 获取全部已有文件画像

2. 读新 notebook 的 `description`、`tags`、`category`

3. 匹配候选文件：
   - 比对 file 的 `keywords` 与 notebook 的 `tags`
   - 用文件 `summary` 和 notebook `description` 的语义相关性辅助判断
   
4. 过滤规则：
   - **通用知识类**（type 为 "other" 或 keywords 含 "general"/"tutorial"）→ 跳过，Claude 自身具备此类知识
   - **已在该 notebook 中的文件**（file.notebooks 含目标 UUID）→ 跳过
   - **项目文献候选** → 保留，列出给用户

5. 用 AskUserQuestion 展示候选列表，每条显示：
   - 标题 + 摘要
   - 当前所属 notebooks
   - 让用户勾选要加入的

6. 对选中文件：
   - `notebooklm source add "<content.md 路径>" -n <UUID> --json`
   - 复制文件夹到 `library/<new-slug>/<paper-name>/`
   - 更新 `registry/files.json`：向该文件的 `notebooks` 数组追加新 UUID，`local_paths` 追加新路径
   - 更新 catalog 的 `source_count`

---

## F. 同步远端目录

用于 catalog 与 NotebookLM 实际状态对齐。

1. 运行 `notebooklm list --json` 获取远端全部 notebook

2. 与本地 `library_index.json` 对比：
   - **远端有、本地无**：新 notebook（可能在 web UI 手动创建的）→ 提示用户补充描述和标签，加入 catalog
   - **本地有、远端无**：已删除的 notebook → 提示用户是否从 catalog 移除
   - **source_count 不一致**：更新 catalog 中的计数

3. 报告同步结果

---

## H. 初始化 / Init

首次使用或需要重建 catalog 时执行。

1. 检查 `~/.notebooklm/library_index.json` 是否存在

2. 验证 NotebookLM 认证状态：
   ```bash
   notebooklm auth check --json
   ```
   - 未认证 → 提示用户在真实终端（PowerShell/Windows Terminal）运行 `notebooklm login`
   - 已认证 → 继续

3. 扫描远端 notebook 列表：
   ```bash
   notebooklm list --json
   ```

4. **如果 catalog 不存在**（全新初始化）：
   - 解析所有 notebook 的 id 和 title
   - 按标题启发式分类：
     - 含 PC0/实验编号/菌名 → category: `project`
     - 含 方法/method/protocol/analysis → category: `method`
     - 含 规范/guide/standard/writing → category: `standard`
     - 含 工具名/IDE/tutorial → category: `tool`
     - 其余 → category: `uncategorized`
   - 为每本生成 slug（kebab-case，ASCII 安全）
   - 初始化 volumes：`[{"uuid": "<id>", "source_count": -1}]`
   - 用 AskUserQuestion 向用户展示分类结果，允许批量调整
   - 写入 `~/.notebooklm/library_index.json`

5. **如果 catalog 已存在**（刷新）：
   - 执行流程 F（同步远端目录）
   - 报告新增/删除/变更

6. 检查本地目录结构完整性：
   - `inbox/` 存在？
   - `library/` 存在？
   - `registry/files.json` 存在且为合法 JSON？
   - 不存在则自动创建

7. 报告初始化结果：
   ```
   初始化完成：
   - Catalog：N 本 notebook 已索引（project: X, method: Y, standard: Z, tool: W, uncategorized: U）
   - 认证状态：已认证（user@email.com）
   - 本地结构：完整
   ```

---

## G. 注册表维护

定期健康检查。

1. 遍历 `registry/files.json`：
   - `local_paths` 中的目录是否实际存在？
   - `notebooks` 中的 UUID 是否仍在 catalog 中？

2. 遍历 `library/` 子目录：
   - 是否有未在 files.json 注册的文件夹？

3. 报告：
   - 孤立记录（registry 有但文件已不存在）
   - 未注册文件（library 有但 registry 中无记录）
   - 无效 notebook 引用

4. 用户确认后执行清理
