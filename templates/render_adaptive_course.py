#!/usr/bin/env python3
"""FIN DINING v4 concept-locked adaptive renderer.

The brand shell and design tokens stay fixed. Card composition, geometry and
chart type are selected from approved archetypes after measuring the content.

Usage:
  python render_adaptive_course.py course-content.json output-directory
"""

from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
MANIFEST = ROOT / "templates-manifest.json"
W, H = 1080, 1350
SANS = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
SERIF = "/System/Library/Fonts/NewYork.ttf"

BG = "#131210"
PAPER = "#F8F3EA"
IVORY = "#F4EEE4"
INK = "#1C1915"
MUTED = "#B0A79B"
GOLD = "#C3A15D"
GREEN = "#416B52"
GREEN_BG = "#E8EFE9"
RED = "#8B4A49"
RED_BG = "#F2E6E5"
OUTLINE = "#D7CBB8"

PAGE_NAMES = ["cover", "summary", "event", "reason", "data", "impact", "cta"]

# Every approved archetype paints a fixed number of blocks. Content above the
# capacity used to be dropped by zip(); content below it raised a bare
# IndexError. Both are reported by make_plan before a pixel is rendered.
ARCHETYPE_CAPACITY = {
    "lead-plus-support": ("items", 3, 3),
    "editorial-list": ("items", 2, 4),
    "timeline-cards": ("items", 3, 3),
    "causal-flow": ("items", 3, 3),
    "stacked-insights": ("items", 2, 4),
    "featured-plus-grid": ("items", 3, 3),
    "range-dots": ("data_points", 2, 6),
    "line-chart": ("data_points", 2, 7),
    "rank-bars": ("data_points", 2, 6),
    "calendar-grid": ("checklist", 4, 4),
    "checklist-stack": ("checklist", 3, 4),
}

# Editorial surfaces live between the course rule and the footer rule, inside
# the 72px safe margin. Nothing painted may leave this box.
SAFE_BOX = (72, 220, 1008, 1176)

CONFIGS = {
    "mon-policy": {
        "course": "COURSE 01", "label": "POLICY · 정책",
        "accent": "#6F8FFF", "accentInk": "#3557C7", "accent2": "#AFC0FF",
        "hero": ASSETS / "fin-dining-mon-policy-hero.png",
    },
    "tue-global": {
        "course": "COURSE 02", "label": "GLOBAL · 글로벌",
        "accent": "#A68CFF", "accentInk": "#6E50C9", "accent2": "#61C6CF",
        "hero": ASSETS / "fin-dining-tue-global-hero.png",
    },
    "wed-market": {
        "course": "COURSE 03", "label": "K-MARKET · 국내시장",
        "accent": "#F07B68", "accentInk": "#B44736", "accent2": "#3AA79B",
        "hero": ASSETS / "fin-dining-wed-market-hero.png",
    },
    "thu-industry": {
        "course": "COURSE 04", "label": "INDUSTRY · 산업",
        "accent": "#E4A953", "accentInk": "#8F5D18", "accent2": "#E4C88A",
        "hero": ASSETS / "fin-dining-thu-industry-hero.png",
    },
    "fri-weekly": {
        "course": "COURSE 05", "label": "WEEKLY CLOSE · 주간결산",
        "accent": "#E0748E", "accentInk": "#97374D", "accent2": "#D9A1A8",
        "hero": ASSETS / "fin-dining-fri-weekly-hero.png",
    },
    "sat-preview": {
        "course": "COURSE 06", "label": "NEXT WEEK · 다음주",
        "accent": "#C584B2", "accentInk": "#7D466C", "accent2": "#D2A8C2",
        "hero": ASSETS / "fin-dining-sat-preview-hero.png",
    },
}


def font(path: str, size: int, index: int = 0):
    return ImageFont.truetype(path, size=size, index=index)


def sans(size: int, weight: str = "regular"):
    return font(SANS, size, {"regular": 0, "medium": 2, "semibold": 4, "bold": 6}[weight])


def serif(size: int):
    return font(SERIF, size)


F_BRAND = serif(36)
F_SECTION = serif(32)
F_PAGE = serif(28)
F_COVER = sans(72, "bold")
F_TITLE = sans(58, "bold")
F_H2 = sans(42, "bold")
F_BODY = sans(32, "regular")
F_SMALL = sans(30, "regular")
F_LABEL = sans(26, "semibold")
F_LEGAL = sans(24, "regular")
F_NUMBER = serif(46)


def add_micro_grain(image: Image.Image):
    grain = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(grain)
    for i in range(1800):
        x = (i * 73 + 17) % W
        y = (i * 151 + 29) % H
        draw.point((x, y), fill=(255, 244, 220, 7) if i % 3 else (0, 0, 0, 9))
    image.alpha_composite(grain)


