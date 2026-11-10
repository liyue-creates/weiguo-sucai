#!/usr/bin/env python3
"""Rebuild materials.json and materials.md from the daily markdown sources.

Default source directory is the parent of this file (/workspace/mirror).
Override with SUCAI_SOURCE=/path/to/mirror.

Usage:
    python3 generate.py
    SUCAI_SOURCE=/workspace/mirror python3 /workspace/mirror/site/generate.py
"""

from __future__ import annotations

import json
import os
import re
from collections import OrderedDict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = Path(os.environ.get("SUCAI_SOURCE", ROOT.parent))
OUT_DIR = ROOT
DATA_DIR = OUT_DIR / "data"
SEOUL = timezone(timedelta(hours=9))

CN_BATCH = [
    ("二十一", 21), ("二十", 20), ("十九", 19), ("十八", 18), ("十七", 17),
    ("十六", 16), ("十五", 15), ("十四", 14), ("十三", 13), ("十二", 12),
    ("十一", 11), ("十", 10), ("九", 9), ("八", 8), ("七", 7),
    ("六", 6), ("五", 5), ("四", 4), ("三", 3), ("二", 2), ("一", 1),
]

CATEGORY_MAP = OrderedDict([
    ("A", "小而美作品"),
    ("B", "细分人群"),
    ("C", "大佬观点·爆款型"),
    ("D", "热词·高星"),
    ("E", "长青题"),
    ("F", "创作方法论"),
    ("G", "GitHub对你自己有用"),
])

FILTER_CHIPS = [
    "小而美作品",
    "细分人群",
    "大佬观点·爆款型",
    "好玩产品",
    "求职测评可用",
    "二次元",
    "应季",
    "GitHub对你自己有用",
    "国外火国内未火",
]

STAGE_CANON = ["萌芽", "爆发", "衰退", "常青", "扩散"]

# Extra ratings / overrides not always present as a clean field.
RATING_OVERRIDE = {
    "S006": "喜欢",
    "S010": "喜欢",
    "S011": "好",
    "S012": "好",
    "S014": "好",
    "S015": "好",
    "S016": "好",
    "S017": "好",
    "S018": "好",
    "S019": "好",
    "S020": "好",
    "S021": "好",
    "S022": "好",
    "S023": "好",
    "S024": "好",
    "S025": "好",
    "S026": "好",
    "S027": "好",
    "S028": "好",
    "S029": "好",
    "S030": "好",
    "S047": "值得做",
    "S064": "值得做",
}

# Viewer moments (and a few extra fields) taken from the text that was
# actually sent, when the markdown store is more compressed.
CHAT_OVERLAY = {
    "S122": {
        "viewer_moment": "原来不是只有我投出去都石沉大海。",
        "stage": "爆发",
    },
    "S123": {
        "viewer_moment": "我也想把老板（或者自己）关进地下室玩一把。",
        "stage": "爆发",
    },
    "S124": {
        "viewer_moment": "租房、住宿舍买不到合适的柜子，原来可以自己设计。",
        "stage": "萌芽",
    },
}

PRIVACY_REPLACEMENTS = [
    (r"可接\s*MiniMax\s*工作台商单", "可做成生活工作台"),
    (r"接\s*MiniMax\s*工作台商单", "可做成生活工作台"),
    (r"并进\s*MiniMax\s*工作台", "可做成生活工作台"),
    (r"可接\s*MiniMax\s*工作台(?:的话)?(?:求职线|商单)?", "可做成生活工作台"),
    (r"接\s*MiniMax\s*工作台的话", "如果做成生活工作台"),
    (r"接\s*MiniMax\s*工作台(?:的话)?(?:求职线|商单)?", "可做成生活工作台"),
    (r"接\s*MiniMax\s*商单", "可做成生活工作台"),
    (r"MiniMax\s*工作台商单", "生活工作台"),
    (r"MiniMax\s*工作台", "生活工作台"),
    (r"MiniMax\s*商单", "生活工作台"),
    (r"可接工作台商单", "可做成生活工作台"),
    (r"工作台商单", "生活工作台"),
    (r"商单文案", "文案"),
    (r"https://zhiji-career-preview\.vercel\.app/reports/?", ""),
    (r"职迹可用", "求职测评可用"),
    (r"职迹报告", "求职测评报告"),
    (r"可接职迹", "可做成求职测评"),
    (r"接职迹", "可做成求职测评"),
    (r"给职迹", "给求职测评"),
    (r"做成职迹", "做成求职测评"),
    (r"职迹可参考", "求职测评可参考"),
    (r"与职迹", "与求职测评"),
    (r"和职迹", "和求职测评"),
    (r"职迹「", "求职测评「"),
    (r"职迹“", "求职测评“"),
    (r"职迹", "求职测评"),
    (r"做进\s*My Room[：:，,]?", ""),
    (r"和 My Room 也能接[：:。]?", ""),
    (r"接\s*My Room", ""),
    (r"My Room", "个人空间"),
    (r"唯果自己是谷圈人，能讲成", "可讲成"),
    (r"申请人：唯果", "申请人：本人"),
    (r"替唯果干了什么", "帮你干了什么"),
    (r"替唯果干了啥", "帮你干了啥"),
    (r"信息收集 bot、选题 bot", "不同的 AI 分身"),
    (r"信息收集 bot", "素材收集助手"),
    (r"选题 bot", "选题助手"),
    (r"正文和开头 bot", "后续写作助手"),
    (r"给你的工作台或 bot 们", "给生活工作台"),
    (r"让各分工bot写今天", "让 AI 分身写今天"),
    (r"唯果", ""),
    (r"给她的工作台", "给生活工作台"),
    (r"记成她要的", "记成"),
    (r"她的人生星空线/演唱会年鉴可以复用", "人生星空线、演唱会年鉴可以复用"),
    (r"她近期不太玩 OC，做 OC 要先讲清这群人要什么", "做 OC 要先讲清这群人要什么"),
    (r"和她认可的焦虑推演器同路", "和焦虑改写同路"),
    (r"她还提过换材质做信封或立牌", "也可以换材质做信封或立牌"),
    (r"她认可的版本：", ""),
    (r"她认可过的", ""),
    (r"交给正文和开头 bot", "可作表达方法参考"),
    (r"选题 bot 必读", ""),
    (r"已交选题", "已标为值得做"),
    (r"素材收集 bot", "素材收集"),
    (r"子代理找到[、，][^|｜]*没推", "备选条目，当时未推送"),
    (r"DDL/拼谷/约稿", "DDL 和手头事项"),
    (r"待办、拼谷、约稿、投递记录", "待办和这一年做过的事"),
    (r"10-25 唯果：低能量电量条，已标为值得做", "低能量电量条"),
    (r"10-25 唯果：低能量电量条，已交选题", "低能量电量条"),
]


