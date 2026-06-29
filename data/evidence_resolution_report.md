# 证据警告清理报告

本报告基于 `unsupported_claims.csv` 清理证据不足字段，并把章节/路线标题引用移入 `chapter_refs`。处理过程不使用坐标或现代地图反推路线。

## 汇总

- unsupported claims 总数: 18
- 找到补充证据并保留/改写字段: 16
- 改为 null 或“书中未明示”: 1
- 移动到 review_notes: 2
- 标题移出后追加清理项: 5
- 移入 chapter_refs 的标题引用: 15
- 只有 chapter_refs、缺少事实 book_refs 的段落: 无

## 原始 18 条分段修改

### seg-001 `resupply`

- action: supported_with_new_book_ref
- before: 第45页提到村民提示餐馆并在餐馆吃拉面。
- after: 村民提示附近有餐馆，作者找到餐馆后吃了一碗拉面。
- added_refs: p45 找到村民所说的餐馆，点了一碗拉面
- moved_to_review_notes: no
- quote_validation: p45:found
- notes: 无

### seg-002 `risks_or_notes`

- action: supported_with_new_book_ref
- before: 暑热、背包变重、路上犬只绕行。
- after: 背包明显变重；晴空湛蓝，又一个高亢的暑天；遇狗阻路后绕道。
- added_refs: p56 背包明显变重了。晴空湛蓝，又一个高亢的暑天 | p58 既然它不让我走，我只好绕道了
- moved_to_review_notes: no
- quote_validation: p56:found | p58:found
- notes: 无

### seg-003 `lodging`

- action: cleared_to_unspecified
- before: 无本段步行住宿；作者坐车返回居庸关/中关村休整。
- after: 书中未明示
- added_refs: 无
- moved_to_review_notes: yes
- quote_validation: 无新增引文
- notes: 未找到能直接支持“无本段步行住宿”的正面证据；保留为复核说明。

### seg-006 `roads_or_paths`

- action: supported_with_new_book_ref
- before: 修路路段、老路、人行道、国道京环线/G112。
- after: 修路路段、老路、人行道、国道京环线（G112）。
- added_refs: p151 我们尽量走路边的老路或人行道 | p161 汇入国道京环线（G112）
- moved_to_review_notes: no
- quote_validation: p151:found | p161:found
- notes: 无

### seg-006 `risks_or_notes`

- action: supported_with_new_book_ref
- before: 修路扬尘、烈日、疲劳、水泡。
- after: 修路尘土飞扬、烈日、疲劳；王抒脚上打了水泡。
- added_refs: p154 大卡车奔忙来去，拖曳着尘土飞扬的长龙 | p155 他的脚第一天就打了水泡 | p160 顶着烈日再走一个小时
- moved_to_review_notes: no
- quote_validation: p154:found | p155:found | p160:found
- notes: 无

### seg-007 `route_summary`

- action: supported_with_new_book_ref
- before: 从龙门所沿 G112 先北上越过白河与黑河分水岭，再下到黑河河谷，经塘子庙、东万口乡，下午到白草镇。
- after: 从龙门所沿 G112 北上，到小东沟林场一带越过白河与黑河分水岭，下山后折向东，经东万口乡，下午到白草镇；书中另写到塘子庙温泉和住宿安排。
- added_refs: p174 塘子庙就是明代地图上的“滚水塘”，以温泉得名
- moved_to_review_notes: no
- quote_validation: p174:found
- notes: 无

### seg-007 `lodging`

- action: supported_with_new_book_ref
- before: 塘子庙温泉宾馆一带。
- after: 塘子庙一带的“温泉宾馆”。
- added_refs: p174 我们住的这家“温泉宾馆”开业不久
- moved_to_review_notes: no
- quote_validation: p174:found
- notes: 无

### seg-008 `route_summary`

- action: supported_with_new_book_ref
- before: 从白草镇出发，沿黑河东岸 X404 北上，经过三道川、黑龙山、山神庙等地，进入老掌沟河谷森林地带；因路程和同行人返程安排，后段由度假村车接走。
- after: 从白草镇出发，沿黑河东岸 X404 北上，经过三道川、黑龙山、山神庙等地，进入老掌沟；从沟口往沟里走半小时后，请度假村老板开车来接。
- added_refs: p207 请他开车来接我们。他爽快地答应了
- moved_to_review_notes: no
- quote_validation: p207:found
- notes: 无