def paste_contain(background: Image.Image, foreground: Image.Image, box):
    x1, y1, x2, y2 = box
    item = foreground.copy().convert("RGBA")
    ratio = min((x2 - x1) / item.width, (y2 - y1) / item.height)
    item = item.resize((round(item.width * ratio), round(item.height * ratio)), Image.Resampling.LANCZOS)
    x = round(x1 + (x2 - x1 - item.width) / 2)
    y = round(y1 + (y2 - y1 - item.height) / 2)
    background.alpha_composite(item, (x, y))


def draw_arrow(draw: ImageDraw.ImageDraw, start, end, fill, width=4, head_length=24, head_width=18):
    """Draw a shaft and arrowhead from one shared direction vector."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length <= head_length:
        raise ValueError(f"arrow is too short: {start} -> {end}")
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    base = (end[0] - ux * head_length, end[1] - uy * head_length)
    left = (base[0] + px * head_width / 2, base[1] + py * head_width / 2)
    right = (base[0] - px * head_width / 2, base[1] - py * head_width / 2)
    draw.line((start, base), fill=fill, width=width)
    draw.polygon((end, left, right), fill=fill)
    hx, hy = end[0] - base[0], end[1] - base[1]
    head_axis_length = math.hypot(hx, hy)
    cross_error = ux * hy - uy * hx
    alignment_cosine = (ux * hx + uy * hy) / head_axis_length
    return {
        "start": [round(start[0]), round(start[1])],
        "base": [round(base[0], 2), round(base[1], 2)],
        "tip": [round(end[0]), round(end[1])],
        "direction": [round(ux, 4), round(uy, 4)],
        "head_length": head_length,
        "head_width": head_width,
        "cross_error": round(cross_error, 8),
        "alignment_cosine": round(alignment_cosine, 8),
        "aligned": abs(cross_error) < 1e-6 and alignment_cosine > 0.9999,
    }


def wrap_text(draw: ImageDraw.ImageDraw, value: str, font_obj, max_width: int, max_lines: int | None = None):
    words = str(value).split()
    if not words:
        return ""
    lines, current = [], ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    if max_lines and len(lines) > max_lines:
        raise ValueError(f"copy exceeds {max_lines} lines: {value}")
    return "\n".join(lines)


def count_numbers(value: str) -> int:
    return len(re.findall(r"[-+]?\d+(?:\.\d+)?%?|\d+조|\d+억", value))


def contains_date(value: str) -> bool:
    return bool(re.search(r"\d{1,2}월|\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2}|매일", value))


def axis_origin(low: float, span: float) -> float:
    """Baseline for rank bars, snapped to a readable number and always labelled.

    Bars keep a truncated axis so index-like series stay legible, but the start
    is rounded down to a clean step and printed on the card, so bar length can
    no longer be misread as a value ratio.
    """
    raw = low - span * 0.15
    step = 10 ** math.floor(math.log10(span))
    origin = math.floor(raw / step) * step
    if low >= 0:
        origin = max(0.0, origin)
    return round(origin, 6)


def runtime_config(day_key: str) -> dict:
    """Read brand tokens from the existing weekday layout source of truth."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if day_key not in manifest["templates"]:
        raise ValueError(f"unknown day_key: {day_key}")
    entry = manifest["templates"][day_key]
    layout = json.loads((ROOT.parent / entry["layout"]).read_text(encoding="utf-8"))
    colors = layout["colors"]
    return {
        "course": layout["course"],
        "label": layout["label"],
        "accent": colors["accent"],
        "accentInk": colors.get("accentInk", colors["accent"]),
        "accent2": colors.get("accent2", colors["accent"]),
        "hero": ROOT / layout["heroAsset"],
    }


def page_slug(card: dict, index: int) -> str:
    if index == 0:
        return "cover"
    if "data_points" in card:
        return "data"
    if "checklist" in card:
        return "cta"
    if isinstance(card.get("items", [None])[0], dict):
        return "impact"
    section = card.get("section", "").upper()
    return {
        "TASTING NOTES": "summary",
        "THE EVENT": "event",
        "WHY IT MATTERS": "reason",
    }.get(section, "insight")