def now_seoul() -> datetime:
    return datetime.now(SEOUL)


def cn_batch_num(text: str) -> int | None:
    m = re.search(r"第([一二三四五六七八九十]+)批", text)
    if not m:
        return None
    token = m.group(1)
    for name, num in CN_BATCH:
        if token == name:
            return num
    return None


def parse_date(text: str) -> str | None:
    m = re.search(r"(20\d{2})-(\d{1,2})-(\d{1,2})", text)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(?<!\d)(\d{1,2})-(\d{1,2})(?!\d)", text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return f"2026-{month:02d}-{day:02d}"
    return None


def extract_urls(text: str) -> list[str]:
    if not text:
        return []
    found = re.findall(r"https?://[^\s）)(\（】\]\[<>，,；;、\"'|｜]+", text)
    cleaned = []
    for url in found:
        url = url.rstrip("。．.,，、；;:：/）)")
        url = url.rstrip("'\"”’")
        if url.startswith("http") and "缺失" not in url:
            cleaned.append(url)
    # bare "网站 example.com" mentions recorded without a scheme
    for host in re.findall(r"(?:网站|作品|原站)\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/\S*)?)", text):
        host = host.rstrip("。．.,，、；;:：）)")
        if not host.startswith("http"):
            cleaned.append("https://" + host)
    # preserve order, drop dupes
    out, seen = [], set()
    for url in cleaned:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def link_label(url: str) -> str:
    host = urlparse(url).netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    mapping = {
        "x.com": "X",
        "twitter.com": "X",
        "github.com": "GitHub",
        "github.io": "GitHub Pages",
        "218s.cn": "风向标",
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
        "weibo.com": "微博",
        "s.weibo.com": "微博",
        "xiaohongshu.com": "小红书",
        "reddit.com": "Reddit",
        "36kr.com": "36氪",
        "huxiu.com": "虎嗅",
        "thepaper.cn": "澎湃",
        "sina.cn": "新浪",
        "sina.com.cn": "新浪",
        "koreatimes.co.kr": "Korea Times",
        "heraldcorp.com": "Herald",
        "wikipedia.org": "维基百科",
        "zh.wikipedia.org": "维基百科",
    }
    for key, label in mapping.items():
        if host == key or host.endswith("." + key):
            return label
    return host or "链接"


def split_md_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def empty_item(sid: str) -> dict:
    return {
        "id": sid,
        "batch": None,
        "date": None,
        "title": "",
        "category_codes": [],
        "category": "",
        "links": [],
        "data": "",
        "why_popular": "",
        "viewer_moment": "",
        "stage": "",
        "idea": "",
        "difficulty": "",
        "tags": [],
        "rating": "待反馈",
        "pushed": True,
        "notes": "",
        "raw_category": "",
    }


def better_text(old: str, new: str) -> str:
    old = (old or "").strip()
    new = (new or "").strip()
    if not new:
        return old
    if not old:
        return new
    if new in ("缺失", "—", "-") and old not in ("", "缺失"):
        return old
    return new if len(new) >= len(old) else old


def merge_list(old: list, new: list) -> list:
    out, seen = [], set()
    for item in list(old or []) + list(new or []):
        key = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def parse_category_codes(text: str) -> list[str]:
    if not text:
        return []
    codes = []
    for m in re.finditer(r"(?<![A-Z])([A-G])(?![A-Za-z])", text):
        if m.group(1) not in codes:
            codes.append(m.group(1))
    return codes