### seg-008 `risks_or_notes`

- action: supported_with_new_book_ref
- before: 长距离近四十公里计划、天气突变、越野车、后段非连续步行。
- after: 离老掌沟还有约二十公里，书中判断很难完成；山区可能突降暴雨，路上有越野车队；后段联系度假村车辆接应。
- added_refs: p205 离目的地老掌沟还有差不多二十公里，看来很难完成了 | p205 山区有自己的小气候，也许会突然来一场暴雨 | p205 一路上已见到好几拨越野车队
- moved_to_review_notes: no
- quote_validation: p205:found | p205:found | p205:found
- notes: 无

### seg-009 `risks_or_notes`

- action: supported_with_new_book_ref
- before: 反复过河、深车辙、细沙、绕行导致距离增加。
- after: 沟谷中需反复过河；细沙和深车辙使行走困难；五公里沟谷实际走了差不多十公里。
- added_refs: p220 无论怎么走都得反复过河 | p220 满谷都是细沙，被越野车纵横碾压之后，车辙深陷
- moved_to_review_notes: no
- quote_validation: p220:found | p220:found | p220:found
- notes: 无

### seg-010 `resupply`

- action: supported_with_new_book_ref
- before: 小厂镇早餐和小卖部买水；途中小店泡面、啤酒。
- after: 石柱村商店提供方便面，作者先喝两瓶啤酒。
- added_refs: p245 我给你们泡碗方便面吧 | p245 从冰箱里拿出两瓶啤酒，让我们先喝着
- moved_to_review_notes: no
- quote_validation: p245:found | p245:found
- notes: 无

### seg-011 `risks_or_notes`

- action: supported_with_new_book_ref
- before: 本段包含车辆回到补走起点，需避免误画乘车路线。
- after: 本段先乘出租车到梳妆楼，再送到五花草甸；随后从五花草甸一带补走到沽源。
- added_refs: p273 上午九点五十分，出租车把我们送到五花草甸
- moved_to_review_notes: no
- quote_validation: p265:found | p273:found
- notes: 无

### seg-012 `risks_or_notes`

- action: supported_with_new_book_ref
- before: 酷热、强日晒、长距离无行道树。
- after: 高原的暴晒和暑热开始发威；作者越来越畏惧阳光；到方元酒店时两脚打了水泡。
- added_refs: p285 高原的暴晒和暑热开始发威 | p286 我越来越畏惧阳光 | p300 两脚的脚跟和外侧都打了水泡
- moved_to_review_notes: no
- quote_validation: p285:found | p286:found | p300:found
- notes: 无

### seg-013 `route_summary`

- action: rewritten_without_unsupported_part
- before: 从塞北管理区沿县道 402 北行，跨过河北/内蒙古边界后沿滦河东岸继续，经过明安驿、李陵台遗址，到黑城子镇一带。
- after: 从塞北管理区沿县道402往北，跨过河北与内蒙古分界后进入正蓝旗，沿X502继续北行，经黑土城镇前往李陵台遗址；之后到黑城子镇一带。
- added_refs: p305 由此往北再走三公里，十一点三十分，我们到达河北与内蒙的分界点 | p313 下午两点半，我们走到黑土城镇的南侧
- moved_to_review_notes: yes
- quote_validation: p305:found | p313:found
- notes: 原 summary 中“经过明安驿”与本段 book_refs 无法对应；已移入复核备注。

### seg-014 `resupply`

- action: supported_with_new_book_ref
- before: 途中蒙古包/牧户处休息、自带午饭和热水。
- after: 途中在蒙古包休息；对方提供热水，作者一行吃自带的馒头和面包。
- added_refs: p328 于是我们进到院内的一个蒙古包里 | p328 我们自己带着午饭，所以就不麻烦他们了，就着水吃起自带的馒头和面包
- moved_to_review_notes: no
- quote_validation: p328:found | p328:found
- notes: 无

### seg-015 `resupply`

- action: supported_with_new_book_ref
- before: 电视台记者送冰冻矿泉水和西瓜。
- after: 电视台记者送来冰冻矿泉水和西瓜。
- added_refs: p348 冰冻的矿泉水和西瓜从未如此充满吸引力
- moved_to_review_notes: no
- quote_validation: p348:found
- notes: 无

