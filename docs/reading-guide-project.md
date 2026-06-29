# Reading Guide Project

`reading-guide` 是 `ebook-content-lab` 中面向普通读者的电子书导读型子项目。它适合章节结构清晰、需要帮助读者理解主题、概念、引文和讨论问题的书。

## 适合的书

- 章节或篇目结构明确的非虚构作品。
- 需要提炼主题、术语、人物、地点或关键论点的书。
- 适合做读书会、课程阅读、个人精读笔记的书。
- 不适合只靠少量摘录就能说明的项目；所有判断都应保留页码证据。

## 公开数据结构

`reading-guide` 的公开数据放在：

```text
projects/<slug>/public/
web/public/projects/<slug>/
```

标准文件：

- `book_overview.json`：全书导读、阅读目的、结构概览、使用说明和限制。
- `chapter_reading_cards.json`：按章节整理的导读卡片。
- `key_concepts.json`：核心概念、术语、主题或人物关系。
- `quote_index.json`：短引文索引，每条引文必须控制长度。
- `reading_questions.json`：理解题、讨论题、研究题或反思题。

通用证据字段 `evidence_refs`：

```json
{
  "page": 1,
  "quote": "不超过 120 字的短摘",
  "note": "说明这条短摘支持什么判断",
  "source_file": null
}
```

## 从 PDF/OCR 到导读数据

1. 将电子书源文件放入 `projects/<slug>/private/source/book.pdf`。
2. 运行 OCR，生成可检索 PDF、分页文本和分块文本。
3. 将 OCR 全文和扫描页保留在 `projects/<slug>/private/`。
4. 运行电子书识别，更新 `project.json` 中的书名、作者、语言和内容类型建议。
5. 根据章节结构生成导读草稿。
6. 为每条章节概括、概念解释、引文和阅读问题补充 `evidence_refs`。
7. 运行 `scripts/check_reading_guide_project.py`。
8. 同步公开数据到 `web/public/projects/<slug>/`。
9. 运行 `scripts/check_public_release.py` 和 `npm run build`。

## 章节导读卡片

`chapter_reading_cards.json` 中每条章节卡片建议包含：

- `chapter_id`
- `chapter_title`
- `page_start`
- `page_end`
- `summary`
- `key_points`
- `reading_notes`
- `evidence_refs`
- `review_notes`

章节卡片不应复制长段原文。摘要必须来自 OCR 文本和短证据，不确定内容写入 `review_notes`。

## 核心概念

`key_concepts.json` 可用于整理：

- 反复出现的关键词。
- 章节之间的主题线索。
- 需要读者提前理解的背景概念。
- 需要人工复核的术语或 OCR 疑似错误。

概念解释不能脱离书中证据扩写。需要外部背景时，应另行标记来源，不要混入书中事实。

## 引文索引

`quote_index.json` 只保存短摘，不保存 OCR 全文。

规则：

- 单条 `quote` 不超过 120 字。
- 每条引文必须有页码。
- `note` 说明引文用于支持什么阅读判断。
- 不公开连续长段原文。

## 阅读问题

`reading_questions.json` 可包含：

- `comprehension`：理解题。
- `discussion`：讨论题。
- `research`：延伸研究题。
- `reflection`：反思题。

问题应指向章节或主题，并尽量保留证据引用。不能把尚未核验的推断写成确定结论。

## 私有与公开边界

可以公开：

- 结构化导读 JSON。
- 人工整理的短说明。
- 有页码的短摘证据。
- 不含 OCR 全文的复核说明。

不能公开：

- 原始 PDF。
- OCR PDF。
- OCR 全文。
- 分页 OCR JSONL。
- 扫描页图片。
- 长段原文摘录。

## 校验命令

```powershell
python scripts\check_reading_guide_project.py --project projects\<slug>
python scripts\check_public_release.py
cd web
npm run build
```

draft 状态下，章节、概念、引文和问题列表可以为空。非 draft 状态下，必须至少有章节卡片，并且章节卡片必须带 `evidence_refs`。

## 上线展示

`web` 会从 `/projects/<slug>/project.json` 读取项目类型。如果 `project_type` 是 `reading-guide`，页面显示 reading-guide 草稿页或导读内容页。项目仍处于 draft 时，页面必须明确提示尚未导入电子书。