def parse_stage(text: str) -> str:
    if not text:
        return ""
    # Prefer an explicit arrow form
    m = re.search(r"(萌芽|爆发|衰退|常青|扩散)\s*[→~\-－]+\s*(萌芽|爆发|衰退|常青|扩散|稳定)", text)
    if m:
        return f"{m.group(1)}→{m.group(2)}"
    found = []
    for stage in STAGE_CANON:
        if stage in text:
            found.append(stage)
    if not found:
        return ""
    if "常青" in found and "衰退" in found:
        return "衰退→常青"
    return found[0]


def parse_difficulty(text: str) -> str:
    if not text:
        return ""
    m = re.search(
        r"难度[：:]?\s*(零|低到中|中到高|简单到中等|简单|中等|中低|低|中|高)"
        r"(?:[，,、 ]*(?:[12]–[123]天|[1-3]天|几天|直接用))?",
        text,
    )
    if m:
        return m.group(0).replace("难度", "").strip(" ：:")
    m = re.search(r"([12]–[123]天|[1-3]\s*天|几天)", text)
    return m.group(1) if m else ""


def parse_tags(text: str) -> list[str]:
    if not text:
        return []
    text = re.sub(r"^标签[：:]\s*", "", text.strip())
    parts = re.split(r"[、，,｜|/；;·\n]", text)
    tags = []
    for p in parts:
        p = p.strip(" []【】")
        if not p or p in {"A", "B", "C", "D", "E", "F", "G"}:
            continue
        if p.startswith("http"):
            continue
        if len(p) > 40:
            continue
        if p not in tags:
            tags.append(p)
    return tags


def extract_field(text: str, keys: list[str]) -> str:
    if not text:
        return ""
    for key in keys:
        m = re.search(rf"{key}[：:]\s*(.+?)(?=(?:观众视角|观众那一刻|火的原因|为什么火|火因|启发|具体启发|难度|标签|话题阶段|阶段)[：:]|$)", text)
        if m:
            return m.group(1).strip(" ｜|")
    return ""


def classify_pipe_parts(parts: list[str]) -> dict:
    info = {
        "title": parts[0].strip() if parts else "",
        "links_text": "",
        "data": "",
        "raw_category": "",
        "viewer_moment": "",
        "why_popular": "",
        "stage": "",
        "idea": "",
        "difficulty": "",
        "tags": [],
        "notes": "",
    }
    leftover = []
    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue
        urls = extract_urls(part)
        if urls:
            info["links_text"] = (info["links_text"] + " " + part).strip()
            remainder = part
            for url in urls:
                remainder = remainder.replace(url, " ")
            remainder = re.sub(r"(原帖|作品|来源|风向标|网站)\s*", " ", remainder)
            remainder = remainder.strip(" ：:;；,，()（）")
            # A part that is mostly a link should not also be classified as data.
            if not remainder or len(remainder) <= 12:
                continue
            part = remainder
        if part.startswith("观众视角") or part.startswith("观众那一刻"):
            info["viewer_moment"] = re.sub(r"^观众(?:视角|那一刻)[：:]\s*", "", part)
            continue
        if part.startswith("火的原因") or part.startswith("为什么火") or part.startswith("火因"):
            info["why_popular"] = re.sub(r"^(?:火的原因|为什么火|火因)[：:]\s*", "", part)
            continue
        if part.startswith("启发") or part.startswith("具体启发"):
            info["idea"] = re.sub(r"^(?:具体)?启发(?:（[^）]*）)?[：:]\s*", "", part)
            continue
        if part.startswith("难度"):
            info["difficulty"] = re.sub(r"^难度[：:]\s*", "", part)
            continue
        if part.startswith("标签"):
            info["tags"] = parse_tags(part)
            continue
        if re.search(r"(浏览|点赞|赞|收藏|star|星|转发|评论|万次|万单|多单|客单|月销|播放|热搜|GMV|收入|卖出|份|访问|美元|MRR|购买)", part) and "启发" not in part[:6]:
            if not info["data"] or len(part) > len(info["data"]):
                info["data"] = part
            continue
        if parse_category_codes(part) and len(part) <= 80:
            info["raw_category"] = part
            extra_tags = parse_tags(part)
            info["tags"] = merge_list(info["tags"], extra_tags)
            continue
        if (parse_stage(part) and len(part) <= 40 and "启发" not in part and "火因" not in part
                and "观众" not in part):
            info["stage"] = part.replace("话题阶段", "").replace("阶段", "").strip(" ：:")
            continue
        leftover.append(part)

    still = []
    for part in leftover:
        if not info["why_popular"] and re.search(r"(收藏|一秒|情绪|反差|社交)", part) and len(part) > 8:
            info["why_popular"] = part
        elif not info["idea"] and ("做" in part or "视频" in part or "小作品" in part):
            info["idea"] = part
        else:
            still.append(part)
    if still:
        info["notes"] = "；".join(still)
    return info


