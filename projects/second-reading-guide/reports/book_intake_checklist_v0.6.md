# 第二本 EPUB 导入前清单（v0.6-D0）

> 本文档是 **v0.6-D0** 阶段的导入前清单。它只描述“什么时候、怎么把 EPUB 放入 projects/second-reading-guide/”，
> 并不执行任何 OCR、identify_book 或实际解析。**未导入 EPUB、未修改项目数据、未 commit、未 push。**

本清单适用于 reading-guide 类型的第二本电子书，使用 EPUB 格式。

---

## 1. 第二本书选择标准

### 1.1 适合 reading-guide 的 EPUB 类型

- **文字型 EPUB（text-first）**：正文以可提取 XHTML/HTML 文本为主，章节结构清晰。
- **有完整 nav / toc**：包含 EPUB 3 nav.xhtml 或 EPUB 2 ncx.idx，可以程序化解析章节层级。
- **章节数适中**（10–40 章）：既不至于零碎，也不至于无法人工逐章复核。
- **可读中文或英文**为主，结构层次不会因为多语种混杂而变复杂。
- **引文密度高、概念密度高**：例如非虚构、思想史、社会研究、随笔、人物评传、文学评论、哲学/历史随笔等。
- **可引用页码稳定**：印刷书有页码或 EPUB 内部有稳定锚点，方便 evidence_refs 用 page/anchor 引用。

### 1.2 不适合 reading-guide 的 EPUB 类型

- **图片型 EPUB（image-first）**：正文是扫描图像或整页插图，无法直接抽取文本。
- **强交互 / 富媒体 EPUB**：含大量音频、视频、JS 行为，结构不稳定。
- **DRM 加密 EPUB**：无法在不破坏协议的前提下抽取正文。
- **乱码 / 排版破损 EPUB**：没有合法 container.xml / OPF / nav，结构化抽取会失败。
- **主要是公式 / 化学式 / 复杂表格**：导出的 XHTML 解析成本远高于阅读价值。
- **目录层级过深（>3 层）**：会导致 chapter_reading_cards 数量爆炸，难以人工复核。

### 1.3 推荐篇幅

- **正文 8–20 万字**为佳。
- 短于 5 万字：可能章节不足，导出的 chapter_reading_cards 会过于稀薄。
- 长于 30 万字：会显著拉长 identify_book 与人工复核的时长，且 chapter_reading_cards 体积会超出 GitHub Pages 的合理范围。

### 1.4 推荐章节结构

- **有显式章节标题**：每章有明确 `h1` 或 `h2`，EPUB nav 里能直接列出来。
- **章节之间有清晰断点**：不依赖隐含分页或样式 class。
- **章节内部有可识别小节**：可选；若有，会让 key_concepts / quote_index 抽取更稳定。
- **不含复杂 cross-reference**：避免“参见第 X 章第 Y 节”大量横跳，影响 evidence_refs 准确性。

### 1.5 是否有目录 nav / toc

EPUB 3 标准要求 nav.xhtml；EPUB 2 使用 ncx.idx。**两种都必须有**，否则 chapter_reading_cards 抽取会退化。

### 1.6 是否包含大量图片、脚注、表格或复杂排版

- **少量图片**（每章 ≤ 3 张）：可保留 metadata，不进入正文 evidence_refs。
- **大量脚注 / 尾注**：可作为 quote_index 的潜在来源，但需在 reading-guide 草稿阶段决定是否纳入。
- **复杂表格 / 数学公式**：跳过，跳过的内容标记 `not_extracted` 而不是污染 evidence_refs。
- **整页插图**：跳过，正文 evidence_refs 不会引用这些图。

---

## 2. 导入前文件位置

| 用途 | 路径 | 公开? |
|---|---|---|
| 原始 EPUB | `projects/second-reading-guide/private/source/book.epub` | **否**（`.gitignore` 屏蔽） |
| EPUB 解包中间产物 | `projects/second-reading-guide/working/` | 否 |
| 抽取后纯文本中间产物 | `projects/second-reading-guide/working/book_text/` | 否 |
| 人工审核中间产物 | `projects/second-reading-guide/review_pack/` | 否 |
| 公开结构化数据 | `projects/second-reading-guide/public/*.json` | **是** |
| Web 加载的公开数据 | `web/public/projects/second-reading-guide/*.json` | **是** |

### 关键约束

- **不要**把 `book.epub` 放进 `public/`、`web/public/`、或 `web/dist/`。
- **不要**把 EPUB 解包后的完整 XHTML 正文放进 `public/`。
- **不要**把 EPUB 解包后转成的完整 Markdown 全文放进 `public/`。
- 任何**完整长段原文**都不可公开；只能保留短摘 + 章节/页码证据。
- `.gitignore` 已配置 `projects/*/private/`，EPUB 不会进 git 仓库，但即使如此**也不要**误放进 public。

---

## 3. EPUB 导入前检查

按以下顺序对 `projects/second-reading-guide/private/source/book.epub` 做最小可行性预检：