def make_plan(payload: dict) -> dict:
    cards = payload["cards"]
    if not 5 <= len(cards) <= 7:
        raise ValueError("v4 cards must contain 5 to 7 slides")
    planned = []
    for index, card in enumerate(cards):
        if index == 0:
            compact = len(card["headline"].replace(" ", "")) <= 16
            variant = "split-hero" if compact else "centered-editorial"
            reason = "short hook supports a split hero" if compact else "long hook needs a centered text field"
        elif "data_points" in card:
            values = [float(p["value"]) for p in card["data_points"]]
            mean = sum(abs(v) for v in values) / len(values) or 1
            relative_span = (max(values) - min(values)) / mean
            dated = all(re.search(r"\d", p["label"]) for p in card["data_points"])
            if dated and relative_span < 0.05:
                variant, reason = "range-dots", "small time-series range should not be visually exaggerated"
            elif dated:
                variant, reason = "line-chart", "ordered time labels support a line chart"
            else:
                variant, reason = "rank-bars", "categorical values support comparable bars"
        elif "checklist" in card:
            dated_count = sum(contains_date(item) for item in card["checklist"])
            variant = "calendar-grid" if dated_count >= 2 else "checklist-stack"
            reason = "dated items support a calendar grid" if dated_count >= 2 else "undated items need a checklist"
        elif isinstance(card.get("items", [None])[0], dict):
            variant, reason = "featured-plus-grid", "one featured audience and two supporting audiences create hierarchy"
        elif card.get("section", "").upper() == "TASTING NOTES":
            numeric_density = sum(count_numbers(item) for item in card["items"])
            variant = "lead-plus-support" if numeric_density >= 3 else "editorial-list"
            reason = "numeric lead deserves asymmetric emphasis" if numeric_density >= 3 else "balanced conclusions support an editorial list"
        elif any(contains_date(item) for item in card.get("items", [])):
            variant, reason = "timeline-cards", "dated facts support an ordered timeline"
        elif any("→" in item for item in card.get("items", [])):
            variant, reason = "causal-flow", "causal arrows support a connected flow"
        else:
            variant, reason = "stacked-insights", "independent facts support stacked insight cards"
        planned.append({"page": index + 1, "section": card.get("section", "COVER"), "variant": variant, "reason": reason})
    problems = []
    for card, choice in zip(cards, planned):
        capacity = ARCHETYPE_CAPACITY.get(choice["variant"])
        if capacity is None:
            continue
        key, low, high = capacity
        count = len(card.get(key, []))
        if not low <= count <= high:
            want = str(low) if low == high else f"{low}-{high}"
            problems.append(
                f'page {choice["page"]} ({choice["section"]}) {choice["variant"]} '
                f"holds {want} {key}, got {count}"
            )
    if problems:
        raise ValueError("card content does not fit the selected archetypes:\n" + "\n".join(problems))
    return {
        "version": "4.1",
        "date": payload["date"],
        "day_key": payload["day_key"],
        "slide_count": len(cards),
        "brand_constraints": {
            "canvas": [W, H], "safe_margin": 72,
            "fonts": ["New York", "Apple SD Gothic Neo"],
            "body_min": 30, "legal_min": 24,
        },
        "cards": planned,
    }