def apply_item_fields(item: dict, info: dict, links_from: str = "") -> None:
    if info.get("title"):
        item["title"] = better_text(item["title"], info["title"])
    links_text = info.get("links_text") or links_from or ""
    if links_text:
        item["links"] = merge_list(item["links"], extract_urls(links_text))
    if info.get("data"):
        item["data"] = better_text(item["data"], info["data"])
    if info.get("raw_category"):
        item["raw_category"] = better_text(item["raw_category"], info["raw_category"])
        item["category_codes"] = merge_list(item["category_codes"], parse_category_codes(info["raw_category"]))
    if info.get("viewer_moment"):
        item["viewer_moment"] = better_text(item["viewer_moment"], info["viewer_moment"])
    if info.get("why_popular"):
        item["why_popular"] = better_text(item["why_popular"], info["why_popular"])
    if info.get("stage"):
        item["stage"] = better_text(item["stage"], info["stage"])
    if info.get("idea"):
        item["idea"] = better_text(item["idea"], info["idea"])
    if info.get("difficulty"):
        item["difficulty"] = better_text(item["difficulty"], info["difficulty"])
    if info.get("tags"):
        item["tags"] = merge_list(item["tags"], info["tags"])
    if info.get("notes"):
        item["notes"] = better_text(item["notes"], info["notes"])


def normalize_rating(text: str) -> str:
    if not text:
        return "待反馈"
    raw = text.strip()
    if re.search(r"值得做", raw):
        return "值得做"
    if re.search(r"\bpass\b|评价一般|不吸引", raw, re.I):
        return "pass"
    if "改方向" in raw:
        return "改方向"
    if "喜欢" in raw:
        return "喜欢"
    if re.search(r"\*\*好\*\*|好，已标记|^好$|好，", raw) or raw.startswith("好"):
        return "好"
    if "待反馈" in raw or "未逐条" in raw or "未单独" in raw or "未评" in raw:
        return "待反馈"
    if raw in {"好", "喜欢", "值得做", "pass", "改方向", "待反馈"}:
        return raw
    return "待反馈"


def parse_pool(path: Path) -> dict[str, dict]:
    items: dict[str, dict] = OrderedDict()
    if not path.exists():
        return items
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    batch = None
    date = None
    pushed = True
    table_kind = "standard"
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if "没有推" in stripped or "没收的" in stripped or "没有推给她" in stripped:
            pushed = False
        if re.search(r"^#{2,3}\s+", stripped):
            maybe_batch = cn_batch_num(stripped)
            if maybe_batch:
                batch = maybe_batch
                date = parse_date(stripped) or date
            if "没有推" in stripped or "没收的" in stripped:
                pushed = False
            else:
                pushed = True
        if stripped.startswith("|") and "标题" in stripped:
            header = "".join(split_md_row(stripped))
            if "来源链接" in header and "分类" not in header:
                table_kind = "found_not_pushed"
            elif "要点" in header:
                table_kind = "method"
            else:
                table_kind = "standard"
        # table row
        mrow = re.match(r"^\|\s*(S\d{3})\s*\|", stripped)
        if mrow:
            cols = split_md_row(stripped)
            sid = mrow.group(1)
            if len(cols) >= 3 and cols[1] not in {"标题", "---", ""}:
                item = items.get(sid) or empty_item(sid)
                item["batch"] = batch or item["batch"]
                item["date"] = date or item["date"]
                item["pushed"] = False if (not pushed or table_kind == "found_not_pushed") else item.get("pushed", True)
                item["title"] = better_text(item["title"], cols[1])
                if table_kind == "found_not_pushed":
                    item["links"] = merge_list(item["links"], extract_urls(cols[2] if len(cols) > 2 else ""))
                    if len(cols) > 3:
                        item["data"] = better_text(item["data"], cols[3])
                    if len(cols) > 4:
                        note = cols[4]
                        if note.startswith("启发"):
                            item["idea"] = better_text(item["idea"], re.sub(r"^启发[：:]\s*", "", note))
                        else:
                            item["notes"] = better_text(item["notes"], note)
                        if not item["difficulty"]:
                            item["difficulty"] = parse_difficulty(note)
                    if "国外火国内未火" in item["title"] and "国外火国内未火" not in item["tags"]:
                        item["tags"] = merge_list(item["tags"], ["国外火国内未火"])
                else:
                    if len(cols) > 2:
                        item["raw_category"] = better_text(item["raw_category"], cols[2])
                        item["category_codes"] = merge_list(item["category_codes"], parse_category_codes(cols[2]))
                        item["tags"] = merge_list(item["tags"], [t for t in parse_tags(cols[2]) if t not in CATEGORY_MAP.values()])
                    if len(cols) > 3:
                        item["links"] = merge_list(item["links"], extract_urls(cols[3]))
                    if len(cols) > 4:
                        item["data"] = better_text(item["data"], cols[4])
                    if table_kind == "method":
                        if len(cols) > 5:
                            item["idea"] = better_text(item["idea"], cols[5])
                        if len(cols) > 6:
                            item["rating"] = normalize_rating(cols[6])
                    else:
                        if len(cols) > 5:
                            item["why_popular"] = better_text(item["why_popular"], cols[5])
                        if len(cols) > 6:
                            item["idea"] = better_text(item["idea"], cols[6])
                            if not item["difficulty"]:
                                item["difficulty"] = parse_difficulty(cols[6])
                        if len(cols) > 7:
                            item["rating"] = normalize_rating(cols[7])
                items[sid] = item
            i += 1
            continue
        # pipe / prose line starting with Sxxx
        mline = re.match(r"^(S\d{3})\s+(.+)$", stripped)
        if mline and "｜" in stripped:
            sid = mline.group(1)
            item = items.get(sid) or empty_item(sid)
            item["batch"] = batch or item["batch"]
            item["date"] = date or item["date"]
            item["pushed"] = True if pushed else item.get("pushed", True) and pushed
            info = classify_pipe_parts([mline.group(2)] if "｜" not in mline.group(2) else [mline.group(2).split("｜")[0]] + mline.group(2).split("｜")[1:])
            # The above split duplicates title; do it cleanly:
            parts = stripped.split("｜")
            title_part = re.sub(r"^S\d{3}\s+", "", parts[0]).strip()
            info = classify_pipe_parts([title_part] + parts[1:])
            apply_item_fields(item, info)
            # leftover urls anywhere on the line
            item["links"] = merge_list(item["links"], extract_urls(stripped))
            if not item["stage"]:
                item["stage"] = parse_stage(stripped)
            if not item["difficulty"] and item.get("idea"):
                item["difficulty"] = parse_difficulty(item["idea"])
            items[sid] = item
            i += 1
            continue
        i += 1
    return items


