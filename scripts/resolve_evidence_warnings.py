# -*- coding: utf-8 -*-
"""Resolve evidence warnings produced by audit_route_evidence.py.

The script is deliberately narrow and source-bound:
- it separates chapter/title references from factual book_refs;
- it adds only explicitly configured OCR-page evidence;
- it clears or rewrites unsupported fields without changing coordinates or route
  order.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FACT_FIELDS = {"resupply", "lodging", "risks_or_notes", "roads_or_paths"}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.lower()
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[`~!@#$%^&*_+=|\\/<>{}\[\]（）()【】《》“”\"'‘’：:；;，,。.!！?？、-]", "", text)
    return text


def compact(value: Any, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", "" if value is None else str(value)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def append_unique(items: list[Any], item: Any) -> None:
    marker = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else str(item)
    seen = {
        json.dumps(existing, ensure_ascii=False, sort_keys=True) if isinstance(existing, dict) else str(existing)
        for existing in items
    }
    if marker not in seen:
        items.append(item)


def add_review_note(segment: dict[str, Any], note: str) -> None:
    notes = segment.get("review_notes")
    if not isinstance(notes, list):
        notes = [] if notes in (None, "") else [str(notes)]
    if note not in notes:
        notes.append(note)
    segment["review_notes"] = notes


def add_evidence_note(segment: dict[str, Any], note: str) -> None:
    notes = segment.get("evidence_notes")
    if not isinstance(notes, list):
        notes = [] if notes in (None, "") else [str(notes)]
    if note not in notes:
        notes.append(note)
    segment["evidence_notes"] = notes


def book_ref_key(ref: dict[str, Any]) -> tuple[str, str]:
    return (str(ref.get("page", "")), normalize_text(ref.get("quote", "")))


def add_book_ref(segment: dict[str, Any], ref: dict[str, Any]) -> bool:
    refs = segment.setdefault("book_refs", [])
    existing = {book_ref_key(item) for item in refs if isinstance(item, dict)}
    if book_ref_key(ref) in existing:
        return False
    refs.append(ref)
    return True


def is_chapter_ref(ref: dict[str, Any], segment: dict[str, Any]) -> bool:
    quote = str(ref.get("quote", "") or "").strip()
    note = str(ref.get("note", "") or "")
    title = str(segment.get("title", "") or "").strip()
    if "标题" in note or "章节" in note:
        return True
    if title and normalize_text(quote) == normalize_text(title):
        return True
    return False


@dataclass
class Resolution:
    action: str
    new_value: Any | None = None
    note: str = ""
    refs: list[dict[str, Any]] | None = None


RESOLUTIONS: dict[tuple[str, str], Resolution] = {
    ("seg-001", "resupply"): Resolution(
        action="supported_with_new_book_ref",
        new_value="村民提示附近有餐馆，作者找到餐馆后吃了一碗拉面。",
        refs=[
            {
                "page": 45,
                "quote": "找到村民所说的餐馆，点了一碗拉面",
                "note": "支持本段途中补给：村民提示餐馆，作者在餐馆吃拉面。",
            }
        ],
    ),
    ("seg-002", "risks_or_notes"): Resolution(
        action="supported_with_new_book_ref",
        new_value="背包明显变重；晴空湛蓝，又一个高亢的暑天；遇狗阻路后绕道。",
        refs=[
            {
                "page": 56,
                "quote": "背包明显变重了。晴空湛蓝，又一个高亢的暑天",
                "note": "支持背包变重和暑热背景。",
            },
            {
                "page": 58,
                "quote": "既然它不让我走，我只好绕道了",
                "note": "支持路上因犬只阻路而绕行。",
            },
        ],
    ),
    ("seg-003", "lodging"): Resolution(
        action="cleared_to_unspecified",
        new_value="书中未明示",
        note="未找到能直接支持“无本段步行住宿”的正面证据；保留为复核说明。",
    ),
    ("seg-006", "roads_or_paths"): Resolution(
        action="supported_with_new_book_ref",
        new_value="修路路段、老路、人行道、国道京环线（G112）。",
        refs=[
            {
                "page": 151,
                "quote": "我们尽量走路边的老路或人行道",
                "note": "支持本段修路环境下走老路或人行道。",
            },
            {
                "page": 161,
                "quote": "汇入国道京环线（G112）",
                "note": "支持本段道路进入国道京环线/G112。",
            },
        ],
    ),
    ("seg-006", "risks_or_notes"): Resolution(
        action="supported_with_new_book_ref",
        new_value="修路尘土飞扬、烈日、疲劳；王抒脚上打了水泡。",
        refs=[
            {
                "page": 154,
                "quote": "大卡车奔忙来去，拖曳着尘土飞扬的长龙",
                "note": "支持修路车辆扬尘。",
            },
            {
                "page": 155,
                "quote": "他的脚第一天就打了水泡",
                "note": "支持脚部水泡风险。",
            },
            {
                "page": 160,
                "quote": "顶着烈日再走一个小时",
                "note": "支持烈日和疲劳背景。",
            },
        ],
    ),
    ("seg-007", "route_summary"): Resolution(
        action="supported_with_new_book_ref",
        new_value="从龙门所沿 G112 北上，到小东沟林场一带越过白河与黑河分水岭，下山后折向东，经东万口乡，下午到白草镇；书中另写到塘子庙温泉和住宿安排。",
        refs=[
            {
                "page": 174,
                "quote": "塘子庙就是明代地图上的“滚水塘”，以温泉得名",
                "note": "支持 route_summary 中塘子庙相关描述。",
            }
        ],
    ),
    ("seg-007", "lodging"): Resolution(
        action="supported_with_new_book_ref",
        new_value="塘子庙一带的“温泉宾馆”。",
        refs=[
            {
                "page": 174,
                "quote": "我们住的这家“温泉宾馆”开业不久",
                "note": "支持本段住宿为塘子庙温泉宾馆。",
            }
        ],
    ),
    ("seg-008", "route_summary"): Resolution(
        action="supported_with_new_book_ref",
        new_value="从白草镇出发，沿黑河东岸 X404 北上，经过三道川、黑龙山、山神庙等地，进入老掌沟；从沟口往沟里走半小时后，请度假村老板开车来接。",
        refs=[
            {
                "page": 207,
                "quote": "请他开车来接我们。他爽快地答应了",
                "note": "支持本段后段由度假村车辆接应。",
            }
        ],
    ),
    ("seg-008", "risks_or_notes"): Resolution(
        action="supported_with_new_book_ref",
        new_value="离老掌沟还有约二十公里，书中判断很难完成；山区可能突降暴雨，路上有越野车队；后段联系度假村车辆接应。",
        refs=[
            {
                "page": 205,
                "quote": "离目的地老掌沟还有差不多二十公里，看来很难完成了",
                "note": "支持本段路程压力。",
            },
            {
                "page": 205,
                "quote": "山区有自己的小气候，也许会突然来一场暴雨",
                "note": "支持天气突变风险。",
            },
            {
                "page": 205,
                "quote": "一路上已见到好几拨越野车队",
                "note": "支持越野车相关风险。",
            },
        ],
    ),
    ("seg-009", "risks_or_notes"): Resolution(
        action="supported_with_new_book_ref",
        new_value="沟谷中需反复过河；细沙和深车辙使行走困难；五公里沟谷实际走了差不多十公里。",
        refs=[
            {
                "page": 220,
                "quote": "无论怎么走都得反复过河",
                "note": "支持反复过河风险。",
            },
            {
                "page": 220,
                "quote": "满谷都是细沙，被越野车纵横碾压之后，车辙深陷",
                "note": "支持细沙和深车辙。",
            },
            {
                "page": 220,
                "quote": "本来只有五公里长的沟谷，我们实际走了差不多十公里",
                "note": "支持绕行导致距离增加。",
            },
        ],
    ),
    ("seg-010", "resupply"): Resolution(
        action="supported_with_new_book_ref",
        new_value="石柱村商店提供方便面，作者先喝两瓶啤酒。",
        refs=[
            {
                "page": 245,
                "quote": "我给你们泡碗方便面吧",
                "note": "支持石柱村商店提供方便面。",
            },
            {
                "page": 245,
                "quote": "从冰箱里拿出两瓶啤酒，让我们先喝着",
                "note": "支持途中补给中的啤酒。",
            },
        ],
    ),
    ("seg-011", "risks_or_notes"): Resolution(
        action="supported_with_new_book_ref",
        new_value="本段先乘出租车到梳妆楼，再送到五花草甸；随后从五花草甸一带补走到沽源。",
        refs=[
            {
                "page": 265,
                "quote": "先把我们送去梳妆楼，在那里等着，再送我们去五花草甸",
                "note": "支持本段存在乘车到补走起点的接续。",
            },
            {
                "page": 273,
                "quote": "上午九点五十分，出租车把我们送到五花草甸",
                "note": "支持从五花草甸开始补走。",
            },
        ],
    ),
    ("seg-012", "risks_or_notes"): Resolution(
        action="supported_with_new_book_ref",
        new_value="高原的暴晒和暑热开始发威；作者越来越畏惧阳光；到方元酒店时两脚打了水泡。",
        refs=[
            {
                "page": 285,
                "quote": "高原的暴晒和暑热开始发威",
                "note": "支持本段暴晒和暑热风险。",
            },
            {
                "page": 286,
                "quote": "我越来越畏惧阳光",
                "note": "支持强日晒对身体状态的影响。",
            },
            {
                "page": 300,
                "quote": "两脚的脚跟和外侧都打了水泡",
                "note": "支持到达方元酒店时的脚部风险。",
            },
        ],
    ),
    ("seg-013", "route_summary"): Resolution(
        action="rewritten_without_unsupported_part",
        new_value="从塞北管理区沿县道402往北，跨过河北与内蒙古分界后进入正蓝旗，沿X502继续北行，经黑土城镇前往李陵台遗址；之后到黑城子镇一带。",
        note="原 summary 中“经过明安驿”与本段 book_refs 无法对应；已移入复核备注。",
        refs=[
            {
                "page": 305,
                "quote": "由此往北再走三公里，十一点三十分，我们到达河北与内蒙的分界点",
                "note": "支持本段跨过河北与内蒙古分界。",
            },
            {
                "page": 313,
                "quote": "下午两点半，我们走到黑土城镇的南侧",
                "note": "支持本段到达黑土城镇。",
            },
        ],
    ),
    ("seg-014", "resupply"): Resolution(
        action="supported_with_new_book_ref",
        new_value="途中在蒙古包休息；对方提供热水，作者一行吃自带的馒头和面包。",
        refs=[
            {
                "page": 328,
                "quote": "于是我们进到院内的一个蒙古包里",
                "note": "支持途中在蒙古包休息。",
            },
            {
                "page": 328,
                "quote": "我们自己带着午饭，所以就不麻烦他们了，就着水吃起自带的馒头和面包",
                "note": "支持自带午饭和热水。",
            },
        ],
    ),
    ("seg-015", "resupply"): Resolution(
        action="supported_with_new_book_ref",
        new_value="电视台记者送来冰冻矿泉水和西瓜。",
        refs=[
            {
                "page": 348,
                "quote": "冰冻的矿泉水和西瓜从未如此充满吸引力",
                "note": "支持最后一日补给。",
            }
        ],
    ),
    ("seg-015", "lodging"): Resolution(
        action="supported_with_new_book_ref",
        new_value="前一晚住正蓝旗上都镇的上都酒店。",
        refs=[
            {
                "page": 318,
                "quote": "直奔网上推荐的上都酒店，办好入住手续",
                "note": "支持前一晚住宿在正蓝旗上都酒店。",
            }
        ],
    ),
    ("seg-015", "risks_or_notes"): Resolution(
        action="supported_with_new_book_ref",
        new_value="最后一天天气极热；脚趾和脚后跟多处水泡，脚底疼痛；路上没有树，也没有其他可以遮阴的地方。",
        refs=[
            {
                "page": 344,
                "quote": "今天会是几年来最热的一天",
                "note": "支持极端暑热。",
            },
            {
                "page": 345,
                "quote": "发现脚趾头和脚后跟打了好几个水泡",
                "note": "支持脚部水泡风险。",
            },
            {
                "page": 346,
                "quote": "事实上也没有地方适合休息，没有树，也没有其他可以遮阴的地方",
                "note": "支持无遮阴风险。",
            },
        ],
    ),
}


ORIGINAL_CLAIMS: dict[tuple[str, str], str] = {
    ("seg-001", "resupply"): "第45页提到村民提示餐馆并在餐馆吃拉面",
    ("seg-002", "risks_or_notes"): "暑热、背包变重、路上犬只绕行",
    ("seg-003", "lodging"): "无本段步行住宿",
    ("seg-006", "roads_or_paths"): "修路路段、老路、人行道、国道京环线/G112",
    ("seg-006", "risks_or_notes"): "修路扬尘、烈日、疲劳、水泡",
    ("seg-007", "route_summary"): "经塘子庙",
    ("seg-007", "lodging"): "塘子庙温泉宾馆一带",
    ("seg-008", "route_summary"): "因路程和同行人返程安排，后段由度假村车接走",
    ("seg-008", "risks_or_notes"): "长距离近四十公里计划、天气突变、越野车、后段非连续步行",
    ("seg-009", "risks_or_notes"): "反复过河、深车辙、细沙、绕行导致距离增加",
    ("seg-010", "resupply"): "途中小店泡面、啤酒",
    ("seg-011", "risks_or_notes"): "本段包含车辆回到补走起点，需避免误画乘车路线",
    ("seg-012", "risks_or_notes"): "酷热、强日晒、长距离无行道树",
    ("seg-013", "route_summary"): "经过明安驿",
    ("seg-014", "resupply"): "途中蒙古包/牧户处休息、自带午饭和热水",
    ("seg-015", "resupply"): "电视台记者送冰冻矿泉水和西瓜",
    ("seg-015", "lodging"): "前一晚住正蓝旗上都镇",
    ("seg-015", "risks_or_notes"): "极端暑热、脚底疼痛、无树荫",
}


POST_CLEANUPS: dict[str, dict[str, Any]] = {
    "seg-004": {
        "fields": {
            "route_summary": "吃完早饭，作者一行告别延庆，坐出租车前往旧县镇，从那里开始走去白河堡水库；经车坊、黑峪口、盘云岭山口，沿昌赤路和水库边道路到白河堡水库。",
            "lodging": "水库库区管理所的燕山天池宾馆。",
        },
        "refs": [
            {
                "page": 102,
                "quote": "吃完早饭，我们告别延庆，坐出租车前往旧县镇，从那里开始走去白河堡水库",
                "note": "支持本段从延庆/旧县镇开始走向白河堡水库。",
            },
            {
                "page": 111,
                "quote": "盘云岭山口是由地质学上所说的盘云岭断层形成的",
                "note": "支持本段经过盘云岭山口。",
            },
            {
                "page": 115,
                "quote": "找到水库库区管理所的燕山天池宾馆",
                "note": "支持本段住宿地点。",
            },
        ],
        "ref_updates": [
            {
                "page": 104,
                "old_quote": "今昌赤路从车坊向北，一路缓坡上升",
                "new_quote": "今昌赤路（即212省道）从车坊向北，一路缓坡上升",
            },
            {
                "page": 114,
                "old_quote": "沿昌赤路在水库边走半小时",
                "new_quote": "沿昌赤路（S212）在水库边走半小时之后",
            },
        ],
    },
    "seg-005": {
        "fields": {
            "route_summary": "从白河堡水库一带沿白河河谷行走，上午到达骆驼山村；从骆驼山村离开滦赤路，向北转入 X405 县级公路蒋京线，最终到长伸地村附近。",
            "walking_directions": [
                "沿白河河谷前行。",
                "上午到达骆驼山村后，向北折入 X405 县级公路蒋京线。",
                "到长伸地村口后右转过河上山至住宿处。",
            ],
            "water_sources": "白河河谷。",
        },
        "refs": [
            {
                "page": 125,
                "quote": "公路紧贴在白河河谷的北岸",
                "note": "支持本段沿白河河谷行走。",
            },
            {
                "page": 126,
                "quote": "上午十点，到达骆驼山村",
                "note": "支持本段到达骆驼山村。",
            },
            {
                "page": 127,
                "quote": "从骆驼山村开始，我们就要离开滦赤路，向北折人编号为X405的县级公路蒋京线",
                "note": "支持从骆驼山转入 X405/蒋京线。",
            },
        ],
        "review_note": "证据不足，待人工复核：seg-005 原 route_summary / walking_directions 中的“郑家窑、镇虏楼”未在正文事实页形成足够支撑，本轮仅从摘要和方向中移除，地点候选仍需回看 PDF。",
    },
    "seg-009": {
        "fields": {
            "route_summary": "首先要补上昨天没有走完的一段；在南沟口附近下车后开始补走这一段；从沟门往北走十多分钟到分水岭，经前坝村和后坝村一带，下午四点一刻到小厂镇。",
            "walking_directions": [
                "在南沟口附近下车，补走前一日未完成的沟谷路段。",
                "从沟门往北过分水岭。",
                "沿 X404 经前坝、后坝一带，下午到小厂镇。",
            ],
            "terrain": "沟谷多小河、细沙和车辙；沟门以北为开阔田野，沙岭一带为沙质地貌。",
        },
        "refs": [
            {
                "page": 218,
                "quote": "首先要补上昨天没有走完的一段",
                "note": "支持本段补走前一日未完成路段。",
            },
            {
                "page": 221,
                "quote": "从沟门往北走十多分钟，就到了燕山山脉北支的分水岭",
                "note": "支持从沟门向北过分水岭。",
            },
            {
                "page": 222,
                "quote": "沙岭至小厂镇地势下降明显",
                "note": "支持沙岭至小厂镇的地势和路线背景。",
            },
            {
                "page": 224,
                "quote": "X404的路东先后是前坝村和后坝村",
                "note": "支持经前坝、后坝一带。",
            },
            {
                "page": 228,
                "quote": "下午四点一刻，我们走到X404与S245交叉的地方，终于到小厂镇了",
                "note": "支持本段到达小厂镇。",
            },
        ],
    },
    "seg-012": {
        "fields": {
            "route_summary": "从沽源县城北出，经过察罕脑儿/小宏城子遗址、水泉淖尔；从水泉淖尔向东上山到转佛庙村南口，沿 024 县道东北行到马神庙村，再向塞北管理区方元酒店行走。",
            "walking_directions": [
                "从沽源酒店沿街北走，右转东行过青年湖大桥。",
                "到小宏城子遗址后沿024县级公路向北，再折向东北。",
                "从水泉淖尔向东上山到转佛庙村南口；沿024县道东北行，半小时后到马神庙村，再向塞北管理区行走。",
            ],
        },
        "refs": [
            {
                "page": 291,
                "quote": "从水泉淖尔向东，一路上山，到转佛庙村南口所建的旅游点",
                "note": "支持经转佛庙村南口。",
            },
            {
                "page": 298,
                "quote": "沿着024县道东北行，一路下山，半小时后走到紧傍滦河的马神庙村",
                "note": "支持从转佛庙方向沿 024 县道到马神庙村。",
            },
            {
                "page": 299,
                "quote": "从马神庙村向北的公路，是县级公路X402从前的老路",
                "note": "支持从马神庙村继续向北进入塞北管理区方向。",
            },
        ],
    },
    "seg-014": {
        "ref_updates": [
            {
                "page": 332,
                "old_quote": "过了闪电河大桥，可以看到公路西北隐隐隆起的青色城垣",
                "new_quote": "过了闪电河（上都高勒）大桥，可以看到公路西北隐隐隆起",
            }
        ]
    },
}


def load_pages(path: Path) -> dict[int, dict[str, Any]]:
    pages: dict[int, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            pages[int(row["page"])] = row
    return pages


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_unsupported(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def validate_ref(ref: dict[str, Any], pages: dict[int, dict[str, Any]]) -> tuple[bool, str]:
    try:
        page = int(ref["page"])
    except (KeyError, TypeError, ValueError):
        return False, "invalid page"
    quote = str(ref.get("quote", "") or "")
    page_text = str((pages.get(page) or {}).get("text", "") or "")
    if normalize_text(quote) and normalize_text(quote) in normalize_text(page_text):
        return True, "found"
    return False, "quote not found in OCR page"


def move_chapter_refs(segment: dict[str, Any]) -> int:
    refs = segment.get("book_refs")
    if not isinstance(refs, list):
        return 0
    factual: list[dict[str, Any]] = []
    chapter_refs = segment.get("chapter_refs")
    if not isinstance(chapter_refs, list):
        chapter_refs = []
    moved = 0
    for ref in refs:
        if isinstance(ref, dict) and is_chapter_ref(ref, segment):
            moved_ref = copy.deepcopy(ref)
            moved_ref["note"] = "章节或段落标题来源"
            append_unique(chapter_refs, moved_ref)
            moved += 1
        else:
            factual.append(ref)
    segment["book_refs"] = factual
    if chapter_refs:
        segment["chapter_refs"] = chapter_refs
    return moved


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "segment_id",
        "field",
        "claim",
        "action",
        "before",
        "after",
        "added_refs",
        "moved_to_review_notes",
        "quote_validation",
        "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def render_report(
    rows: list[dict[str, Any]],
    post_rows: list[dict[str, Any]],
    chapter_moves: dict[str, int],
    fail_segments: list[str],
    counts: dict[str, int],
) -> str:
    lines = [
        "# 证据警告清理报告",
        "",
        "本报告基于 `unsupported_claims.csv` 清理证据不足字段，并把章节/路线标题引用移入 `chapter_refs`。处理过程不使用坐标或现代地图反推路线。",
        "",
        "## 汇总",
        "",
        f"- unsupported claims 总数: {counts['total']}",
        f"- 找到补充证据并保留/改写字段: {counts['supported']}",
        f"- 改为 null 或“书中未明示”: {counts['cleared']}",
        f"- 移动到 review_notes: {counts['moved_to_notes']}",
        f"- 标题移出后追加清理项: {len(post_rows)}",
        f"- 移入 chapter_refs 的标题引用: {sum(chapter_moves.values())}",
        f"- 只有 chapter_refs、缺少事实 book_refs 的段落: {', '.join(fail_segments) if fail_segments else '无'}",
        "",
        "## 原始 18 条分段修改",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['segment_id']} `{row['field']}`",
                "",
                f"- action: {row['action']}",
                f"- before: {row['before']}",
                f"- after: {row['after']}",
                f"- added_refs: {row['added_refs'] or '无'}",
                f"- moved_to_review_notes: {row['moved_to_review_notes']}",
                f"- quote_validation: {row['quote_validation']}",
                f"- notes: {row['notes'] or '无'}",
                "",
            ]
        )
    if post_rows:
        lines.extend(["## 标题移出后的追加清理", ""])
        for row in post_rows:
            lines.extend(
                [
                    f"### {row['segment_id']}",
                    "",
                    f"- action: {row['action']}",
                    f"- fields: {row['fields']}",
                    f"- added_refs: {row['added_refs'] or '无'}",
                    f"- quote_validation: {row['quote_validation']}",
                    f"- notes: {row['notes'] or '无'}",
                    "",
                ]
            )
    lines.extend(["## chapter_refs 移动", ""])
    for sid, count in sorted(chapter_moves.items()):
        lines.append(f"- {sid}: {count} 条标题/章节引用移入 chapter_refs")
    return "\n".join(lines).rstrip() + "\n"


def update_existing_refs(segment: dict[str, Any], updates: list[dict[str, Any]]) -> list[str]:
    changed: list[str] = []
    refs = segment.get("book_refs")
    if not isinstance(refs, list):
        return changed
    for update in updates:
        page = str(update.get("page"))
        old_norm = normalize_text(update.get("old_quote", ""))
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            if str(ref.get("page")) != page:
                continue
            if old_norm and normalize_text(ref.get("quote", "")) == old_norm:
                ref["quote"] = update["new_quote"]
                changed.append(f"p{page} quote updated")
    return changed


def apply_post_cleanups(
    segments: list[dict[str, Any]],
    pages: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(segment.get("id")): segment for segment in segments}
    rows: list[dict[str, Any]] = []
    for sid, cleanup in POST_CLEANUPS.items():
        segment = by_id.get(sid)
        if not segment:
            continue
        added_refs: list[str] = []
        validations: list[str] = []
        for ref in cleanup.get("refs", []):
            ok, reason = validate_ref(ref, pages)
            validations.append(f"p{ref.get('page')}:{reason}")
            if ok and add_book_ref(segment, copy.deepcopy(ref)):
                added_refs.append(f"p{ref['page']} {ref['quote']}")
        ref_updates = update_existing_refs(segment, cleanup.get("ref_updates", []))
        for field, value in cleanup.get("fields", {}).items():
            segment[field] = value
            add_evidence_note(segment, f"{field}: 标题引用移出后补充正文证据并收紧表达。")
        if cleanup.get("review_note"):
            add_review_note(segment, cleanup["review_note"])
        for update_note in ref_updates:
            add_evidence_note(segment, update_note)
        if cleanup.get("fields") or added_refs or ref_updates:
            segment["evidence_status"] = "warning"
            rows.append(
                {
                    "segment_id": sid,
                    "action": "post_cleanup_after_chapter_ref_split",
                    "fields": ", ".join(sorted(cleanup.get("fields", {}).keys())) or "book_refs",
                    "added_refs": " | ".join(added_refs + ref_updates),
                    "quote_validation": " | ".join(validations) if validations else "无新增引文",
                    "notes": cleanup.get("review_note", ""),
                }
            )
    return rows


def update_review_notes(path: Path, rows: list[dict[str, Any]], fail_segments: list[str]) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    marker = "## 证据警告清理记录"
    section = [
        marker,
        "",
        "- 本节由 `scripts/resolve_evidence_warnings.py` 生成；只记录证据不足字段的处理，不改变路线顺序或坐标。",
    ]
    moved = [row for row in rows if row["moved_to_review_notes"] == "yes"]
    if moved:
        section.append("- 已移入复核的证据不足内容：")
        for row in moved:
            section.append(f"  - {row['segment_id']} `{row['field']}`: {row['before']}")
    else:
        section.append("- 本轮没有新增需移入复核的字段。")
    if fail_segments:
        section.append("- 仅有 chapter_refs、缺少事实 book_refs 的段落：" + ", ".join(fail_segments))
    else:
        section.append("- 每段均保留至少 1 条路线事实 book_refs。")

    new_section = "\n".join(section).rstrip() + "\n"
    if marker in existing:
        existing = existing.split(marker, 1)[0].rstrip() + "\n\n" + new_section
    else:
        existing = existing.rstrip() + "\n\n" + new_section if existing.strip() else new_section
    path.write_text(existing, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve route evidence warnings.")
    parser.add_argument("--segments", required=True, help="Input audited route segments JSON")
    parser.add_argument("--unsupported", required=True, help="Input unsupported_claims.csv")
    parser.add_argument("--book-pages", required=True, help="Input book_pages.cleaned.jsonl")
    parser.add_argument("--chunks", required=True, help="Input book_chunks.jsonl; loaded for provenance/search parity")
    parser.add_argument("--output", required=True, help="Output resolved route segments JSON")
    parser.add_argument("--report", required=True, help="Output Markdown report")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    segment_path = Path(args.segments)
    unsupported_path = Path(args.unsupported)
    pages_path = Path(args.book_pages)
    chunks_path = Path(args.chunks)
    output_path = Path(args.output)
    report_path = Path(args.report)
    data_dir = output_path.parent

    segments = json.loads(segment_path.read_text(encoding="utf-8"))
    if not isinstance(segments, list):
        raise SystemExit("--segments must be a JSON array")
    pages = load_pages(pages_path)
    # Loaded to satisfy the declared input contract; current deterministic
    # resolutions are page-based and do not need chunk-level fallback.
    _chunks = load_jsonl(chunks_path)
    unsupported_rows = load_unsupported(unsupported_path)

    by_id = {str(segment.get("id")): segment for segment in segments}
    chapter_moves: dict[str, int] = {}
    for segment in segments:
        segment.pop("evidence_audit", None)
        moved = move_chapter_refs(segment)
        if moved:
            chapter_moves[str(segment.get("id"))] = moved
            add_evidence_note(segment, f"已将 {moved} 条章节/路线标题引用移入 chapter_refs，book_refs 仅保留路线事实证据。")

    resolution_rows: list[dict[str, Any]] = []
    counts = {"total": 0, "supported": 0, "cleared": 0, "moved_to_notes": 0}

    unsupported_by_key = {
        (row.get("segment_id", ""), row.get("field", "")): row
        for row in unsupported_rows
    }
    original_unsupported_rows: list[dict[str, str]] = []
    for key, claim in ORIGINAL_CLAIMS.items():
        row = dict(unsupported_by_key.get(key, {}))
        row.setdefault("segment_id", key[0])
        row.setdefault("field", key[1])
        row.setdefault("claim", claim)
        original_unsupported_rows.append(row)

    for unsupported in original_unsupported_rows:
        sid = unsupported["segment_id"]
        field = unsupported["field"]
        claim = unsupported.get("claim", ORIGINAL_CLAIMS.get((sid, field), ""))
        segment = by_id.get(sid)
        if segment is None:
            continue
        counts["total"] += 1
        before = copy.deepcopy(segment.get(field))
        resolution = RESOLUTIONS.get((sid, field))
        quote_validation: list[str] = []
        added_refs: list[str] = []
        moved_to_notes = "no"

        if resolution is None:
            resolution = Resolution(
                action="cleared_to_unspecified",
                new_value="书中未明示" if field in FACT_FIELDS else before,
                note="未配置补充证据，按保守规则降级。",
            )

        refs = resolution.refs or []
        all_refs_valid = True
        for ref in refs:
            ok, reason = validate_ref(ref, pages)
            quote_validation.append(f"p{ref.get('page')}:{reason}")
            if ok:
                if add_book_ref(segment, copy.deepcopy(ref)):
                    added_refs.append(f"p{ref['page']} {ref['quote']}")
            else:
                all_refs_valid = False

        if resolution.action == "supported_with_new_book_ref" and all_refs_valid:
            segment[field] = resolution.new_value
            counts["supported"] += 1
        elif resolution.action == "rewritten_without_unsupported_part":
            segment[field] = resolution.new_value
            note = f"证据不足，待人工复核：{field} 原内容含无法由本段 book_refs 支撑的信息；原内容：{compact(before, 180)}"
            add_review_note(segment, note)
            moved_to_notes = "yes"
            counts["moved_to_notes"] += 1
        else:
            segment[field] = resolution.new_value
            counts["cleared"] += 1
            note = f"证据不足，待人工复核：{field} 原内容：{compact(before, 180)}"
            add_review_note(segment, note)
            moved_to_notes = "yes"
            counts["moved_to_notes"] += 1

        segment["evidence_status"] = "warning"
        add_evidence_note(segment, f"{field}: {resolution.action}; {resolution.note or '已按书中证据清理。'}")
        if refs and not all_refs_valid:
            add_evidence_note(segment, f"{field}: 补充引文未全部通过页内校验，已保守处理。")

        resolution_rows.append(
            {
                "segment_id": sid,
                "field": field,
                "claim": claim,
                "action": resolution.action,
                "before": compact(before, 220),
                "after": compact(segment.get(field), 220),
                "added_refs": " | ".join(added_refs),
                "moved_to_review_notes": moved_to_notes,
                "quote_validation": " | ".join(quote_validation) if quote_validation else "无新增引文",
                "notes": resolution.note,
            }
        )

    post_rows = apply_post_cleanups(segments, pages)

    fail_segments: list[str] = []
    for segment in segments:
        refs = segment.get("book_refs")
        if not isinstance(refs, list) or not refs:
            fail_segments.append(str(segment.get("id")))
            segment["evidence_status"] = "fail"
            add_evidence_note(segment, "该段只有 chapter_refs 或缺少路线事实 book_refs。")
        elif "evidence_status" not in segment:
            segment["evidence_status"] = "warning" if segment.get("chapter_refs") else "pass"

    output_path.write_text(json.dumps(segments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(render_report(resolution_rows, post_rows, chapter_moves, fail_segments, counts), encoding="utf-8")
    write_csv(data_dir / "unsupported_claims.resolved.csv", resolution_rows)
    update_review_notes(data_dir / "review_notes.md", resolution_rows, fail_segments)

    print(f"resolved route segments written: {output_path}")
    print(f"report written: {report_path}")
    print(f"unsupported claims total={counts['total']} supported={counts['supported']} cleared={counts['cleared']} moved_to_notes={counts['moved_to_notes']}")
    print(f"post_cleanup_items={len(post_rows)}")
    print(f"chapter_refs_moved={sum(chapter_moves.values())} fail_segments={','.join(fail_segments) if fail_segments else 'none'}")


if __name__ == "__main__":
    main()