class AdaptiveRenderer:
    def __init__(self, payload: dict, plan: dict, output_dir: Path):
        self.payload = payload
        self.plan = plan
        self.output_dir = output_dir
        self.cfg = runtime_config(payload["day_key"])
        self.current_page = 0
        self.audit = {"version": "4.1", "records": [], "arrows": [], "blocks": [], "charts": [], "errors": [], "pages": []}

    def record(self, page: int, name: str, bbox, container):
        bbox = tuple(round(v) for v in bbox)
        container = tuple(round(v) for v in container)
        inside = bbox[0] >= container[0] and bbox[1] >= container[1] and bbox[2] <= container[2] and bbox[3] <= container[3]
        self.audit["records"].append({"page": page, "name": name, "bbox": list(bbox), "container": list(container), "inside": inside})
        if not inside:
            self.audit["errors"].append(f"page {page} {name} outside container: {bbox} vs {container}")

    def register_block(self, name: str, box, collide: bool = True):
        """Track a painted surface so blocks drawn on top of each other fail.

        record() only proves a text run sits inside the box it was handed. It
        cannot see a later card painted over an earlier one, or a surface that
        grew past the safe area. Marks that deliberately hang over their own
        card pass collide=False: their margins are still checked, but they are
        excluded from the pairwise test.
        """
        box = tuple(round(v) for v in box)
        self.audit["blocks"].append({"page": self.current_page, "name": name, "box": list(box), "collide": collide})

    def check_collisions(self, page: int):
        blocks = [item for item in self.audit["blocks"] if item["page"] == page]
        for item in blocks:
            box = item["box"]
            if not (box[0] >= SAFE_BOX[0] and box[1] >= SAFE_BOX[1] and box[2] <= SAFE_BOX[2] and box[3] <= SAFE_BOX[3]):
                self.audit["errors"].append(
                    f'page {page} block {item["name"]} breaks the safe area: {box} vs {list(SAFE_BOX)}'
                )
        surfaces = [(item["name"], tuple(item["box"])) for item in blocks if item["collide"]]
        for index, (name_a, a) in enumerate(surfaces):
            for name_b, b in surfaces[index + 1:]:
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    self.audit["errors"].append(
                        f"page {page} block {name_a} overlaps {name_b}: {list(a)} vs {list(b)}"
                    )

    def draw_wrapped(self, draw, page, name, xy, value, font_obj, fill, max_width, max_lines, container, spacing=8):
        rendered = wrap_text(draw, value, font_obj, max_width, max_lines)
        draw.multiline_text(xy, rendered, font=font_obj, fill=fill, spacing=spacing)
        bbox = draw.multiline_textbbox(xy, rendered, font=font_obj, spacing=spacing)
        self.record(page, name, bbox, container)
        return bbox

    def paper_card(self, image, box, radius=20, fill=PAPER, name=None):
        self.register_block(name or f'card_{len(self.audit["blocks"])}', box)
        x1, y1, x2, y2 = box
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle((x1, y1 + 8, x2, y2 + 8), radius=radius, fill=(0, 0, 0, 58))
        image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
        ImageDraw.Draw(image).rounded_rectangle(box, radius=radius, fill=fill, outline=OUTLINE, width=1)

    def base(self, page: int, total: int):
        image = Image.new("RGBA", (W, H), BG)
        add_micro_grain(image)
        draw = ImageDraw.Draw(image)
        draw.text((72, 76), "FIN DINING", font=F_BRAND, fill=IVORY)
        draw.text((72, 118), "by Finsight", font=F_LEGAL, fill=MUTED)
        draw.line((72, 151, 1008, 151), fill=GOLD, width=2)
        draw.text((72, 181), self.cfg["course"], font=F_PAGE, fill=self.cfg["accent"])
        draw.text((1008, 181), self.cfg["label"], font=F_LEGAL, fill=IVORY, anchor="ra")
        draw.line((72, 1176, 1008, 1176), fill="#3B352E", width=2)
        draw.text((72, 1214), f'{self.payload["date"]} · KST', font=F_LEGAL, fill=MUTED)
        draw.text((1008, 1214), f"{page:02d} / {total:02d}", font=F_PAGE, fill=self.cfg["accent"], anchor="ra")
        draw.text((72, 1270), "정보 제공 목적이며 특정 종목의 매수·매도를 권유하지 않습니다.", font=F_LEGAL, fill=MUTED)
        for y in range(208, 1120, 88):
            for x in range(730, 1008, 38):
                draw.ellipse((x, y, x + 3, y + 3), fill="#574D43")
        return image, draw

    def page_heading(self, draw, page, card):
        draw.text((72, 235), card["section"], font=F_SECTION, fill=self.cfg["accent"])
        for title_font in (F_TITLE, sans(54, "bold"), sans(50, "bold")):
            try:
                rendered = wrap_text(draw, card["headline"], title_font, 900, 2)
                bbox = draw.multiline_textbbox((72, 282), rendered, font=title_font, spacing=8)
                if bbox[3] <= 370:
                    draw.multiline_text((72, 282), rendered, font=title_font, fill=IVORY, spacing=8)
                    self.record(page, "headline", bbox, (72, 270, 1008, 380))
                    return
            except ValueError:
                continue
        raise ValueError(f"headline cannot fit page {page}: {card['headline']}")

    def draw_cover(self, image, draw, page, card, variant):
        if variant == "split-hero":
            hero_box = (520, 235, 1040, 1080)
            draw.ellipse((615, 270, 1015, 670), fill="#1D1A17", outline="#4A4138", width=2)
            paste_contain(image, Image.open(self.cfg["hero"]), hero_box)
            self.draw_wrapped(draw, page, "eyebrow", (72, 244), card["eyebrow"], F_LABEL, self.cfg["accent"], 430, 2, (72, 230, 500, 300))
            self.draw_wrapped(draw, page, "cover_headline", (72, 318), card["headline"], F_COVER, IVORY, 500, 3, (72, 300, 560, 575), 10)
            self.draw_wrapped(draw, page, "subheadline", (72, 605), card["subheadline"], F_BODY, MUTED, 455, 2, (72, 590, 530, 690))
            draw.line((72, 720, 382, 720), fill=self.cfg["accent"], width=4)
        else:
            self.draw_wrapped(draw, page, "eyebrow", (72, 250), card["eyebrow"], F_LABEL, self.cfg["accent"], 850, 2, (72, 235, 1008, 300))
            self.draw_wrapped(draw, page, "cover_headline", (72, 335), card["headline"], F_COVER, IVORY, 900, 3, (72, 315, 1008, 610), 10)
            self.draw_wrapped(draw, page, "subheadline", (72, 690), card["subheadline"], F_BODY, MUTED, 750, 2, (72, 670, 900, 780))

    def draw_summary(self, image, draw, page, card, variant):
        items = card["items"]
        if variant == "lead-plus-support":
            lead = (72, 400, 1008, 625)
            self.register_block("summary_lead", lead)
            draw.rounded_rectangle(lead, radius=24, fill=self.cfg["accentInk"])
            draw.text((108, 438), "01 · LEAD", font=F_SECTION, fill=self.cfg["accent2"])
            self.draw_wrapped(draw, page, "summary_1", (108, 500), items[0], F_H2, PAPER, 820, 3, (100, 485, 970, 600), 9)
            for index, (item, box) in enumerate(zip(items[1:], ((72, 660, 1008, 810), (72, 842, 1008, 992))), 2):
                self.paper_card(image, box, 18, name=f"summary_card_{index}")
                draw.text((110, box[1] + 45), f"0{index}", font=F_NUMBER, fill=self.cfg["accentInk"])
                self.draw_wrapped(draw, page, f"summary_{index}", (200, box[1] + 43), item, F_BODY, INK, 750, 3, (190, box[1] + 25, 970, box[3] - 20))
        else:
            line_counts = [max(1, math.ceil(len(item) / 28)) for item in items]
            heights = [120 + min(lines, 3) * 22 for lines in line_counts]
            gap = 24
            y = 405
            for index, (item, height) in enumerate(zip(items, heights), 1):
                box = (72, y, 1008, y + height)
                self.paper_card(image, box, 18, name=f"summary_card_{index}")
                draw.text((110, y + 42), f"0{index}", font=F_NUMBER, fill=self.cfg["accentInk"])
                self.draw_wrapped(draw, page, f"summary_{index}", (200, y + 40), item, F_BODY, INK, 750, 3, (190, y + 20, 970, y + height - 20))
                y += height + gap

    def draw_event(self, image, draw, page, card, variant):
        y_positions = (412, 610, 808)
        for index, (item, y) in enumerate(zip(card["items"], y_positions), 1):
            box = (168 if index % 2 else 120, y, 1008 if index % 2 else 960, y + 158)
            badge = (box[0] - 48, y + 45, box[0] + 20, y + 113)
            self.paper_card(image, box, 18, name=f"event_card_{index}")
            self.register_block(f"event_badge_{index}", badge, collide=False)
            draw.rounded_rectangle(badge, radius=34, fill=self.cfg["accentInk"])
            draw.text((box[0] - 14, y + 79), f"{index:02d}", font=F_LEGAL, fill=PAPER, anchor="mm")
            self.draw_wrapped(draw, page, f"event_{index}", (box[0] + 52, y + 40), item, F_BODY, INK, box[2] - box[0] - 90, 3, (box[0] + 45, y + 24, box[2] - 25, y + 138))
            if index < 3:
                draw.line((540, y + 160, 540, y + 194), fill=self.cfg["accent"], width=3)

    def draw_stacked(self, image, draw, page, card):
        """Balanced editorial cards for independent, non-causal insights."""
        items = card["items"]
        count = len(items)
        if not 2 <= count <= 4:
            raise ValueError(f"stacked insights need 2 to 4 items on page {page}")
        available, gap = 570, 24
        height = (available - gap * (count - 1)) // count
        y = 410
        for index, item in enumerate(items, 1):
            box = (72, y, 1008, y + height)
            self.paper_card(image, box, 18, name=f"insight_card_{index}")
            draw.text((110, y + 39), f"{index:02d}", font=F_NUMBER, fill=self.cfg["accentInk"])
            self.draw_wrapped(draw, page, f"insight_{index}", (200, y + 38), item, F_BODY, INK, 750, 3, (190, y + 20, 970, y + height - 20))
            y += height + gap

    def draw_reason(self, image, draw, page, card, variant):
        nodes = [(72, 410, 870, 555), (210, 620, 1008, 765), (72, 830, 870, 975)]
        for index, (item, box) in enumerate(zip(card["items"], nodes), 1):
            self.paper_card(image, box, 18, name=f"reason_card_{index}")
            draw.ellipse((box[0] + 28, box[1] + 43, box[0] + 88, box[1] + 103), fill=self.cfg["accentInk"])
            draw.text((box[0] + 58, box[1] + 73), str(index), font=F_LABEL, fill=PAPER, anchor="mm")
            self.draw_wrapped(draw, page, f"reason_{index}", (box[0] + 120, box[1] + 38), item, F_BODY, INK, box[2] - box[0] - 155, 3, (box[0] + 110, box[1] + 22, box[2] - 24, box[3] - 20))
            if index < 3:
                start_x = box[2] - 55 if index == 1 else box[0] + 55
                end_x = 910 if index == 1 else 160
                arrow = draw_arrow(
                    draw,
                    (start_x, box[3] + 16),
                    (end_x, box[3] + 53),
                    self.cfg["accent"],
                    width=4,
                    head_length=24,
                    head_width=20,
                )
                arrow.update({"page": page, "from_node": index, "to_node": index + 1})
                self.audit["arrows"].append(arrow)
                if not arrow["aligned"]:
                    self.audit["errors"].append(f"page {page} arrow {index} head is not aligned with shaft")

    def draw_data(self, image, draw, page, card, variant):
        box = (72, 400, 1008, 1010)
        self.paper_card(image, box, 20, name="data_panel")
        self.draw_wrapped(draw, page, "data_note", (112, 438), card["note"], F_BODY, INK, 830, 2, (100, 420, 980, 500))
        points = card["data_points"]
        values = [float(point["value"]) for point in points]
        low, high = min(values), max(values)
        span = high - low or 1.0
        if variant == "range-dots":
            axis_left, axis_right = 310, 900
            top, row_gap = 550, 82
            draw.line((axis_left, 525, axis_right, 525), fill=OUTLINE, width=3)
            draw.text((axis_left, 510), f"MIN {low:g}", font=F_LEGAL, fill=MUTED, anchor="ms")
            draw.text((axis_right, 510), f"MAX {high:g}", font=F_LEGAL, fill=MUTED, anchor="ms")
            for index, (point, value) in enumerate(zip(points, values)):
                y = top + index * row_gap
                x = axis_left + round((value - low) / span * (axis_right - axis_left))
                draw.text((122, y), point["label"], font=F_LABEL, fill=INK)
                draw.line((axis_left, y + 20, axis_right, y + 20), fill="#E4DCCE", width=8)
                draw.ellipse((x - 13, y + 7, x + 13, y + 33), fill=self.cfg["accentInk"])
                draw.text((940, y), point["display"], font=F_LABEL, fill=self.cfg["accentInk"], anchor="ra")
        elif variant == "line-chart":
            if len(points) < 2:
                raise ValueError(f"line chart needs at least two points on page {page}")
            xs = [180 + i * (720 / (len(points) - 1)) for i in range(len(points))]
            plotted = []
            for x, point, value in zip(xs, points, values):
                y = round(890 - ((value - low) / span) * 300)
                plotted.append((x, y))
                draw.text((x, 925), point["label"], font=F_LABEL, fill=INK, anchor="ma")
                draw.text((x, y - 28), point["display"], font=F_LABEL, fill=self.cfg["accentInk"], anchor="ms")
            draw.line(plotted, fill=self.cfg["accentInk"], width=8, joint="curve")
            for x, y in plotted:
                draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=self.cfg["accent2"])
        else:
            origin = axis_origin(low, span)
            reach = (high - origin) or 1.0
            axis_left, axis_right = 300, 900
            bottom = 550 + (len(points) - 1) * 82 + 42
            draw.line((axis_left, 525, axis_right, 525), fill=OUTLINE, width=3)
            draw.text((axis_left, 510), f"\uae30\uc900\uc120 {origin:g}", font=F_LEGAL, fill=MUTED, anchor="ls")
            draw.text((axis_right, 510), f"\ucd5c\ub300 {high:g}", font=F_LEGAL, fill=MUTED, anchor="rs")
            draw.line((axis_left, 540, axis_left, bottom + 12), fill=OUTLINE, width=2)
            for index, (point, value) in enumerate(zip(points, values)):
                y = 550 + index * 82
                width = max(8, round((value - origin) / reach * 600))
                draw.text((122, y), point["label"], font=F_LABEL, fill=INK)
                draw.rounded_rectangle((axis_left, y, axis_left + width, y + 42), radius=min(18, width // 2), fill=self.cfg["accentInk"])
                draw.text((940, y + 3), point["display"], font=F_LABEL, fill=self.cfg["accentInk"], anchor="ra")
            self.audit["charts"].append({"page": page, "variant": variant, "axis_origin": origin, "axis_max": high, "zero_based": origin == 0})

    def impact_content(self, image, draw, page, item, box, featured=False, name="impact_card"):
        x1, y1, x2, y2 = box
        self.paper_card(image, box, 20, name=name)
        draw.ellipse((x1 + 26, y1 + 26, x1 + 76, y1 + 76), fill=self.cfg["accentInk"])
        draw.text((x1 + 51, y1 + 51), "●", font=F_LEGAL, fill=PAPER, anchor="mm")
        title_font = F_H2 if featured else sans(34, "bold")
        self.draw_wrapped(draw, page, f"impact_name_{y1}", (x1 + 96, y1 + 24), item["name"], title_font, INK, x2 - x1 - 125, 2, (x1 + 88, y1 + 15, x2 - 22, y1 + 95))
        opportunity = f'기회 · {item["opportunity"]}'
        risk = f'리스크 · {item["risk"]}'
        if featured:
            opp_box, risk_box = (x1 + 26, y1 + 108, x1 + 444, y2 - 24), (x1 + 468, y1 + 108, x2 - 26, y2 - 24)
            draw.rounded_rectangle(opp_box, radius=16, fill=GREEN_BG)
            draw.rounded_rectangle(risk_box, radius=16, fill=RED_BG)
            self.draw_wrapped(draw, page, f"impact_opp_{y1}", (opp_box[0] + 16, opp_box[1] + 15), opportunity, F_SMALL, GREEN, opp_box[2] - opp_box[0] - 32, 3, (opp_box[0] + 12, opp_box[1] + 8, opp_box[2] - 12, opp_box[3] - 8))
            self.draw_wrapped(draw, page, f"impact_risk_{y1}", (risk_box[0] + 16, risk_box[1] + 15), risk, F_SMALL, RED, risk_box[2] - risk_box[0] - 32, 3, (risk_box[0] + 12, risk_box[1] + 8, risk_box[2] - 12, risk_box[3] - 8))
        else:
            opp_box, risk_box = (x1 + 24, y1 + 110, x2 - 24, y1 + 205), (x1 + 24, y1 + 222, x2 - 24, y2 - 24)
            draw.rounded_rectangle(opp_box, radius=16, fill=GREEN_BG)
            draw.rounded_rectangle(risk_box, radius=16, fill=RED_BG)
            self.draw_wrapped(draw, page, f"impact_opp_{y1}", (opp_box[0] + 14, opp_box[1] + 13), opportunity, F_SMALL, GREEN, opp_box[2] - opp_box[0] - 28, 3, (opp_box[0] + 10, opp_box[1] + 8, opp_box[2] - 10, opp_box[3] - 8))
            self.draw_wrapped(draw, page, f"impact_risk_{y1}", (risk_box[0] + 14, risk_box[1] + 13), risk, F_SMALL, RED, risk_box[2] - risk_box[0] - 28, 3, (risk_box[0] + 10, risk_box[1] + 8, risk_box[2] - 10, risk_box[3] - 8))

    def draw_impact(self, image, draw, page, card, variant):
        items = card["items"]
        self.impact_content(image, draw, page, items[0], (72, 400, 1008, 625), featured=True, name="impact_card_1")
        self.impact_content(image, draw, page, items[1], (72, 660, 524, 1010), featured=False, name="impact_card_2")
        self.impact_content(image, draw, page, items[2], (556, 660, 1008, 1010), featured=False, name="impact_card_3")

    def draw_cta(self, image, draw, page, card, variant):
        if variant == "checklist-stack":
            y = 405
            for index, item in enumerate(card["checklist"], 1):
                box = (72, y, 1008, y + 120)
                self.paper_card(image, box, 18, name=f"cta_card_{index}")
                draw.ellipse((98, y + 34, 150, y + 86), fill=self.cfg["accentInk"])
                draw.text((124, y + 60), "✓", font=F_LABEL, fill=PAPER, anchor="mm")
                self.draw_wrapped(draw, page, f"cta_item_{index}", (178, y + 36), item, F_SMALL, INK, 785, 2, (170, y + 20, 980, y + 100))
                y += 140
            cta_box = (72, 985, 1008, 1085)
            self.register_block("cta_banner", cta_box)
            draw.rounded_rectangle(cta_box, radius=22, fill=self.cfg["accentInk"])
            rendered = wrap_text(draw, card["cta"], F_BODY, 820, 2)
            bbox = draw.multiline_textbbox((540, 1035), rendered, font=F_BODY, anchor="mm", align="center", spacing=8)
            draw.multiline_text((540, 1035), rendered, font=F_BODY, fill=PAPER, anchor="mm", align="center", spacing=8)
            self.record(page, "cta", bbox, cta_box)
            sources = "출처 · " + " · ".join(card["sources"])
            self.draw_wrapped(draw, page, "sources", (72, 1105), sources, F_LABEL, MUTED, 900, 1, (72, 1095, 1008, 1155))
            return
        boxes = [(72, 405, 524, 600), (556, 405, 1008, 600), (72, 630, 524, 825), (556, 630, 1008, 825)]
        for index, (item, box) in enumerate(zip(card["checklist"], boxes), 1):
            self.paper_card(image, box, 18, name=f"cta_card_{index}")
            parts = [part.strip() for part in item.split("·", 1)]
            date = parts[0]
            detail = parts[1] if len(parts) > 1 else item
            draw.rounded_rectangle((box[0] + 24, box[1] + 24, box[0] + 174, box[1] + 72), radius=14, fill=self.cfg["accentInk"])
            draw.text((box[0] + 99, box[1] + 48), date, font=F_LEGAL, fill=PAPER, anchor="mm")
            self.draw_wrapped(draw, page, f"cta_item_{index}", (box[0] + 24, box[1] + 94), detail, F_SMALL, INK, box[2] - box[0] - 48, 3, (box[0] + 20, box[1] + 84, box[2] - 20, box[3] - 18))
        cta_box = (72, 862, 1008, 984)
        self.register_block("cta_banner", cta_box)
        draw.rounded_rectangle(cta_box, radius=22, fill=self.cfg["accentInk"])
        rendered = wrap_text(draw, card["cta"], F_BODY, 820, 2)
        bbox = draw.multiline_textbbox((540, 924), rendered, font=F_BODY, anchor="mm", align="center", spacing=8)
        draw.multiline_text((540, 924), rendered, font=F_BODY, fill=PAPER, anchor="mm", align="center", spacing=8)
        self.record(page, "cta", bbox, cta_box)
        sources = "출처 · " + " · ".join(card["sources"])
        self.draw_wrapped(draw, page, "sources", (72, 1022), sources, F_LABEL, MUTED, 900, 2, (72, 1010, 1008, 1090))

    def render(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        outputs = []
        total = len(self.payload["cards"])
        for index, (card, choice) in enumerate(zip(self.payload["cards"], self.plan["cards"]), 1):
            self.current_page = index
            image, draw = self.base(index, total)
            if index == 1:
                self.draw_cover(image, draw, index, card, choice["variant"])
            else:
                self.page_heading(draw, index, card)
                if "data_points" in card:
                    self.draw_data(image, draw, index, card, choice["variant"])
                elif "checklist" in card:
                    self.draw_cta(image, draw, index, card, choice["variant"])
                elif isinstance(card.get("items", [None])[0], dict):
                    self.draw_impact(image, draw, index, card, choice["variant"])
                elif card.get("section", "").upper() == "TASTING NOTES":
                    self.draw_summary(image, draw, index, card, choice["variant"])
                elif choice["variant"] == "timeline-cards":
                    self.draw_event(image, draw, index, card, choice["variant"])
                elif choice["variant"] == "causal-flow":
                    self.draw_reason(image, draw, index, card, choice["variant"])
                else:
                    self.draw_stacked(image, draw, index, card)
            self.check_collisions(index)
            filename = f'{self.payload["date"]}_{self.payload["day_key"].upper().replace("-", "_")}_V4_{index:02d}_{page_slug(card, index - 1)}.png'
            path = self.output_dir / filename
            image.convert("RGB").save(path, "PNG", optimize=True)
            outputs.append(path)
            self.audit["pages"].append({"page": index, "variant": choice["variant"], "file": filename})

        preview = self.make_preview(outputs)
        mobile = self.make_mobile_preview(outputs)
        self.audit["passed"] = not self.audit["errors"]
        (self.output_dir / "layout-audit.json").write_text(json.dumps(self.audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if self.audit["errors"]:
            raise ValueError("adaptive layout audit failed:\n" + "\n".join(self.audit["errors"]))
        return outputs, preview, mobile

    def make_preview(self, outputs):
        thumb_w, thumb_h = 270, 338
        preview = Image.new("RGB", (thumb_w * 4 + 36 * 5, thumb_h * 2 + 60 * 3), BG)
        for index, path in enumerate(outputs):
            image = Image.open(path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            x = 36 + (index % 4) * (thumb_w + 36)
            y = 36 + (index // 4) * (thumb_h + 60)
            preview.paste(image, (x, y))
        path = self.output_dir / f'{self.payload["date"]}_{self.payload["day_key"]}_v4_preview.png'
        preview.save(path, "PNG", optimize=True)
        return path

    def make_mobile_preview(self, outputs):
        thumb_w, thumb_h, gap = 390, 488, 28
        rows = math.ceil(len(outputs) / 2)
        canvas = Image.new("RGB", (thumb_w * 2 + gap * 3, rows * (thumb_h + 50) + gap * 2), BG)
        draw = ImageDraw.Draw(canvas)
        for index, path in enumerate(outputs):
            image = Image.open(path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            x = gap + (index % 2) * (thumb_w + gap)
            y = gap + (index // 2) * (thumb_h + 50)
            canvas.paste(image, (x, y))
            draw.text((x + thumb_w // 2, y + thumb_h + 10), f"{index + 1:02d}", font=F_LEGAL, fill=MUTED, anchor="ma")
        path = self.output_dir / f'{self.payload["date"]}_{self.payload["day_key"]}_v4_mobile390.png'
        canvas.save(path, "PNG", optimize=True)
        return path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: render_adaptive_course.py course-content.json output-directory")
    content_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    payload = json.loads(content_path.read_text(encoding="utf-8"))
    runtime_config(payload["day_key"])
    plan = make_plan(payload)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "layout-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    renderer = AdaptiveRenderer(payload, plan, output_dir)
    outputs, preview, mobile = renderer.render()
    print(json.dumps({
        "version": "4.1",
        "layout_plan": str(output_dir / "layout-plan.json"),
        "images": [str(path) for path in outputs],
        "preview": str(preview),
        "mobile_preview": str(mobile),
        "audit": str(output_dir / "layout-audit.json"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