LABEL_MAP = {
    "分类": "raw_category",
    "来源": "links_text",
    "数据": "data",
    "为什么火": "why_popular",
    "火的原因": "why_popular",
    "火因": "why_popular",
    "观众视角": "viewer_moment",
    "观众那一刻": "viewer_moment",
    "话题阶段": "stage",
    "阶段": "stage",
    "具体启发": "idea",
    "启发": "idea",
    "作品难度": "difficulty",
    "难度": "difficulty",
    "标签": "tags_text",
    "为什么值得看": "why_popular",
    "对你自己有用": "idea",
    "要点": "idea",
}


def parse_daily_file(path: Path) -> dict[str, dict]:
    items: dict[str, dict] = OrderedDict()
    text = path.read_text(encoding="utf-8")
    batch = cn_batch_num(text)
    date = parse_date(path.name) or parse_date(text[:200])
    # split by **Sxxx or leading Sxxx lines that start a block
    pattern = re.compile(r"(?:^|\n)(?:\*\*)?(S\d{3})(?:\s+|｜)(.+?)(?=\n(?:\*\*)?S\d{3}\b|\n## |\n---|\Z)", re.S)
    for m in pattern.finditer("\n" + text):
        sid = m.group(1)
        block = m.group(2).strip()
        # stop at 未推 within block? usually after ---
        item = empty_item(sid)
        item["batch"] = batch
        item["date"] = date
        item["pushed"] = True
        first_line, _, rest = block.partition("\n")
        first_line = first_line.strip().strip("*").strip()
        # If first line is pipe-style, parse that way
        if "｜" in first_line and not first_line.startswith("-"):
            parts = [first_line.split("｜")[0]] + first_line.split("｜")[1:]
            # first_line already excludes Sxxx
            info = classify_pipe_parts(parts)
            apply_item_fields(item, info)
            item["links"] = merge_list(item["links"], extract_urls(first_line))
        else:
            item["title"] = first_line
            item["links"] = merge_list(item["links"], extract_urls(first_line))
        info = {
            "title": item["title"],
            "links_text": "",
            "data": "",
            "raw_category": "",
            "viewer_moment": "",
            "why_popular": "",
            "stage": "",
            "idea": "",
            "difficulty": "",
            "tags": [],
        }
        current_key = None
        acc = []

        def flush():
            nonlocal current_key, acc
            if not current_key:
                acc = []
                return
            value = " ".join(x.strip() for x in acc).strip()
            acc = []
            if current_key == "links_text":
                info["links_text"] = value
            elif current_key == "tags_text":
                info["tags"] = parse_tags(value)
            elif current_key in info:
                info[current_key] = value
            current_key = None

        for raw_line in rest.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            line = re.sub(r"^[-*]\s+", "", line)
            labeled = False
            for label, key in LABEL_MAP.items():
                mlab = re.match(rf"^{re.escape(label)}(?:（[^）]*）)?[：:]\s*(.*)$", line)
                if mlab:
                    flush()
                    current_key = key
                    acc = [mlab.group(1)]
                    labeled = True
                    break
            if not labeled:
                if current_key:
                    acc.append(line)
                else:
                    item["notes"] = better_text(item["notes"], line)
        flush()
        apply_item_fields(item, info)
        item["links"] = merge_list(item["links"], extract_urls(block))
        if not item["stage"]:
            item["stage"] = parse_stage(block)
        if not item["difficulty"]:
            item["difficulty"] = parse_difficulty(block)
        items[sid] = item
    return items


