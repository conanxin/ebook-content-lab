# Manual Review Full Packet v0.7-A7

- Project: `second-reading-guide`
- Total tasks: `95`
- Grouped by priority and category.
- This packet includes structural public metadata only.

## P0 / book_overview

- task count: `1`

### p0-book-overview-001

- priority: `P0`
- category: `book_overview`
- target_id: `book_overview`
- target_title: `Book overview`
- source_file: `projects/second-reading-guide/public/book_overview.json`
- current manual_result: `blank`
- review question: Confirm the overview accurately describes the draft as structural and conservative.

Structured context:

- schema_version: `reading-guide.v0.2`
- status: `draft`
- body_letter_count: `25`
- source_mode: `metadata_and_letters_brief`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P0 / chapter_card_sample

- task count: `5`

### p0-chapter-sample-001

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-001`
- target_title: `第1封 3月17日~18日 娘子关→骊山→西安`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-006`
- order: `1`
- places: `娘子关, 骊山, 西安`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `2`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p0-chapter-sample-007

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-007`
- target_title: `第7封 4月2日~3日 贵阳流山→桂林伏波山/七星山/象鼻山/漓江`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-012`
- order: `7`
- places: `贵阳流山, 桂林伏波山, 七星山, 象鼻山, 漓江`
- themes: `旅行书信, 山水行旅`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p0-chapter-sample-013

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-013`
- target_title: `第13封 4月13日~14日 汕头看海`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-018`
- order: `13`
- places: `汕头看海`
- themes: `旅行书信`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p0-chapter-sample-019

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-019`
- target_title: `第19封 4月28日~5月2日 千古如斯的余杭`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-024`
- order: `19`
- places: `千古如斯的余杭`
- themes: `旅行书信, 长篇行旅记录, 多段叙述`
- chunk_count: `5`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p0-chapter-sample-025

- priority: `P0`
- category: `chapter_card_sample`
- target_id: `chapter-025`
- target_title: `第25封 5月18日~23日 沪青海航→青岛崂山→返京`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Spot-check that this chapter card is derived only from structural metadata.

Structured context:

- section_id: `sec-030`
- order: `25`
- places: `沪青海航, 青岛崂山, 返京`
- themes: `旅行书信, 长篇行旅记录, 多段叙述, 山水行旅, 城市与旅途`
- chunk_count: `6`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P0 / public_boundary

- task count: `1`

### p0-public-boundary-001

- priority: `P0`
- category: `public_boundary`
- target_id: `public-layer`
- target_title: `Public reading-guide files`
- source_file: `projects/second-reading-guide/public/*.json`
- current manual_result: `blank`
- review question: Confirm public files contain no private paths, no source text, and no long excerpts.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P0 / quote_policy

- task count: `1`

### p0-quote-policy-001

- priority: `P0`
- category: `quote_policy`
- target_id: `quote_index`
- target_title: `Quote index policy`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm quote entries use structural_no_quote and do not publish source quotations.

Structured context:

- quote_mode: `structural_no_quote`
- entries: `25`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P0 / schema_status

- task count: `1`

### p0-schema-status-001

- priority: `P0`
- category: `schema_status`
- target_id: `reading-guide.v0.2`
- target_title: `Schema and status`
- source_file: `projects/second-reading-guide/public/*.json`
- current manual_result: `blank`
- review question: Confirm schema_version is reading-guide.v0.2 and status remains draft.

Structured context:

- schemas: `reading-guide.v0.2`
- statuses: `draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P0 / web_mirror

- task count: `1`

### p0-web-mirror-001

- priority: `P0`
- category: `web_mirror`
- target_id: `web-public-mirror`
- target_title: `Web public mirror`
- source_file: `web/public/projects/second-reading-guide/*.json`
- current manual_result: `blank`
- review question: Confirm web mirror JSON files match project public JSON files.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P1 / chapter_card

- task count: `25`

### p1-chapter-card-001

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-001`
- target_title: `第1封 3月17日~18日 娘子关→骊山→西安`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-006`
- order: `1`
- places: `娘子关, 骊山, 西安`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `2`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-002

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-002`
- target_title: `第2封 3月19日~20日 半坡/碑林→成都`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-007`
- order: `2`
- places: `半坡, 碑林, 成都`
- themes: `旅行书信, 城市与旅途`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-003

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-003`
- target_title: `第3封 3月21日~23日 杜甫草堂/武侯祠→青城山`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-008`
- order: `3`
- places: `杜甫草堂, 武侯祠, 青城山`
- themes: `旅行书信, 山水行旅`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-004

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-004`
- target_title: `第4封 3月24日~26日 乐山大佛/青衣亭→峨嵋山脚`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-009`
- order: `4`
- places: `乐山大佛, 青衣亭, 峨嵋山脚`
- themes: `旅行书信, 长篇行旅记录, 多段叙述, 山水行旅`
- chunk_count: `6`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-005

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-005`
- target_title: `第5封 3月26日~29日 峨嵋车站→成昆线隧道→昆明车站`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-010`
- order: `5`
- places: `峨嵋车站, 成昆线隧道, 昆明车站`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-006

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-006`
- target_title: `第6封 3月31日~4月1日 昆明温泉/西山/石林→贵阳花溪`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-011`
- order: `6`
- places: `昆明温泉, 西山, 石林, 贵阳花溪`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-007

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-007`
- target_title: `第7封 4月2日~3日 贵阳流山→桂林伏波山/七星山/象鼻山/漓江`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-012`
- order: `7`
- places: `贵阳流山, 桂林伏波山, 七星山, 象鼻山, 漓江`
- themes: `旅行书信, 山水行旅`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-008

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-008`
- target_title: `第8封 4月3日~5日 桂林南溪山月岸/叠彩峰/隐山→阳朔`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-013`
- order: `8`
- places: `桂林南溪山, 叠彩峰, 隐山, 阳朔`
- themes: `旅行书信, 山水行旅`
- chunk_count: `2`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-009

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-009`
- target_title: `第9封 4月5日~7日 漓江→阳朔→梧州`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-014`
- order: `9`
- places: `漓江, 阳朔, 梧州`
- themes: `旅行书信`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-010

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-010`
- target_title: `第10封 4月7日~8日 梧州西江种种`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-015`
- order: `10`
- places: `梧州西江种种`
- themes: `旅行书信`
- chunk_count: `2`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-011

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-011`
- target_title: `第11封 4月8日~9日 肇庆天柱阁`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-016`
- order: `11`
- places: `肇庆天柱阁`
- themes: `旅行书信`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-012

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-012`
- target_title: `第12封 4月9日~11日 广州中山大学/白云山`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-017`
- order: `12`
- places: `广州中山大学, 白云山`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `2`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-013

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-013`
- target_title: `第13封 4月13日~14日 汕头看海`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-018`
- order: `13`
- places: `汕头看海`
- themes: `旅行书信`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-014

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-014`
- target_title: `第14封 4月15日~16日 云霄→漳浦→漳州→厦门→福州→鼓浪屿`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-019`
- order: `14`
- places: `云霄, 漳浦, 漳州, 厦门, 福州, 鼓浪屿`
- themes: `旅行书信, 城市与旅途`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-015

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-015`
- target_title: `第15封 4月17日~19日 泉州→福州西湖/戚公祠/乌龙江大桥/涌泉寺`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-020`
- order: `15`
- places: `泉州, 福州西湖, 戚公祠, 乌龙江大桥, 涌泉寺`
- themes: `旅行书信, 城市与旅途`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-016

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-016`
- target_title: `第16封 4月20日~22日 福安交溪→福鼎灵溪→南雁荡/会文书院→北雁荡`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-021`
- order: `16`
- places: `福安交溪, 福鼎灵溪, 南雁荡, 会文书院, 北雁荡`
- themes: `旅行书信, 山水行旅`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-017

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-017`
- target_title: `第17封 4月23日~25日 温州北雁荡由浅入深`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-022`
- order: `17`
- places: `温州北雁荡由浅入深`
- themes: `旅行书信, 长篇行旅记录, 多段叙述, 山水行旅`
- chunk_count: `7`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-018

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-018`
- target_title: `第18封 4月28日 朝辞雁荡暮至余杭`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-023`
- order: `18`
- places: `朝辞雁荡暮至余杭`
- themes: `旅行书信, 山水行旅`
- chunk_count: `2`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-019

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-019`
- target_title: `第19封 4月28日~5月2日 千古如斯的余杭`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-024`
- order: `19`
- places: `千古如斯的余杭`
- themes: `旅行书信, 长篇行旅记录, 多段叙述`
- chunk_count: `5`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-020

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-020`
- target_title: `第20封 5月4日~5日 黄山天都峰排云亭`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-025`
- order: `20`
- places: `黄山天都峰排云亭`
- themes: `旅行书信, 山水行旅`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-021

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-021`
- target_title: `第21封 5月6日~8日 青阳九华山/安庆小孤山`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-026`
- order: `21`
- places: `青阳九华山, 安庆小孤山`
- themes: `旅行书信, 长篇行旅记录, 多段叙述, 山水行旅`
- chunk_count: `5`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-022

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-022`
- target_title: `第22封 5月8日~11日 鄱阳五老峰/三叠瀑`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-027`
- order: `22`
- places: `鄱阳五老峰, 三叠瀑`
- themes: `旅行书信, 长篇行旅记录, 多段叙述, 山水行旅`
- chunk_count: `6`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-023

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-023`
- target_title: `第23封 5月11日~14日 南京中山陵/玄武湖→苏州园林`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-028`
- order: `23`
- places: `南京中山陵, 玄武湖, 苏州园林`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `3`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-024

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-024`
- target_title: `第24封 5月15日~17日 苏州天平山沧浪亭→上海`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-029`
- order: `24`
- places: `苏州天平山沧浪亭, 上海`
- themes: `旅行书信, 山水行旅, 城市与旅途`
- chunk_count: `4`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-chapter-card-025

- priority: `P1`
- category: `chapter_card`
- target_id: `chapter-025`
- target_title: `第25封 5月18日~23日 沪青海航→青岛崂山→返京`
- source_file: `projects/second-reading-guide/public/chapter_reading_cards.json`
- current manual_result: `blank`
- review question: Review title, places, themes, counts, and structural evidence reference.

Structured context:

- section_id: `sec-030`
- order: `25`
- places: `沪青海航, 青岛崂山, 返京`
- themes: `旅行书信, 长篇行旅记录, 多段叙述, 山水行旅, 城市与旅途`
- chunk_count: `6`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P1 / key_concept

- task count: `5`

### p1-key-concept-001

- priority: `P1`
- category: `key_concept`
- target_id: `concept-001`
- target_title: `旅行书信`
- source_file: `projects/second-reading-guide/public/key_concepts.json`
- current manual_result: `blank`
- review question: Review whether this concept grouping is reasonable as a structural draft.

Structured context:

- label: `旅行书信`
- related_letters: `25`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-key-concept-002

- priority: `P1`
- category: `key_concept`
- target_id: `concept-002`
- target_title: `山水行旅`
- source_file: `projects/second-reading-guide/public/key_concepts.json`
- current manual_result: `blank`
- review question: Review whether this concept grouping is reasonable as a structural draft.

Structured context:

- label: `山水行旅`
- related_letters: `17`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-key-concept-003

- priority: `P1`
- category: `key_concept`
- target_id: `concept-003`
- target_title: `城市与旅途`
- source_file: `projects/second-reading-guide/public/key_concepts.json`
- current manual_result: `blank`
- review question: Review whether this concept grouping is reasonable as a structural draft.

Structured context:

- label: `城市与旅途`
- related_letters: `10`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-key-concept-004

- priority: `P1`
- category: `key_concept`
- target_id: `concept-004`
- target_title: `多段叙述`
- source_file: `projects/second-reading-guide/public/key_concepts.json`
- current manual_result: `blank`
- review question: Review whether this concept grouping is reasonable as a structural draft.

Structured context:

- label: `多段叙述`
- related_letters: `6`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-key-concept-005

- priority: `P1`
- category: `key_concept`
- target_id: `concept-005`
- target_title: `长篇行旅记录`
- source_file: `projects/second-reading-guide/public/key_concepts.json`
- current manual_result: `blank`
- review question: Review whether this concept grouping is reasonable as a structural draft.

Structured context:

- label: `长篇行旅记录`
- related_letters: `6`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P1 / quote_structural_entry

- task count: `25`

### p1-quote-structural-001

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-001`
- target_title: `sec-006`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-006`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-002

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-002`
- target_title: `sec-007`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-007`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-003

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-003`
- target_title: `sec-008`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-008`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-004

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-004`
- target_title: `sec-009`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-009`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-005

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-005`
- target_title: `sec-010`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-010`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-006

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-006`
- target_title: `sec-011`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-011`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-007

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-007`
- target_title: `sec-012`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-012`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-008

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-008`
- target_title: `sec-013`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-013`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-009

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-009`
- target_title: `sec-014`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-014`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-010

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-010`
- target_title: `sec-015`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-015`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-011

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-011`
- target_title: `sec-016`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-016`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-012

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-012`
- target_title: `sec-017`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-017`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-013

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-013`
- target_title: `sec-018`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-018`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-014

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-014`
- target_title: `sec-019`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-019`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-015

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-015`
- target_title: `sec-020`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-020`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-016

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-016`
- target_title: `sec-021`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-021`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-017

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-017`
- target_title: `sec-022`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-022`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-018

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-018`
- target_title: `sec-023`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-023`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-019

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-019`
- target_title: `sec-024`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-024`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-020

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-020`
- target_title: `sec-025`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-025`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-021

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-021`
- target_title: `sec-026`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-026`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-022

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-022`
- target_title: `sec-027`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-027`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-023

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-023`
- target_title: `sec-028`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-028`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-024

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-024`
- target_title: `sec-029`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-029`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-quote-structural-025

- priority: `P1`
- category: `quote_structural_entry`
- target_id: `quote-placeholder-025`
- target_title: `sec-030`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Confirm this quote slot remains structural-only until a human selects an allowed short quote.

Structured context:

- quote_mode: `structural_no_quote`
- section_id: `sec-030`
- quote_is_empty: `true`
- review_status: `awaiting_manual_quote_review`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P1 / reading_question

- task count: `26`

### p1-reading-question-001

- priority: `P1`
- category: `reading_question`
- target_id: `book-question-001`
- target_title: `这 25 封书信如何按照行程顺序展开出一条阅读路线？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `book`
- letter_id: ``
- section_id: ``
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-002

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-001`
- target_title: `阅读“第1封 3月17日~18日 娘子关→骊山→西安”时，可以如何把 娘子关、骊山、西安 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-001`
- section_id: `sec-006`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-003

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-002`
- target_title: `阅读“第2封 3月19日~20日 半坡/碑林→成都”时，可以如何把 半坡、碑林、成都 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-002`
- section_id: `sec-007`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-004

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-003`
- target_title: `阅读“第3封 3月21日~23日 杜甫草堂/武侯祠→青城山”时，可以如何把 杜甫草堂、武侯祠、青城山 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-003`
- section_id: `sec-008`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-005

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-004`
- target_title: `阅读“第4封 3月24日~26日 乐山大佛/青衣亭→峨嵋山脚”时，可以如何把 乐山大佛、青衣亭、峨嵋山脚 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-004`
- section_id: `sec-009`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-006

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-005`
- target_title: `阅读“第5封 3月26日~29日 峨嵋车站→成昆线隧道→昆明车站”时，可以如何把 峨嵋车站、成昆线隧道、昆明车站 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-005`
- section_id: `sec-010`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-007

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-006`
- target_title: `阅读“第6封 3月31日~4月1日 昆明温泉/西山/石林→贵阳花溪”时，可以如何把 昆明温泉、西山、石林 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-006`
- section_id: `sec-011`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-008

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-007`
- target_title: `阅读“第7封 4月2日~3日 贵阳流山→桂林伏波山/七星山/象鼻山/漓江”时，可以如何把 贵阳流山、桂林伏波山、七星山 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-007`
- section_id: `sec-012`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-009

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-008`
- target_title: `阅读“第8封 4月3日~5日 桂林南溪山月岸/叠彩峰/隐山→阳朔”时，可以如何把 桂林南溪山、叠彩峰、隐山 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-008`
- section_id: `sec-013`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-010

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-009`
- target_title: `阅读“第9封 4月5日~7日 漓江→阳朔→梧州”时，可以如何把 漓江、阳朔、梧州 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-009`
- section_id: `sec-014`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-011

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-010`
- target_title: `阅读“第10封 4月7日~8日 梧州西江种种”时，可以如何把 梧州西江种种 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-010`
- section_id: `sec-015`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-012

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-011`
- target_title: `阅读“第11封 4月8日~9日 肇庆天柱阁”时，可以如何把 肇庆天柱阁 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-011`
- section_id: `sec-016`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-013

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-012`
- target_title: `阅读“第12封 4月9日~11日 广州中山大学/白云山”时，可以如何把 广州中山大学、白云山 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-012`
- section_id: `sec-017`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-014

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-013`
- target_title: `阅读“第13封 4月13日~14日 汕头看海”时，可以如何把 汕头看海 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-013`
- section_id: `sec-018`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-015

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-014`
- target_title: `阅读“第14封 4月15日~16日 云霄→漳浦→漳州→厦门→福州→鼓浪屿”时，可以如何把 云霄、漳浦、漳州 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-014`
- section_id: `sec-019`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-016

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-015`
- target_title: `阅读“第15封 4月17日~19日 泉州→福州西湖/戚公祠/乌龙江大桥/涌泉寺”时，可以如何把 泉州、福州西湖、戚公祠 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-015`
- section_id: `sec-020`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-017

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-016`
- target_title: `阅读“第16封 4月20日~22日 福安交溪→福鼎灵溪→南雁荡/会文书院→北雁荡”时，可以如何把 福安交溪、福鼎灵溪、南雁荡 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-016`
- section_id: `sec-021`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-018

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-017`
- target_title: `阅读“第17封 4月23日~25日 温州北雁荡由浅入深”时，可以如何把 温州北雁荡由浅入深 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-017`
- section_id: `sec-022`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-019

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-018`
- target_title: `阅读“第18封 4月28日 朝辞雁荡暮至余杭”时，可以如何把 朝辞雁荡暮至余杭 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-018`
- section_id: `sec-023`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-020

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-019`
- target_title: `阅读“第19封 4月28日~5月2日 千古如斯的余杭”时，可以如何把 千古如斯的余杭 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-019`
- section_id: `sec-024`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-021

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-020`
- target_title: `阅读“第20封 5月4日~5日 黄山天都峰排云亭”时，可以如何把 黄山天都峰排云亭 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-020`
- section_id: `sec-025`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-022

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-021`
- target_title: `阅读“第21封 5月6日~8日 青阳九华山/安庆小孤山”时，可以如何把 青阳九华山、安庆小孤山 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-021`
- section_id: `sec-026`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-023

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-022`
- target_title: `阅读“第22封 5月8日~11日 鄱阳五老峰/三叠瀑”时，可以如何把 鄱阳五老峰、三叠瀑 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-022`
- section_id: `sec-027`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-024

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-023`
- target_title: `阅读“第23封 5月11日~14日 南京中山陵/玄武湖→苏州园林”时，可以如何把 南京中山陵、玄武湖、苏州园林 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-023`
- section_id: `sec-028`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-025

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-024`
- target_title: `阅读“第24封 5月15日~17日 苏州天平山沧浪亭→上海”时，可以如何把 苏州天平山沧浪亭、上海 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-024`
- section_id: `sec-029`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

### p1-reading-question-026

- priority: `P1`
- category: `reading_question`
- target_id: `letter-question-025`
- target_title: `阅读“第25封 5月18日~23日 沪青海航→青岛崂山→返京”时，可以如何把 沪青海航、青岛崂山、返京 与本封书信的行旅结构联系起来？`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Review whether this reading question is useful and appropriately conservative.

Structured context:

- scope: `letter`
- letter_id: `letter-025`
- section_id: `sec-030`
- review_status: `auto_structural_draft`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P2 / concept_grouping_refinement

- task count: `1`

### p2-concept-grouping-001

- priority: `P2`
- category: `concept_grouping_refinement`
- target_id: `key_concepts`
- target_title: `Concept grouping refinement`
- source_file: `projects/second-reading-guide/public/key_concepts.json`
- current manual_result: `blank`
- review question: Consider whether concept labels should be merged, split, or renamed after manual reading.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P2 / future_quote_replacement

- task count: `1`

### p2-future-quote-review-001

- priority: `P2`
- category: `future_quote_replacement`
- target_id: `quote_index`
- target_title: `Future quote review`
- source_file: `projects/second-reading-guide/public/quote_index.json`
- current manual_result: `blank`
- review question: Prepare a later process for manually selected short quotations without publishing long excerpts.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P2 / question_quality_enhancement

- task count: `1`

### p2-question-quality-001

- priority: `P2`
- category: `question_quality_enhancement`
- target_id: `reading_questions`
- target_title: `Question quality enhancement`
- source_file: `projects/second-reading-guide/public/reading_questions.json`
- current manual_result: `blank`
- review question: Refine generic structural questions after close reading and manual review.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.

## P2 / wording_polish

- task count: `1`

### p2-wording-polish-001

- priority: `P2`
- category: `wording_polish`
- target_id: `public-reading-guide`
- target_title: `Public wording`
- source_file: `projects/second-reading-guide/public/*.json`
- current manual_result: `blank`
- review question: Improve wording only after P0/P1 evidence checks are complete.

Structured context:

- structural context: `see source_file`

Human decision needed:

- Decide whether this task can be marked `pass`, `needs_fix`, `blocked`, or `deferred`.
- Add notes for every non-pass result.