| # | 检查项 | 期望 | 失败时如何处理 |
|---|---|---|---|
| 1 | 文件存在 | 存在 | 中止，提示放入 EPUB |
| 2 | 文件大小 | 100 KB – 50 MB | <100 KB 提示内容过少；>50 MB 提示过大 |
| 3 | 是否为合法 zip | 是 | 提示 EPUB 损坏 |
| 4 | 是否为合法 epub | 是（zip + mimetype=`application/epub+zip`） | 提示非标准 EPUB |
| 5 | `META-INF/container.xml` 是否存在 | 是 | 提示 EPUB 结构损坏 |
| 6 | OPF 文件能否读取 | 是 | 提示 EPUB 结构损坏 |
| 7 | 书名（dc:title）能否读取 | 是 | 提示元数据缺失 |
| 8 | 作者（dc:creator）能否读取 | 是 | 提示元数据缺失 |
| 9 | 语言（dc:language）能否读取 | 是 | 提示元数据缺失 |
| 10 | 出版信息（dc:publisher / dc:date）能否读取 | 可选 | 缺失仅 warning |
| 11 | toc / nav 能否读取 | 是 | 提示结构损坏，章节抽取会退化 |
| 12 | 章节正文能否提取 | 是 | 提示可能是图片型 EPUB |
| 13 | 疑似 DRM / 加密 | 否 | 中止，提示需提供未加密版本 |
| 14 | 主要是图片型 EPUB | 否 | 标记 `needs_manual_review` 并暂停后续步骤 |

任何**结构性失败**（3/4/5/6/11/12/13）都应**中止导入**，先在 `book_identity_report.md` 里记录失败原因。

---

## 4. EPUB 解析流程

预期命令（**脚本未实现，仅作为占位**）：

```bash
python scripts/extract_epub.py --project projects/second-reading-guide
```

预期行为：

1. 校验 `private/source/book.epub` 存在。
2. 解压到 `working/unpacked/<timestamp>/`（不进入 public）。
3. 解析 `META-INF/container.xml` → 定位 OPF。
4. 解析 OPF → manifest / spine / metadata（dc:title, dc:creator, dc:language, dc:publisher, dc:date）。
5. 解析 toc / nav → 章节层级。
6. 抽取每个章节的纯文本 → 写入 `working/book_text/<chapter_id>.txt`。
7. 输出 `working/parse_summary.json`（结构、字数、章节数、是否含图、是否疑似 DRM）。
8. **不**触碰 `public/` 任何文件。

失败模式：见 §3 表。

---

## 5. 电子书识别流程

预期命令：

```bash
python scripts/identify_book.py \
  --project projects/second-reading-guide \
  --output projects/second-reading-guide/reports/book_identity_report.md
```

预期行为：

1. 读取 `working/parse_summary.json` 与 `working/book_text/`。
2. 推断：书名 / 作者 / 语言 / 来源类型 / 章节数 / 估算字数。
3. 写入 `book_identity_report.md`，含：
   - 元数据（书名、作者、语言、出版信息）
   - 章节结构（按 toc 列出章节列表）
   - 字数 / 段落数 / 脚注计数
   - 风险提示（DRM 嫌疑、图片型、章节数异常）
   - 下一步建议（可继续生成 reading-guide 草稿 / 需人工介入）

---

## 6. EPUB 不需要 OCR 的默认原则

- EPUB 通常包含**结构化 XHTML 文本**，因此**默认不做 OCR**。
- 当前流水线（`extract_epub.py` + `identify_book.py`）只做 EPUB 文本解析和结构化，不调用任何 OCR 引擎。
- **例外**：如果正文主要是图片或不可提取文本（EPUB 实际是图片扫描），会在 `book_identity_report.md` 标记 `needs_manual_review=true`，并把该项目标为 **OCR-required**。此时**不**进入 reading-guide 公开数据生成。

---

## 7. reading-guide 后续公开数据目标

| 公开数据文件 | 描述 | 字段要点 |
|---|---|---|
| `book_overview.json` | 全书导读 | 书名、作者、主题、章节数、阅读时长、关键背景 |
| `chapter_reading_cards.json` | 章节导读 | 每章：标题、导读、关键论点、evidence_refs |
| `key_concepts.json` | 核心概念 | 名词、解释、出现章节、相关引文 |
| `quote_index.json` | 引文索引 | 短摘、章节/页码、用途 |
| `reading_questions.json` | 阅读问题 | 提问、对应章节、参考答案方向 |

每个公开 JSON 都会同时**镜像**到 `web/public/projects/second-reading-guide/<name>.json`，供 web app 加载。

---

## 8. 公开边界

**不公开**：

- 原始 EPUB 文件本身
- EPUB 解包后的完整 XHTML 正文
- 完整 Markdown 全文
- 任何超过 120 字符的长段原文
- 完整脚注 / 尾注全文
- 原始 OCR 文本（如有）

**公开**：

- 结构化导读（书/章节/概念/引文/问题）
- 短摘（默认 ≤120 字符，由 `quote_index` 校验约束）
- 页码 / 章节证据（`evidence_refs` 形式）
- 原创解读、人工撰写的元数据

---

## 9. 人工复核要求

下表列出 v0.6-D1 之后需要人工复核的字段：

| 字段 | 来源 | 复核要点 |
|---|---|---|
| 章节标题 | nav / OPF / XHTML h1/h2 | 标题是否准确；与书中目录是否一致 |
| EPUB 目录层级 | nav.xhtml / ncx | 层级深度（≤3 层）、顺序、是否遗漏 |
| 章节顺序 | spine + nav | 顺序是否符合原书（部分 EPUB 会把前言/序放在最后） |
| 引文短摘 | `quote_index.json` | ≤120 字符；不与版权敏感的整段重合；page/anchor 准确 |
| 概念解释 | `key_concepts.json` | 解释是否自洽；不引入未在原书出现的论点 |
| 阅读问题 | `reading_questions.json` | 问题是否真的能由原书回答；不强行拔高 |
| 脚注 / 尾注 | EPUB xhtml | 是否需要把重要脚注纳入 quote_index（默认否） |

---

## 状态

- 现状：**未导入 EPUB**，仅本清单存在。
- 下一份报告待办：`book_identity_report.md`（在 EPUB 解析成功且 identify_book 跑通后生成）。
- 当前 commit 范围：**不 commit**，本清单与命令模板仅在本地工作区存在。