def merge_items(base: dict, overlay: dict) -> dict:
    if not overlay:
        return base
    out = dict(base)
    for key in ["title", "data", "why_popular", "viewer_moment", "stage", "idea", "difficulty", "raw_category", "notes"]:
        out[key] = better_text(base.get(key, ""), overlay.get(key, ""))
    out["links"] = merge_list(base.get("links"), overlay.get("links"))
    out["tags"] = merge_list(base.get("tags"), overlay.get("tags"))
    out["category_codes"] = merge_list(base.get("category_codes"), overlay.get("category_codes"))
    if overlay.get("batch") and not out.get("batch"):
        out["batch"] = overlay["batch"]
    if overlay.get("date") and not out.get("date"):
        out["date"] = overlay["date"]
    # Prefer overlay batch/date when present (daily file is dated)
    if overlay.get("batch"):
        out["batch"] = overlay["batch"]
    if overlay.get("date"):
        out["date"] = overlay["date"]
    if overlay.get("rating") and overlay["rating"] != "待反馈":
        out["rating"] = overlay["rating"]
    if overlay.get("pushed") is False:
        out["pushed"] = False
    return out


def scrub(text: str) -> str:
    if not text:
        return ""
    out = text
    for pat, repl in PRIVACY_REPLACEMENTS:
        out = re.sub(pat, repl, out)
    out = re.sub(r" +", " ", out)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip(" ；;、，,")


def derive_filters(item: dict) -> list[str]:
    chips = []
    codes = item.get("category_codes") or []
    raw = " ".join([
        item.get("raw_category") or "",
        item.get("title") or "",
        item.get("idea") or "",
        item.get("why_popular") or "",
        " ".join(item.get("tags") or []),
    ])
    if not codes:
        title = item.get("title") or ""
        if any(name in title for name in ("Dan Koe", "Hormozi", "Naval", "Paul Graham", "马斯克", "Karpathy")):
            codes.append("C")
            item["category_codes"] = merge_list(item.get("category_codes") or [], ["C"])
        elif "vibecoding" in title.lower() or "小而美" in raw or "好玩" in raw:
            codes.append("A")
            item["category_codes"] = merge_list(item.get("category_codes") or [], ["A"])
    for code in codes:
        name = CATEGORY_MAP.get(code)
        if name and name not in chips:
            chips.append(name)
    # fallback names in raw text
    mapping_words = [
        ("小而美", "小而美作品"),
        ("细分人群", "细分人群"),
        ("大佬", "大佬观点·爆款型"),
        ("爆款型", "大佬观点·爆款型"),
        ("GitHub", "GitHub对你自己有用"),
        ("对你自己有用", "GitHub对你自己有用"),
        ("求职测评可用", "求职测评可用"),
        ("二次元", "二次元"),
        ("乙女", "二次元"),
        ("同人", "二次元"),
        ("应季", "应季"),
        ("国外火国内未火", "国外火国内未火"),
        ("好玩", "好玩产品"),
    ]
    for word, chip in mapping_words:
        if word in raw and chip not in chips:
            chips.append(chip)
    # playful products: interactive toys / games / tests in A
    playful_kw = ("小游戏", "游戏", "测试", "生成器", "小工具", "网页", "App", "网站")
    if "A" in codes and any(k in (item.get("title") or "") + (item.get("idea") or "") for k in playful_kw):
        if "好玩产品" not in chips:
            chips.append("好玩产品")
    if "G" in codes and "GitHub对你自己有用" not in chips:
        chips.append("GitHub对你自己有用")
    # explicit requested aliases
    if "国外火" in raw and "国外火国内未火" not in chips:
        chips.append("国外火国内未火")
    return chips


def primary_category(item: dict) -> str:
    codes = item.get("category_codes") or []
    if codes:
        return CATEGORY_MAP.get(codes[0], codes[0])
    filters = item.get("filter_tags") or []
    return filters[0] if filters else "未分类"


def normalize_tags(item: dict) -> list[str]:
    tags = []
    noise = ("缺失", "截断", "未核验", "列表页", "标题")
    for t in item.get("tags") or []:
        t = scrub(t)
        if not t:
            continue
        t = t.replace("职迹可用", "求职测评可用")
        t = re.sub(r"^[A-G]\s+", "", t).strip()
        if not t or t in {"A", "B", "C", "D", "E", "F", "G"}:
            continue
        if any(n in t for n in noise):
            continue
        if len(t) > 28:
            continue
        if t not in tags:
            tags.append(t)
    # pull common flags from raw category / idea
    blob = " ".join([
        item.get("raw_category") or "",
        item.get("idea") or "",
        item.get("why_popular") or "",
        " ".join(item.get("filter_tags") or []),
    ])
    extras = ["应季", "求职测评可用", "国外火国内未火", "爆款型", "二次元", "低能量", "送礼"]
    for extra in extras:
        if extra in blob and extra not in tags:
            tags.append(extra)
    return tags


def links_as_objects(urls: list[str]) -> list[dict]:
    return [{"url": u, "label": link_label(u)} for u in urls]


