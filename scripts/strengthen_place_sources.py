#!/usr/bin/env python3
"""Strengthen public place sources for the reading-guide preview.

This script only updates public, derived reading-guide JSON. It does not read
private source text and does not modify manual-review CSV files.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.lib.project_paths import from_project
except ModuleNotFoundError:
    from lib.project_paths import from_project


PUBLIC_FILES = [
    "book_overview.json",
    "chapter_reading_cards.json",
    "key_concepts.json",
    "quote_index.json",
    "reading_questions.json",
]

A11_PUBLIC_SOURCE_COUNT = 9
UPDATED_IN = "v0.7-A12"


def source(
    source_name: str,
    source_url: str,
    source_type: str,
    now_context: str,
    source_review_note: str,
) -> dict[str, str]:
    return {
        "source_name": source_name,
        "source_url": source_url,
        "source_type": source_type,
        "now_context": now_context,
        "source_review_note": source_review_note,
    }


# The map is intentionally conservative: official, UNESCO, museum/university,
# tourism/government, or encyclopedia pages. Names match public JSON place keys.
A12_PLACE_SOURCES: dict[str, dict[str, str]] = {
    "娘子关": source(
        "Wikipedia - Niangziguan",
        "https://en.wikipedia.org/wiki/Niangziguan",
        "encyclopedia",
        "今日可按历史关隘与太行山交通节点理解；实际游览开放、交通和保护状态仍需临行前核验。",
        "百科页面可作初步地名核对，后续建议补充地方文旅或景区官方来源。",
    ),
    "骊山": source(
        "Wikipedia - Mount Li",
        "https://en.wikipedia.org/wiki/Mount_Li",
        "encyclopedia",
        "今日可按西安近郊山岳与历史文化景观理解；与华清宫、秦岭北麓旅游线路相关。",
        "百科页面可作初步对照，后续建议补充景区或文旅官方来源。",
    ),
    "西安": source(
        "Wikipedia - Xi'an",
        "https://en.wikipedia.org/wiki/Xi%27an",
        "encyclopedia",
        "今日可按陕西省会、古都与综合交通城市节点理解，是多处历史遗址和博物馆的入口城市。",
        "百科页面用于城市节点核对，具体景点需分别查证。",
    ),
    "半坡": source(
        "Xi'an Banpo Museum",
        "http://www.banpomuseum.com/",
        "museum",
        "今日可按新石器时代遗址博物馆理解，适合与书中早期旅行的考古兴趣相互参照。",
        "博物馆官网用于场馆身份核对，开放信息需临行前复核。",
    ),
    "碑林": source(
        "Xi'an Beilin Museum",
        "https://en.wikipedia.org/wiki/Stele_Forest",
        "encyclopedia",
        "今日可按碑刻、石刻和博物馆型历史文化节点理解。",
        "百科页面用于初步定位，后续建议补充博物馆官网。",
    ),
    "成都": source(
        "Wikipedia - Chengdu",
        "https://en.wikipedia.org/wiki/Chengdu",
        "encyclopedia",
        "今日可按四川省会、区域交通枢纽与城市文化节点理解。",
        "百科页面用于城市节点核对，具体景点需分别查证。",
    ),
    "杜甫草堂": source(
        "Du Fu Thatched Cottage Museum",
        "https://en.wikipedia.org/wiki/Du_Fu_Thatched_Cottage",
        "museum",
        "今日可按诗人纪念馆和成都文化景点理解，阅读时可对照作者在城市中的文化访问线索。",
        "百科页面用于初步核对，后续建议补充博物馆官方页面。",
    ),
    "武侯祠": source(
        "Wuhou Shrine",
        "https://en.wikipedia.org/wiki/Wuhou_Shrine",
        "encyclopedia",
        "今日可按三国历史纪念空间和成都重要文化景点理解。",
        "百科页面用于初步核对，后续建议补充景区或博物馆官方来源。",
    ),
    "青城山": source(
        "UNESCO World Heritage Centre - Mount Qingcheng and the Dujiangyan Irrigation System",
        "https://whc.unesco.org/en/list/1001/",
        "unesco",
        "今日可按世界遗产体系中的道教名山与水利文化景观理解。",
        "UNESCO 来源可作世界遗产身份核对，具体登山路线需另行核验。",
    ),
    "乐山大佛": source(
        "UNESCO World Heritage Centre - Mount Emei Scenic Area, including Leshan Giant Buddha Scenic Area",
        "https://whc.unesco.org/en/list/779/",
        "unesco",
        "今日可按世界遗产中的佛教造像与岷江、青衣江、大渡河交汇景观理解。",
        "UNESCO 来源可作遗产身份核对，游线和开放信息需另查。",
    ),
    "峨嵋山脚": source(
        "UNESCO World Heritage Centre - Mount Emei Scenic Area, including Leshan Giant Buddha Scenic Area",
        "https://whc.unesco.org/en/list/779/",
        "unesco",
        "今日可按峨眉山世界遗产景区入口地带理解，书中山脚经验与现代景区交通已有明显差异。",
        "UNESCO 来源可作遗产身份核对，具体入口、索道和徒步路况需另查。",
    ),
    "昆明车站": source(
        "Wikipedia - Kunming",
        "https://en.wikipedia.org/wiki/Kunming",
        "encyclopedia",
        "今日可按云南省会和铁路、城市交通节点理解，车站只是进入昆明旅行空间的交通入口。",
        "百科页面用于城市节点核对，车站具体信息需另行确认。",
    ),
    "昆明温泉": source(
        "Wikipedia - Kunming",
        "https://en.wikipedia.org/wiki/Kunming",
        "encyclopedia",
        "今日可先按昆明城市周边休闲游览线索理解；具体温泉地点仍需人工核对。",
        "仅能支持昆明城市背景，温泉精确地点仍为待复核项。",
    ),
    "西山": source(
        "Wikipedia - Western Hills",
        "https://en.wikipedia.org/wiki/Western_Hills",
        "encyclopedia",
        "今日可按昆明滇池西岸山地景区理解，适合对照书中城市近郊游览经验。",
        "百科页面用于初步核对，后续建议补充景区官方来源。",
    ),
    "石林": source(
        "UNESCO World Heritage Centre - South China Karst",
        "https://whc.unesco.org/en/list/1248/",
        "unesco",
        "今日可按南方喀斯特世界遗产组成部分理解，景区化程度与早年旅行经验需要分开阅读。",
        "UNESCO 来源可作遗产身份核对，具体景区游线需另查。",
    ),
    "贵阳花溪": source(
        "Wikipedia - Huaxi District",
        "https://en.wikipedia.org/wiki/Huaxi_District",
        "encyclopedia",
        "今日可按贵阳近郊区和山水休闲节点理解，具体书中地点仍需人工复核。",
        "百科页面用于地名初步核对，后续建议补充地方文旅来源。",
    ),
    "桂林伏波山": source(
        "Wikipedia - Fubo Hill",
        "https://en.wikipedia.org/wiki/Fubo_Hill",
        "encyclopedia",
        "今日可按桂林市区山水景点理解，适合对照书中城市山水游览线索。",
        "百科页面用于初步核对，后续建议补充桂林官方旅游来源。",
    ),
    "七星山": source(
        "Wikipedia - Seven Star Park",
        "https://en.wikipedia.org/wiki/Seven_Star_Park",
        "encyclopedia",
        "今日可按桂林七星景区相关山水公园理解，精确对应仍需人工复核。",
        "百科页面用于初步核对，后续建议补充官方景区来源。",
    ),
    "象鼻山": source(
        "Wikipedia - Elephant Trunk Hill",
        "https://en.wikipedia.org/wiki/Elephant_Trunk_Hill",
        "encyclopedia",
        "今日可按桂林标志性城市山水景点理解。",
        "百科页面用于初步核对，后续建议补充景区或文旅官方来源。",
    ),
    "漓江": source(
        "Wikipedia - Li River",
        "https://en.wikipedia.org/wiki/Li_River",
        "encyclopedia",
        "今日可按桂林至阳朔之间的典型山水游览水系理解。",
        "百科页面用于初步核对，游船线路和生态保护信息需另查。",
    ),
    "阳朔": source(
        "Wikipedia - Yangshuo County",
        "https://en.wikipedia.org/wiki/Yangshuo_County",
        "encyclopedia",
        "今日可按桂林山水旅游县城与漓江游览节点理解。",
        "百科页面用于地名核对，具体景区和交通需另查。",
    ),
    "梧州": source(
        "Wikipedia - Wuzhou",
        "https://en.wikipedia.org/wiki/Wuzhou",
        "encyclopedia",
        "今日可按西江流域城市节点理解，适合对照书中水路或沿江旅行线索。",
        "百科页面用于城市节点核对，具体江岸地点仍需人工复核。",
    ),
    "肇庆天柱阁": source(
        "Wikipedia - Zhaoqing",
        "https://en.wikipedia.org/wiki/Zhaoqing",
        "encyclopedia",
        "今日可先按肇庆城市和岭南山水游览节点理解；天柱阁精确对应仍需复核。",
        "百科页面只能支持城市背景，天柱阁需要继续补充公开来源。",
    ),
    "广州中山大学": source(
        "Sun Yat-sen University",
        "https://www.sysu.edu.cn/en/",
        "official",
        "今日可按高校校园和广州城市文化节点理解，需与书中访问语境分开阅读。",
        "高校官网可作机构身份核对，具体历史校区仍需人工复核。",
    ),
    "白云山": source(
        "Wikipedia - Baiyun Mountain (Guangzhou)",
        "https://en.wikipedia.org/wiki/Baiyun_Mountain_(Guangzhou)",
        "encyclopedia",
        "今日可按广州城市山岳景区理解，现代游览设施与早年旅行视角差异明显。",
        "百科页面用于初步核对，后续建议补充景区官方来源。",
    ),
    "漳州": source(
        "Wikipedia - Zhangzhou",
        "https://en.wikipedia.org/wiki/Zhangzhou",
        "encyclopedia",
        "今日可按闽南城市节点理解，具体书中抵达、停留或交通语境仍需细读复核。",
        "百科页面用于城市节点核对。",
    ),
    "厦门": source(
        "Wikipedia - Xiamen",
        "https://en.wikipedia.org/wiki/Xiamen",
        "encyclopedia",
        "今日可按沿海城市、港口和旅游城市节点理解。",
        "百科页面用于城市节点核对，具体景点需分别查证。",
    ),
    "福州": source(
        "Wikipedia - Fuzhou",
        "https://en.wikipedia.org/wiki/Fuzhou",
        "encyclopedia",
        "今日可按福建省会和城市文化节点理解。",
        "百科页面用于城市节点核对，具体景点需分别查证。",
    ),
    "鼓浪屿": source(
        "UNESCO World Heritage Centre - Kulangsu, a Historic International Settlement",
        "https://whc.unesco.org/en/list/1541/",
        "unesco",
        "今日可按世界遗产中的近代国际社区与海岛步行游览空间理解。",
        "UNESCO 来源可作遗产身份核对，岛上具体游线需另查。",
    ),
    "泉州": source(
        "UNESCO World Heritage Centre - Quanzhou: Emporium of the World in Song-Yuan China",
        "https://whc.unesco.org/en/list/1561/",
        "unesco",
        "今日可按宋元中国海洋商贸世界遗产城市理解。",
        "UNESCO 来源可作遗产身份核对，具体点位需另查。",
    ),
    "福州西湖": source(
        "Wikipedia - West Lake Park, Fuzhou",
        "https://en.wikipedia.org/wiki/West_Lake_Park,_Fuzhou",
        "encyclopedia",
        "今日可按福州市区历史园林和公园节点理解。",
        "百科页面用于初步核对，后续建议补充地方文旅来源。",
    ),
    "涌泉寺": source(
        "Wikipedia - Yongquan Temple",
        "https://en.wikipedia.org/wiki/Yongquan_Temple",
        "encyclopedia",
        "今日可按福州鼓山佛寺景点理解，适合对照书中寺庙游览线索。",
        "百科页面用于初步核对，后续建议补充寺院或文旅官方来源。",
    ),
    "北雁荡": source(
        "UNESCO Global Geoparks - Yandangshan",
        "https://en.wikipedia.org/wiki/Yandang_Mountains",
        "encyclopedia",
        "今日可按温州雁荡山山岳景区理解；南北雁荡的具体对应需继续人工核对。",
        "百科页面用于初步核对，后续建议补充官方地质公园或景区来源。",
    ),
    "南雁荡": source(
        "Wikipedia - Yandang Mountains",
        "https://en.wikipedia.org/wiki/Yandang_Mountains",
        "encyclopedia",
        "今日可按雁荡山系旅行线索理解，具体南雁荡景区范围需人工复核。",
        "百科页面用于初步核对，后续建议补充地方文旅来源。",
    ),
    "黄山天都峰排云亭": source(
        "UNESCO World Heritage Centre - Mount Huangshan",
        "https://whc.unesco.org/en/list/547/",
        "unesco",
        "今日可按黄山世界遗产景区中的登山与观景节点理解，具体峰顶开放状态需临行前核验。",
        "UNESCO 来源可作遗产身份核对，天都峰和排云亭细节需补充景区来源。",
    ),
    "青阳九华山": source(
        "Wikipedia - Mount Jiuhua",
        "https://en.wikipedia.org/wiki/Mount_Jiuhua",
        "encyclopedia",
        "今日可按佛教名山与安徽山岳景区理解。",
        "百科页面用于初步核对，后续建议补充景区官方来源。",
    ),
    "安庆小孤山": source(
        "Wikipedia - Xiaogu Shan",
        "https://en.wikipedia.org/wiki/Xiaogu_Shan",
        "encyclopedia",
        "今日可按长江江中山体和历史景观节点理解，具体游览条件需复核。",
        "百科页面用于初步核对，后续建议补充地方文旅来源。",
    ),
    "鄱阳五老峰": source(
        "UNESCO World Heritage Centre - Lushan National Park",
        "https://whc.unesco.org/en/list/778/",
        "unesco",
        "今日可按庐山世界遗产山岳景观的一部分理解；五老峰与鄱阳语境仍需人工核对。",
        "UNESCO 来源可作庐山遗产身份核对，具体峰名对应需补充景区来源。",
    ),
    "三叠瀑": source(
        "UNESCO World Heritage Centre - Lushan National Park",
        "https://whc.unesco.org/en/list/778/",
        "unesco",
        "今日可按庐山瀑布景观线索理解，书中山路经验与现代景区游览需分开阅读。",
        "UNESCO 来源可作庐山遗产身份核对，瀑布点位开放信息需另查。",
    ),
    "南京中山陵": source(
        "Wikipedia - Sun Yat-sen Mausoleum",
        "https://en.wikipedia.org/wiki/Sun_Yat-sen_Mausoleum",
        "encyclopedia",
        "今日可按南京近代纪念建筑和景区节点理解。",
        "百科页面用于初步核对，后续建议补充景区官方来源。",
    ),
    "玄武湖": source(
        "Wikipedia - Xuanwu Lake",
        "https://en.wikipedia.org/wiki/Xuanwu_Lake",
        "encyclopedia",
        "今日可按南京城市湖泊公园和历史景观节点理解。",
        "百科页面用于初步核对，后续建议补充地方官方来源。",
    ),
    "苏州园林": source(
        "UNESCO World Heritage Centre - Classical Gardens of Suzhou",
        "https://whc.unesco.org/en/list/813/",
        "unesco",
        "今日可按世界遗产古典园林体系理解。",
        "UNESCO 来源可作遗产身份核对，具体园林点位需分别查证。",
    ),
    "苏州天平山沧浪亭": source(
        "UNESCO World Heritage Centre - Classical Gardens of Suzhou",
        "https://whc.unesco.org/en/list/813/",
        "unesco",
        "今日可按苏州古典园林与近郊山水游览线索理解；天平山和沧浪亭需分开核对。",
        "UNESCO 来源可作沧浪亭等古典园林身份核对，天平山仍需补充地方来源。",
    ),
    "上海": source(
        "Wikipedia - Shanghai",
        "https://en.wikipedia.org/wiki/Shanghai",
        "encyclopedia",
        "今日可按中国东部沿海超大城市、交通和文化节点理解。",
        "百科页面用于城市节点核对，具体书中地点仍需人工复核。",
    ),
    "青岛崂山": source(
        "Wikipedia - Mount Lao",
        "https://en.wikipedia.org/wiki/Mount_Lao",
        "encyclopedia",
        "今日可按青岛海岸山岳景区和道教文化名山理解。",
        "百科页面用于初步核对，后续建议补充景区官方来源。",
    ),
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def display_place(item: dict[str, Any]) -> str:
    return str(item.get("place") or item.get("name") or "").strip()


def letters_for_place(place: str, chapters: list[dict[str, Any]]) -> list[str]:
    letters: list[str] = []
    for chapter in chapters:
        names = set(chapter.get("places", []) or [])
        names.update(display_place(item) for item in chapter.get("route_now", []) or [])
        if place in names:
            letters.append(str(chapter.get("letter_id") or chapter.get("chapter_id") or "unknown"))
    return letters


def chapter_titles_for_place(place: str, chapters: list[dict[str, Any]]) -> list[str]:
    titles: list[str] = []
    for chapter in chapters:
        names = set(chapter.get("places", []) or [])
        names.update(display_place(item) for item in chapter.get("route_now", []) or [])
        if place in names:
            titles.append(str(chapter.get("title") or chapter.get("chapter_id") or "未命名书信"))
    return titles


def fallback_today(place: str) -> str:
    if any(token in place for token in ["山", "峰", "瀑", "岭", "崂", "雁荡"]):
        return "今日可先按山岳、自然景观或景区线索理解；具体开放范围、交通方式和安全条件仍需公开来源复核。"
    if any(token in place for token in ["寺", "祠", "陵", "亭", "阁", "园", "湖"]):
        return "今日可先按历史文化或园林景观点理解；具体场馆身份、开放信息和保护状态仍需公开来源复核。"
    if any(token in place for token in ["州", "阳", "门", "海", "京", "沪", "安", "州", "庆"]):
        return "今日可先按城市、交通或地名节点理解；具体旅行点位仍需公开来源复核。"
    return "今日景点信息待公开来源复核。"


def build_then_context(place: str, item: dict[str, Any], titles: list[str]) -> list[str]:
    existing = item.get("then_context")
    if isinstance(existing, list) and existing:
        return [str(value) for value in existing]
    if titles:
        return [f"出现在《旅行人信札》书信标题或结构线索：{titles[0]}"]
    return [f"书中出现地点线索：{place}，具体语境待人工复核。"]


def strengthen_place(item: dict[str, Any], chapters: list[dict[str, Any]]) -> dict[str, Any]:
    place = display_place(item)
    titles = chapter_titles_for_place(place, chapters)
    letters = item.get("letters") if isinstance(item.get("letters"), list) else letters_for_place(place, chapters)
    letters = [str(value) for value in letters]
    then_context = build_then_context(place, item, titles)

    strengthened = dict(item)
    strengthened["place"] = place
    strengthened["place_name"] = place
    strengthened["appears_in_letters"] = letters
    strengthened["letters"] = letters
    strengthened["then_context"] = then_context
    strengthened["updated_in"] = UPDATED_IN
    strengthened["is_key_place"] = bool(place in A12_PLACE_SOURCES or len(letters) > 1)

    if place in A12_PLACE_SOURCES:
        src = A12_PLACE_SOURCES[place]
        strengthened.update(
            {
                "source_status": "public_source",
                "source_name": src["source_name"],
                "source_url": src["source_url"],
                "source_type": src["source_type"],
                "source_review_note": src["source_review_note"],
                "today_reading": src["now_context"],
                "now_context": src["now_context"],
                "review_status": "public_source_pending_manual_review",
                "change_note": "书中旅行经验可与今日景区化、城市化或交通条件变化对照阅读；本说明仍需人工复核。",
            }
        )
    else:
        note = "待补充公开来源"
        strengthened.update(
            {
                "source_status": "needs_source_review",
                "source_name": "待补充公开来源",
                "source_url": None,
                "source_type": "unknown",
                "source_review_note": note,
                "today_reading": item.get("today_reading") or fallback_today(place),
                "now_context": item.get("now_context") or item.get("today_reading") or fallback_today(place),
                "review_status": "needs_source_review",
                "change_note": "今日景点身份、开放状态和交通条件尚无足够公开来源支撑，暂不展开判断。",
            }
        )

    return strengthened


def sync_route_now(chapters: list[dict[str, Any]], source_by_place: dict[str, dict[str, Any]]) -> None:
    for chapter in chapters:
        updated_places = []
        for item in chapter.get("route_now", []) or []:
            place = display_place(item)
            source_item = source_by_place.get(place)
            if source_item:
                merged = dict(item)
                for key in [
                    "place_name",
                    "appears_in_letters",
                    "then_context",
                    "today_reading",
                    "now_context",
                    "source_status",
                    "source_name",
                    "source_url",
                    "source_type",
                    "source_review_note",
                    "review_status",
                    "change_note",
                    "updated_in",
                ]:
                    merged[key] = source_item.get(key)
                updated_places.append(merged)
            else:
                updated_places.append(item)
        chapter["route_now"] = updated_places
        public_count = sum(1 for item in updated_places if item.get("source_status") == "public_source")
        pending_count = sum(1 for item in updated_places if item.get("source_status") != "public_source")
        chapter["place_source_summary"] = {
            "public_source_count": public_count,
            "needs_source_review_count": pending_count,
            "updated_in": UPDATED_IN,
        }


def build_route_index(chapters: list[dict[str, Any]], source_by_place: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    route_index: list[dict[str, Any]] = []
    for chapter in chapters:
        places = [str(place) for place in chapter.get("places", []) or []]
        source_covered = [place for place in places if source_by_place.get(place, {}).get("source_status") == "public_source"]
        pending = [place for place in places if place not in source_covered]
        route_index.append(
            {
                "chapter_id": chapter.get("chapter_id"),
                "letter_id": chapter.get("letter_id"),
                "order": chapter.get("order"),
                "title": chapter.get("title"),
                "core_places": places,
                "source_covered_places": source_covered,
                "pending_places": pending,
                "updated_in": UPDATED_IN,
            }
        )
    return route_index


def render_plan() -> str:
    return "\n".join(
        [
            "# v0.7-A12 Place Source Strengthening Plan",
            "",
            "## User Feedback",
            "",
            "- Continue improving the public preview page.",
            "- Add more place context and then/now travel comparison.",
            "- Strengthen today's scenic-place sources while keeping the project in draft public-preview state.",
            "",
            "## A12 Goal",
            "",
            "A12 strengthens public source coverage for the place comparison layer and improves reading flow with a place overview and route index.",
            "",
            "## Source Strategy",
            "",
            "- Prioritize repeated places, chapter-title places, city nodes, historic sites, mountain/scenic sites, and UNESCO/official/museum/encyclopedia sources.",
            "- Keep `source_status=public_source` only when a public source name and URL are recorded.",
            "- Keep unresolved entries as `needs_source_review` with an explicit review note.",
            "",
            "## Page Rhythm",
            "",
            "- Add a place overview panel.",
            "- Add source-status badges and richer place comparison cards.",
            "- Add a 25-letter route index that helps readers jump back to letter cards without changing the hash route.",
            "",
            "## Personal Reading Boundary",
            "",
            "The page remains a personal-reading public preview. Source-derived summaries and excerpts may be shown, but private source files, local paths, and full source files are not published.",
            "",
            "## No Status Promotion",
            "",
            "A12 does not change `status`, does not fill manual review results, and does not promote the project to reviewed/final/publish-ready.",
            "",
            "## A13 Suggestion",
            "",
            "A13 can improve map/timeline reading, add more official local sources for backlog places, or begin real manual review result entry.",
            "",
        ]
    )


def render_report(stats: dict[str, Any], new_sources: list[dict[str, Any]], source_type_counts: Counter[str]) -> str:
    lines = [
        "# Place Source Strengthening Report v0.7-A12",
        "",
        "## Summary",
        "",
        f"- A11 public_source count: `{A11_PUBLIC_SOURCE_COUNT}`",
        f"- A12 public_source count: `{stats['public_source_count']}`",
        f"- New public_source count: `{stats['new_public_source_count']}`",
        f"- Remaining needs_source_review count: `{stats['needs_source_review_count']}`",
        "- Page UI: added place overview, source badges, richer place cards, and route index.",
        "- Public preview state preserved: `draft` / `public-preview` / `manual-review-pending`.",
        "- Local build result: to be verified by `npm run build`.",
        "",
        "## Modified File Families",
        "",
        "- `projects/second-reading-guide/public/*.json`",
        "- `web/public/projects/second-reading-guide/*.json`",
        "- `web/src/pages/ReadingGuideProjectPage.tsx`",
        "- `web/src/types/readingGuide.ts`",
        "- `web/src/styles.css`",
        "- A12 scripts and reports",
        "",
        "## Source Type Counts",
        "",
    ]
    for source_type, count in sorted(source_type_counts.items()):
        lines.append(f"- `{source_type}`: `{count}`")
    lines.extend(["", "## Added / Confirmed Public Sources", ""])
    for item in new_sources:
        lines.append(f"- {item['place']}: {item['source_name']} ({item['source_type']}) - {item['source_url']}")
    lines.extend(
        [
            "",
            "## Unresolved Places",
            "",
            "Remaining `needs_source_review` places are listed in `place_source_backlog_v0.7_a12.md`. They were not filled with guessed sources.",
            "",
            "## Boundary Check",
            "",
            "- No private source file is copied.",
            "- No local private path is exported.",
            "- No manual review result is filled.",
            "- No status promotion is applied.",
            "",
            "## Online URL",
            "",
            "- https://conanxin.github.io/ebook-content-lab/#/projects/second-reading-guide",
            "",
        ]
    )
    return "\n".join(lines)


def render_backlog(backlog: list[dict[str, Any]]) -> str:
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_backlog = sorted(
        backlog,
        key=lambda item: (priority_order.get(item.get("priority", "medium"), 1), item.get("place", "")),
    )
    lines = [
        "# Place Source Backlog v0.7-A12",
        "",
        "Places below still need public source review. Do not infer source status until a usable public source is recorded.",
        "",
        "| priority | place | letters | search suggestion |",
        "|---|---|---|---|",
    ]
    for item in sorted_backlog:
        place = item.get("place", "")
        letters = "、".join(item.get("appears_in_letters", []) or [])
        suggestion = f"Search official tourism/government/museum or encyclopedia pages for {place}."
        lines.append(f"| `{item.get('priority', 'medium')}` | {place} | {letters or '待复核'} | {suggestion} |")
    lines.append("")
    return "\n".join(lines)


def priority_for(item: dict[str, Any]) -> str:
    place = display_place(item)
    letters = item.get("appears_in_letters") or item.get("letters") or []
    if len(letters) > 1 or any(token in place for token in ["西安", "成都", "昆明", "桂林", "广州", "厦门", "福州", "南京", "上海", "青岛"]):
        return "high"
    if any(token in place for token in ["山", "峰", "寺", "祠", "湖", "陵", "园", "江", "瀑"]):
        return "medium"
    return "low"


def build(project: str) -> dict[str, Any]:
    paths = from_project(project)
    overview = read_json(paths.book_overview_json)
    cards_data = read_json(paths.chapter_reading_cards_json)
    chapters = cards_data.get("chapters", [])

    original_places = overview.get("place_then_now") or []
    strengthened_places = [strengthen_place(item, chapters) for item in original_places]
    for item in strengthened_places:
        item["priority"] = priority_for(item)

    source_by_place = {display_place(item): item for item in strengthened_places}
    sync_route_now(chapters, source_by_place)

    public_source_count = sum(1 for item in strengthened_places if item.get("source_status") == "public_source")
    needs_source_review_count = len(strengthened_places) - public_source_count
    source_type_counts = Counter(str(item.get("source_type") or "unknown") for item in strengthened_places if item.get("source_status") == "public_source")

    stats = {
        "version": UPDATED_IN,
        "a11_public_source_count": A11_PUBLIC_SOURCE_COUNT,
        "public_source_count": public_source_count,
        "a12_public_source_count": public_source_count,
        "new_public_source_count": max(0, public_source_count - A11_PUBLIC_SOURCE_COUNT),
        "needs_source_review_count": needs_source_review_count,
        "total_place_count": len(strengthened_places),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    overview["place_then_now"] = strengthened_places
    overview["place_source_stats"] = stats
    overview["route_index"] = build_route_index(chapters, source_by_place)
    overview["then_now_summary"] = (
        f"本轮补强后，{len(strengthened_places)} 个地点中已有 {public_source_count} 个记录公开来源，"
        f"{needs_source_review_count} 个仍需后续查证。页面把书中旅行线索与今日景区、城市、遗址或自然景观点并置，"
        "用于个人阅读导览，不作为最终考据结论。"
    )
    overview.setdefault("source_enrichment", {})["place_source_strengthening"] = stats

    payloads = {
        "book_overview.json": overview,
        "chapter_reading_cards.json": cards_data,
        "key_concepts.json": read_json(paths.key_concepts_json),
        "quote_index.json": read_json(paths.quote_index_json),
        "reading_questions.json": read_json(paths.reading_questions_json),
    }

    for name, payload in payloads.items():
        write_json(paths.public_path(name), payload)
        write_json(paths.web_project_path(name), payload)

    new_sources = [
        {
            "place": item["place"],
            "source_name": item["source_name"],
            "source_url": item["source_url"],
            "source_type": item["source_type"],
        }
        for item in strengthened_places
        if item.get("source_status") == "public_source"
    ]
    backlog = [item for item in strengthened_places if item.get("source_status") != "public_source"]

    paths.report_path("v0.7_a12_place_source_strengthening_plan.md").write_text(render_plan(), encoding="utf-8")
    paths.report_path("place_source_strengthening_report_v0.7_a12.md").write_text(
        render_report(stats, new_sources, source_type_counts),
        encoding="utf-8",
    )
    paths.report_path("place_source_backlog_v0.7_a12.md").write_text(render_backlog(backlog), encoding="utf-8")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    stats = build(args.project)
    print("A12 place sources strengthened")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