### seg-015 `lodging`

- action: supported_with_new_book_ref
- before: 书中未明示；前一晚住正蓝旗上都镇。
- after: 前一晚住正蓝旗上都镇的上都酒店。
- added_refs: p318 直奔网上推荐的上都酒店，办好入住手续
- moved_to_review_notes: no
- quote_validation: p318:found
- notes: 无

### seg-015 `risks_or_notes`

- action: supported_with_new_book_ref
- before: 极端暑热、脚底疼痛、无树荫。
- after: 最后一天天气极热；脚趾和脚后跟多处水泡，脚底疼痛；路上没有树，也没有其他可以遮阴的地方。
- added_refs: p344 今天会是几年来最热的一天 | p345 发现脚趾头和脚后跟打了好几个水泡 | p346 事实上也没有地方适合休息，没有树，也没有其他可以遮阴的地方
- moved_to_review_notes: no
- quote_validation: p344:found | p345:found | p346:found
- notes: 无

## 标题移出后的追加清理

### seg-004

- action: post_cleanup_after_chapter_ref_split
- fields: lodging, route_summary
- added_refs: p102 吃完早饭，我们告别延庆，坐出租车前往旧县镇，从那里开始走去白河堡水库 | p111 盘云岭山口是由地质学上所说的盘云岭断层形成的 | p115 找到水库库区管理所的燕山天池宾馆 | p104 quote updated | p114 quote updated
- quote_validation: p102:found | p111:found | p115:found
- notes: 无

### seg-005

- action: post_cleanup_after_chapter_ref_split
- fields: route_summary, walking_directions, water_sources
- added_refs: p125 公路紧贴在白河河谷的北岸 | p126 上午十点，到达骆驼山村
- quote_validation: p125:found | p126:found | p127:quote not found in OCR page
- notes: 证据不足，待人工复核：seg-005 原 route_summary / walking_directions 中的“郑家窑、镇虏楼”未在正文事实页形成足够支撑，本轮仅从摘要和方向中移除，地点候选仍需回看 PDF。

### seg-009

- action: post_cleanup_after_chapter_ref_split
- fields: route_summary, terrain, walking_directions
- added_refs: p218 首先要补上昨天没有走完的一段 | p221 从沟门往北走十多分钟，就到了燕山山脉北支的分水岭 | p222 沙岭至小厂镇地势下降明显 | p224 X404的路东先后是前坝村和后坝村 | p228 下午四点一刻，我们走到X404与S245交叉的地方，终于到小厂镇了
- quote_validation: p218:found | p221:found | p222:found | p224:found | p228:found
- notes: 无

### seg-012

- action: post_cleanup_after_chapter_ref_split
- fields: route_summary, walking_directions
- added_refs: p291 从水泉淖尔向东，一路上山，到转佛庙村南口所建的旅游点 | p298 沿着024县道东北行，一路下山，半小时后走到紧傍滦河的马神庙村 | p299 从马神庙村向北的公路，是县级公路X402从前的老路
- quote_validation: p291:found | p298:found | p299:found
- notes: 无

### seg-014

- action: post_cleanup_after_chapter_ref_split
- fields: book_refs
- added_refs: p332 quote updated
- quote_validation: 无新增引文
- notes: 无

## chapter_refs 移动

- seg-001: 1 条标题/章节引用移入 chapter_refs
- seg-002: 1 条标题/章节引用移入 chapter_refs
- seg-003: 1 条标题/章节引用移入 chapter_refs
- seg-004: 1 条标题/章节引用移入 chapter_refs
- seg-005: 1 条标题/章节引用移入 chapter_refs
- seg-006: 1 条标题/章节引用移入 chapter_refs
- seg-007: 1 条标题/章节引用移入 chapter_refs
- seg-008: 1 条标题/章节引用移入 chapter_refs
- seg-009: 1 条标题/章节引用移入 chapter_refs
- seg-010: 1 条标题/章节引用移入 chapter_refs
- seg-011: 1 条标题/章节引用移入 chapter_refs
- seg-012: 1 条标题/章节引用移入 chapter_refs
- seg-013: 1 条标题/章节引用移入 chapter_refs
- seg-014: 1 条标题/章节引用移入 chapter_refs
- seg-015: 1 条标题/章节引用移入 chapter_refs