def load_json_overlay(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def finalize(items: dict[str, dict]) -> list[dict]:
    ratings_file = load_json_overlay(DATA_DIR / "ratings.json")
    overlays_file = load_json_overlay(DATA_DIR / "overlays.json")

    finalized = []
    for sid, item in items.items():
        # repair swapped pipe fields
        data = item.get("data") or ""
        if re.match(r"^(火的原因|为什么火|火因)", data):
            if not item.get("why_popular"):
                item["why_popular"] = re.sub(r"^(?:火的原因|为什么火|火因)[：:]\s*", "", data)
            item["data"] = ""
        if re.match(r"^启发", item.get("data") or ""):
            if not item.get("idea"):
                item["idea"] = re.sub(r"^(?:具体)?启发(?:（[^）]*）)?[：:]\s*", "", item["data"])
            item["data"] = ""
        if (item.get("difficulty") or "").startswith("难度"):
            item["difficulty"] = re.sub(r"^难度[：:]?\s*", "", item["difficulty"])

        # chat overlays
        extra = {}
        extra.update(CHAT_OVERLAY.get(sid, {}))
        extra.update(overlays_file.get(sid, {}))
        for k, v in extra.items():
            if k == "links":
                item["links"] = merge_list(item["links"], v)
            elif k == "tags":
                item["tags"] = merge_list(item["tags"], v)
            elif k in item:
                item[k] = better_text(item.get(k, ""), v)

        if sid in RATING_OVERRIDE:
            item["rating"] = RATING_OVERRIDE[sid]
        if sid in ratings_file:
            item["rating"] = normalize_rating(str(ratings_file[sid]))

        # scrub textual fields
        for key in ["title", "data", "why_popular", "viewer_moment", "stage", "idea", "difficulty", "raw_category", "notes", "rating"]:
            if isinstance(item.get(key), str):
                item[key] = scrub(item[key])
        item["tags"] = [scrub(t) for t in item.get("tags") or [] if scrub(t)]

        item["filter_tags"] = derive_filters(item)
        item["tags"] = normalize_tags(item)
        item["category"] = primary_category(item)
        item["stage_norm"] = parse_stage(item.get("stage") or "") or (
            item["stage"] if item.get("stage") in STAGE_CANON else ""
        )
        if not item["stage_norm"] and item.get("stage"):
            item["stage_norm"] = parse_stage(item["stage"])
        # display stage: keep human text, but cap length
        item["links"] = links_as_objects(item.get("links") or [])
        hidden = item.get("rating") == "pass"
        item["hidden"] = hidden
        if item["rating"] not in {"值得做", "好", "喜欢", "pass", "改方向", "待反馈"}:
            item["rating"] = normalize_rating(item["rating"])

        finalized.append({
            "id": item["id"],
            "batch": item.get("batch"),
            "date": item.get("date"),
            "title": item.get("title") or item["id"],
            "category": item.get("category") or "未分类",
            "category_codes": item.get("category_codes") or [],
            "filter_tags": item.get("filter_tags") or [],
            "links": item.get("links") or [],
            "data": item.get("data") or "",
            "why_popular": item.get("why_popular") or "",
            "viewer_moment": item.get("viewer_moment") or "",
            "stage": item.get("stage") or "",
            "stage_norm": item.get("stage_norm") or "",
            "idea": item.get("idea") or "",
            "difficulty": item.get("difficulty") or "",
            "tags": item.get("tags") or [],
            "rating": item.get("rating") or "待反馈",
            "hidden": hidden,
            "pushed": bool(item.get("pushed", True)),
        })

    # newest first: by date desc, then id desc
    def sort_key(it):
        date = it.get("date") or "1970-01-01"
        batch = it.get("batch") or 0
        num = int(re.sub(r"\D", "", it["id"]) or 0)
        return (date, batch, num)

    finalized.sort(key=sort_key, reverse=True)
    return finalized


def render_materials_md(payload: dict) -> str:
    lines = [
        "# 每日灵感素材库",
        "",
        f"> 共 {payload['item_count']} 条，覆盖第 1–{payload['batch_max']} 批。生成时间：{payload['generated_at']}（Asia/Seoul）。",
        f"> 机器可读数据：[{payload['json_path']}]({payload['json_path']})",
        "",
        "本页收录已推送的公开灵感素材（小作品、人群痛点、观点帖、GitHub 工具等）。",
        "链接均为当时记录的原始来源；数据如标注「风向标自述」则未经独立核验。",
        "评价为「pass」的条目默认不出现在精选浏览里，但仍保留在数据文件中。",
        "",
    ]
    current_batch = None
    # write oldest-first for reading? site is newest-first; md can group by batch desc
    for item in payload["items"]:
        if item.get("hidden"):
            continue
        if item.get("batch") != current_batch:
            current_batch = item.get("batch")
            date = item.get("date") or ""
            lines.append(f"## 第 {current_batch} 批" + (f" · {date}" if date else ""))
            lines.append("")
        lines.append(f"### {item['id']} {item['title']}")
        meta = [
            f"批次：第 {item.get('batch') or '?'} 批",
            f"日期：{item.get('date') or '未知'}",
            f"分类：{item.get('category') or '未分类'}",
        ]
        if item.get("stage"):
            meta.append(f"阶段：{item['stage']}")
        if item.get("difficulty"):
            meta.append(f"难度：{item['difficulty']}")
        if item.get("rating") and item["rating"] != "待反馈":
            meta.append(f"评价：{item['rating']}")
        lines.append("- " + " ｜ ".join(meta))
        if item.get("tags"):
            lines.append("- 标签：" + "、".join(item["tags"]))
        if item.get("links"):
            link_s = " ； ".join(f"[{lk['label']}]({lk['url']})" for lk in item["links"])
            lines.append(f"- 来源：{link_s}")
        if item.get("data"):
            lines.append(f"- 数据：{item['data']}")
        if item.get("why_popular"):
            lines.append(f"- 为什么火：{item['why_popular']}")
        if item.get("viewer_moment"):
            lines.append(f"- 观众那一刻：{item['viewer_moment']}")
        if item.get("idea"):
            lines.append(f"- 可以做什么：{item['idea']}")
        if not item.get("pushed"):
            lines.append("- 备注：当时找到但未推送的备选")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_llms_txt(payload: dict) -> str:
    cats = "、".join(payload["categories"])
    return f"""# 每日灵感素材库

> 一套按天更新的公开灵感素材卡，方便人像刷信息流一样浏览，也方便其他 AI 直接读取。

- 生成时间：{payload['generated_at']}（Asia/Seoul）
- 条目数：{payload['item_count']}（第 1–{payload['batch_max']} 批）
- 分类：{cats}
- 结构化数据：{payload['json_abs_hint']}
- 全文 Markdown：{payload['md_abs_hint']}
- 人类浏览页：{payload['site_abs_hint']}

## 给 AI 的读法

1. 先读 `{payload['json_path']}`，按 `id`（如 S131）引用条目。
2. 需要连贯叙述时再读 `{payload['md_path']}`。
3. 每条包含：标题、批次与日期、来源链接、数据、为什么火、观众那一刻、阶段、可以做什么、难度、标签、评价。
4. `hidden=true` 或 `rating=pass` 的条目不要当作推荐。
5. 数据字段若写明「风向标自述 / 未核验 / 缺失」，不要把数字当成已核实事实。
6. 只使用条目里出现过的真实链接，不要补造来源。

## 更新

素材每天追加。重新生成方式见本仓库 README.md。
"""


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pool_path = SOURCE_DIR / "素材池_总整理.md"
    items = parse_pool(pool_path)

    for daily in sorted(SOURCE_DIR.glob("每日素材_*.md")):
        daily_items = parse_daily_file(daily)
        for sid, overlay in daily_items.items():
            if sid in items:
                items[sid] = merge_items(items[sid], overlay)
            else:
                items[sid] = overlay

    finalized = finalize(items)
    batch_nums = [it["batch"] for it in finalized if it.get("batch")]
    used_chips = []
    for chip in FILTER_CHIPS:
        if any(chip in (it.get("filter_tags") or []) or it.get("category") == chip for it in finalized):
            used_chips.append(chip)
    extra_cats = []
    for it in finalized:
        cat = it.get("category")
        if cat and cat not in used_chips and cat not in extra_cats:
            extra_cats.append(cat)

    generated_at = now_seoul().strftime("%Y-%m-%d %H:%M")
    payload = {
        "generated_at": generated_at,
        "timezone": "Asia/Seoul",
        "item_count": len(finalized),
        "visible_count": sum(1 for it in finalized if not it.get("hidden")),
        "batch_min": min(batch_nums) if batch_nums else None,
        "batch_max": max(batch_nums) if batch_nums else None,
        "categories": used_chips + extra_cats,
        "stages": STAGE_CANON,
        "json_path": "data/materials.json",
        "md_path": "materials.md",
        "json_abs_hint": "./data/materials.json",
        "md_abs_hint": "./materials.md",
        "site_abs_hint": "./index.html",
        "items": finalized,
    }

    json_path = DATA_DIR / "materials.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_text = render_materials_md(payload)
    (OUT_DIR / "materials.md").write_text(md_text, encoding="utf-8")
    (OUT_DIR / "llms.txt").write_text(render_llms_txt(payload), encoding="utf-8")

    # quick report
    missing_title = [it["id"] for it in finalized if not it["title"] or it["title"] == it["id"]]
    missing_links = [it["id"] for it in finalized if not it["links"]]
    print(f"source: {SOURCE_DIR}")
    print(f"items: {len(finalized)} (hidden/pass: {payload['item_count'] - payload['visible_count']})")
    print(f"batches: {payload['batch_min']}–{payload['batch_max']}")
    print(f"categories: {', '.join(payload['categories'])}")
    print(f"missing titles: {missing_title or 'none'}")
    print(f"no links: {missing_links or 'none'}")
    print(f"wrote {json_path}")
    print(f"wrote {OUT_DIR / 'materials.md'}")
    print(f"wrote {OUT_DIR / 'llms.txt'}")


if __name__ == "__main__":
    main()
