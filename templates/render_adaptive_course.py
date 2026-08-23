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
# Opportunity/risk ink sat at 5.2:1 and 5.4:1 — AA, but washed out beside the
# 15.8:1 body text on the same card. Deepened to ~7:1 and set in medium weight.
GREEN = "#2E5540"
GREEN_BG = "#E3EDE6"
RED = "#6E3130"
RED_BG = "#F0E1E0"
OUTLINE = "#D7CBB8"

# Every approved archetype paints a fixed number of blocks. Content above the
# capacity used to be dropped by zip(); content below it raised a bare
# IndexError. Both are reported by make_plan before a pixel is rendered.
ARCHETYPE_CAPACITY = {
    "lead-plus-support": ("items", 3, 3),
    "editorial-list": ("items", 2, 4),
    "timeline-cards": ("items", 3, 3),
    "causal-flow": ("items", 3, 3),
    "stacked-insights": ("items", 2, 4),
    "audience-rows": ("items", 3, 3),
    "range-dots": ("data_points", 2, 6),
    "line-chart": ("data_points", 2, 7),
    "rank-bars": ("data_points", 2, 6),
    "calendar-grid": ("checklist", 4, 4),
    "checklist-stack": ("checklist", 3, 4),
}

# Editorial surfaces live between the course rule and the footer rule, inside
# the 72px safe margin. Nothing painted may leave this box.
SAFE_BOX = (72, 220, 1008, 1176)

def font(path: str, size: int, index: int = 0):
    return ImageFont.truetype(path, size=size, index=index)


def sans(size: int, weight: str = "regular"):
    return font(SANS, size, {"regular": 0, "medium": 2, "semibold": 4, "bold": 6}[weight])


def serif(size: int):
    return font(SERIF, size)


F_BRAND = serif(36)
F_PAGE = serif(28)
F_COVER = sans(72, "bold")
F_TITLE = sans(58, "bold")
F_H2 = sans(42, "bold")
F_BODY = sans(32, "regular")
F_SMALL = sans(30, "regular")
F_LABEL = sans(26, "semibold")
F_LEGAL = sans(24, "regular")
F_CAPSULE = sans(30, "medium")
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


SHAPE_SS = 4  # supersample factor; Pillow antialiases neither curves nor diagonals


def _smooth(image: Image.Image, box, paint):
    """Render one shape on a supersampled tile and composite it down.

    Pillow's ellipse and rounded_rectangle step their curved edges, which is
    plainly visible on a 68px badge. Only the shape's own bounding box is
    supersampled, so this costs a small transient tile rather than a 4x canvas.
    """
    pad = 2
    x0, y0 = math.floor(box[0]) - pad, math.floor(box[1]) - pad
    x1, y1 = math.ceil(box[2]) + pad + 1, math.ceil(box[3]) + pad + 1
    tile = Image.new("RGBA", ((x1 - x0) * SHAPE_SS, (y1 - y0) * SHAPE_SS), (0, 0, 0, 0))
    paint(ImageDraw.Draw(tile), (
        (box[0] - x0) * SHAPE_SS, (box[1] - y0) * SHAPE_SS,
        (box[2] - x0) * SHAPE_SS, (box[3] - y0) * SHAPE_SS,
    ))
    image.alpha_composite(tile.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), (x0, y0))


def smooth_ellipse(image: Image.Image, box, fill=None, outline=None, width=1):
    _smooth(image, box, lambda pen, scaled: pen.ellipse(
        scaled, fill=fill, outline=outline, width=width * SHAPE_SS))


def smooth_rounded(image: Image.Image, box, radius, fill=None, outline=None, width=1):
    _smooth(image, box, lambda pen, scaled: pen.rounded_rectangle(
        scaled, radius=radius * SHAPE_SS, fill=fill, outline=outline, width=width * SHAPE_SS))


ARROW_SS = SHAPE_SS
ARROW_STEPS = 72  # bezier samples


def bezier(p0, p1, p2, steps=ARROW_STEPS):
    return [(
        (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
        (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1],
    ) for t in (i / steps for i in range(steps + 1))]


def draw_arrow(image: Image.Image, start, end, fill, width=3, head_length=26, head_width=13, bow=0.18):
    """Draw a bowed, tapered connector with a slim head.

    The shaft is a quadratic bezier bowed upward off the chord, so it leaves a
    card flat and dives into the next one, rather than sagging out of it.

    A quadratic bezier's tangent at t=1 is exactly P2-P1, so the head is built
    on that vector and its axis is tangent to the curve at the tip by
    construction. The shaft is drawn the whole way to the tip and the head is
    painted over it, which leaves no joint to misalign. Rendered on a
    supersampled tile of the curve's bounding box, since Pillow does not
    antialias diagonals.
    """
    dx, dy = end[0] - start[0], end[1] - start[1]
    chord = math.hypot(dx, dy)
    if chord <= head_length:
        raise ValueError(f"arrow is too short: {start} -> {end}")
    ux, uy = dx / chord, dy / chord
    px, py = -uy, ux
    if py > 0:  # bow upward whichever way the connector runs
        px, py = -px, -py
    control = ((start[0] + end[0]) / 2 + px * chord * bow,
               (start[1] + end[1]) / 2 + py * chord * bow)
    curve = bezier(start, control, end)

    tx, ty = end[0] - control[0], end[1] - control[1]
    tangent = math.hypot(tx, ty)
    hux, huy = tx / tangent, ty / tangent
    hpx, hpy = -huy, hux
    base = (end[0] - hux * head_length, end[1] - huy * head_length)
    left = (base[0] + hpx * head_width / 2, base[1] + hpy * head_width / 2)
    right = (base[0] - hpx * head_width / 2, base[1] - hpy * head_width / 2)

    pad = head_width + width + 4
    xs = [pt[0] for pt in curve]
    ys = [pt[1] for pt in curve]
    x0, y0 = math.floor(min(xs) - pad), math.floor(min(ys) - pad)
    x1, y1 = math.ceil(max(xs) + pad), math.ceil(max(ys) + pad)
    tile = Image.new("RGBA", ((x1 - x0) * ARROW_SS, (y1 - y0) * ARROW_SS), (0, 0, 0, 0))
    pen = ImageDraw.Draw(tile)

    def at(point):
        return ((point[0] - x0) * ARROW_SS, (point[1] - y0) * ARROW_SS)

    edge_left, edge_right = [], []
    for i, point in enumerate(curve):
        ahead = curve[1] if i == 0 else point
        behind = point if i == 0 else curve[i - 1]
        sx, sy = ahead[0] - behind[0], ahead[1] - behind[1]
        span = math.hypot(sx, sy) or 1.0
        nx, ny = -sy / span, sx / span
        half = width * (0.35 + 0.15 * i / (len(curve) - 1))
        edge_left.append((point[0] + nx * half, point[1] + ny * half))
        edge_right.append((point[0] - nx * half, point[1] - ny * half))
    pen.polygon([at(pt) for pt in edge_left + edge_right[::-1]], fill=fill)
    pen.polygon((at(end), at(left), at(right)), fill=fill)
    image.alpha_composite(tile.resize((x1 - x0, y1 - y0), Image.Resampling.LANCZOS), (x0, y0))

    ex, ey = curve[-1][0] - curve[-2][0], curve[-1][1] - curve[-2][1]
    end_span = math.hypot(ex, ey) or 1.0
    tangent_cosine = (ex * hux + ey * huy) / end_span
    hx, hy = end[0] - base[0], end[1] - base[1]
    head_axis_length = math.hypot(hx, hy)
    cross_error = hux * hy - huy * hx
    alignment_cosine = (hux * hx + huy * hy) / head_axis_length
    return {
        "start": [round(start[0]), round(start[1])],
        "control": [round(control[0], 2), round(control[1], 2)],
        "base": [round(base[0], 2), round(base[1], 2)],
        "tip": [round(end[0]), round(end[1])],
        "direction": [round(hux, 4), round(huy, 4)],
        "bow": bow,
        "head_length": head_length,
        "head_width": head_width,
        "cross_error": round(cross_error, 8),
        "alignment_cosine": round(alignment_cosine, 8),
        "tangent_cosine": round(tangent_cosine, 8),
        "aligned": abs(cross_error) < 1e-6 and alignment_cosine > 0.9999 and tangent_cosine > 0.9999,
    }


def _pack_lines(draw: ImageDraw.ImageDraw, chunks, font_obj, max_width: int):
    lines, current = [], ""
    for chunk in chunks:
        trial = chunk if not current else f"{current} {chunk}"
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = chunk
    if current:
        lines.append(current)
    return lines


def wrap_text(draw: ImageDraw.ImageDraw, value: str, font_obj, max_width: int, max_lines: int | None = None):
    """Wrap copy, breaking after a separator when the copy is a list of items.

    `A · B · C` reads badly when the break lands mid-item and strands two
    syllables on the second line. Breaking after the separator keeps each item
    whole. Skipped when that would leave a stub line, so `기회 · <long>` does
    not put `기회` alone on line one.
    """
    text = str(value)
    if not text.split():
        return ""
    lines = _pack_lines(draw, text.split(), font_obj, max_width)
    chunks = re.split(r"(?<=[·,])\s+", text)
    if len(chunks) > 1:
        by_item = _pack_lines(draw, chunks, font_obj, max_width)
        stub = any(draw.textbbox((0, 0), line, font=font_obj)[2] < max_width * 0.4
                   for line in by_item[:-1])
        if len(by_item) <= len(lines) and not stub:
            lines = by_item
    if max_lines and len(lines) > max_lines:
        raise ValueError(f"copy exceeds {max_lines} lines: {value}")
    return "\n".join(lines)


def draw_centered(draw: ImageDraw.ImageDraw, center, text: str, font_obj, fill, spacing=8, align="left"):
    """Center text on its real ink box and return that box.

    Pillow's "mm" anchor centers on the font's ascender/descender box, not on
    the glyph ink, so text without descenders (digits, checkmarks, bullets)
    lands 1-2px high inside a circle or badge.
    """
    multiline = "\n" in text
    box = (draw.multiline_textbbox((0, 0), text, font=font_obj, spacing=spacing, align=align)
           if multiline else draw.textbbox((0, 0), text, font=font_obj))
    x = center[0] - (box[0] + box[2]) / 2
    y = center[1] - (box[1] + box[3]) / 2
    if multiline:
        draw.multiline_text((x, y), text, font=font_obj, fill=fill, spacing=spacing, align=align)
    else:
        draw.text((x, y), text, font=font_obj, fill=fill)
    return (x + box[0], y + box[1], x + box[2], y + box[3])


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
            variant, reason = "audience-rows", "one row per audience keeps opportunity and risk comparable"
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
        self.audit = {"version": "4.1", "records": [], "arrows": [], "blocks": [], "marks": [], "charts": [], "errors": [], "pages": []}

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

    def register_mark(self, name: str, box):
        """Track a foreground shape whose position comes from the data.

        Fixed geometry is verified once by eye and then never moves. A chart
        mark moves with every day's numbers, so it is the only thing that can
        land on a label without anyone noticing.
        """
        box = tuple(round(v) for v in box)
        self.audit["marks"].append({"page": self.current_page, "name": name, "box": list(box)})

    def label(self, draw, page, name, xy, text, font_obj, fill, container, anchor=None):
        """Draw a single-line label and record its real ink box."""
        text = str(text)
        box = draw.textbbox(xy, text, font=font_obj, anchor=anchor)
        draw.text(xy, text, font=font_obj, fill=fill, anchor=anchor)
        self.record(page, name, box, container)
        return box

    def check_collisions(self, page: int):
        blocks = [item for item in self.audit["blocks"] if item["page"] == page]
        for item in blocks:
            box = item["box"]
            if not (box[0] >= SAFE_BOX[0] and box[1] >= SAFE_BOX[1] and box[2] <= SAFE_BOX[2] and box[3] <= SAFE_BOX[3]):
                self.audit["errors"].append(
                    f'page {page} block {item["name"]} breaks the safe area: {box} vs {list(SAFE_BOX)}'
                )
        def hits(a, b):
            return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]

        surfaces = [(item["name"], tuple(item["box"])) for item in blocks if item["collide"]]
        for index, (name_a, a) in enumerate(surfaces):
            for name_b, b in surfaces[index + 1:]:
                if hits(a, b):
                    self.audit["errors"].append(
                        f"page {page} block {name_a} overlaps {name_b}: {list(a)} vs {list(b)}"
                    )
        # Data-driven marks must not land on any recorded text. Badge glyphs sit
        # inside their mark on purpose, but those go through draw_centered and
        # never reach records, so this needs no exception list.
        marks = [item for item in self.audit["marks"] if item["page"] == page]
        for text in (item for item in self.audit["records"] if item["page"] == page):
            for mark in marks:
                if hits(tuple(text["bbox"]), tuple(mark["box"])):
                    self.audit["errors"].append(
                        f'page {page} text {text["name"]} is covered by mark {mark["name"]}: '
                        f'{text["bbox"]} vs {mark["box"]}'
                    )

    def draw_wrapped(self, draw, page, name, xy, value, font_obj, fill, max_width, max_lines, container, spacing=8, vcenter=False):
        """Draw wrapped copy and record its box.

        vcenter drops the block on the container's vertical centre using the
        real ink height, so a one-line card no longer sits high in a box sized
        for three.
        """
        rendered = wrap_text(draw, value, font_obj, max_width, max_lines)
        x, y = xy
        if vcenter:
            ink = draw.multiline_textbbox((x, 0), rendered, font=font_obj, spacing=spacing)
            y = (container[1] + container[3]) / 2 - (ink[1] + ink[3]) / 2
        draw.multiline_text((x, y), rendered, font=font_obj, fill=fill, spacing=spacing)
        bbox = draw.multiline_textbbox((x, y), rendered, font=font_obj, spacing=spacing)
        self.record(page, name, bbox, container)
        return bbox

    def draw_stack(self, draw, page, name, box, parts, gap=16):
        """Draw stacked runs of copy centred as one block inside box.

        A date line above its body has to be centred as a unit; centring each
        run against the same container just stacks them on top of each other.
        """
        rendered, total = [], 0.0
        for suffix, text, font_obj, fill, max_lines in parts:
            lines = wrap_text(draw, text, font_obj, box[2] - box[0], max_lines)
            ink = draw.multiline_textbbox((0, 0), lines, font=font_obj, spacing=8)
            rendered.append((suffix, lines, font_obj, fill, ink))
            total += ink[3] - ink[1]
        total += gap * (len(rendered) - 1)
        top = (box[1] + box[3]) / 2 - total / 2
        for suffix, lines, font_obj, fill, ink in rendered:
            height = ink[3] - ink[1]
            draw.multiline_text((box[0], top - ink[1]), lines, font=font_obj, fill=fill, spacing=8)
            self.record(page, f"{name}_{suffix}", (box[0] + ink[0], top, box[0] + ink[2], top + height), box)
            top += height + gap

    def paper_card(self, image, box, radius=20, fill=PAPER, name=None):
        self.register_block(name or f'card_{len(self.audit["blocks"])}', box)
        x1, y1, x2, y2 = box
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle((x1, y1 + 8, x2, y2 + 8), radius=radius, fill=(0, 0, 0, 58))
        image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
        smooth_rounded(image, box, radius, fill=fill, outline=OUTLINE, width=1)

    def base(self, page: int, total: int):
        image = Image.new("RGBA", (W, H), BG)
        add_micro_grain(image)
        draw = ImageDraw.Draw(image)
        draw.text((72, 76), "FIN DINING", font=F_BRAND, fill=IVORY)
        draw.text((72, 118), "by Finsight", font=F_LEGAL, fill=MUTED)
        draw.line((72, 151, 1008, 151), fill=GOLD, width=2)
        draw.text((72, 181), self.cfg["course"], font=F_PAGE, fill=self.cfg["accent"])
        # layout label is `ENGLISH · 한글` saying the same thing twice; keep the
        # English and spend the space on the period the course actually covers.
        label = self.cfg["label"].split("·")[0].strip()
        period = self.payload.get("period")
        draw.text((1008, 181), f"{label} · {period}" if period else label,
                  font=F_LEGAL, fill=IVORY, anchor="ra")
        draw.line((72, 1176, 1008, 1176), fill="#3B352E", width=2)
        draw.text((72, 1214), f'{self.payload["date"]} · KST', font=F_LEGAL, fill=MUTED)
        draw.text((1008, 1214), f"{page:02d} / {total:02d}", font=F_PAGE, fill=self.cfg["accent"], anchor="ra")
        draw.text((72, 1270), "정보 제공 목적이며 특정 종목의 매수·매도를 권유하지 않습니다.", font=F_LEGAL, fill=MUTED)
        for y in range(208, 1120, 88):
            for x in range(730, 1008, 38):
                draw.ellipse((x, y, x + 3, y + 3), fill="#574D43")
        return image, draw

    def page_heading(self, draw, page, card):
        """Optional eyebrow above the headline, then the headline.

        The eyebrow is the card's actual subject, written by the author. A
        generic role label (`숫자`, `결론`) only repeats what the headline
        already says, so a card with nothing specific to add omits it and the
        headline takes the space instead.
        """
        eyebrow = card.get("eyebrow")
        if eyebrow:
            self.draw_wrapped(draw, page, "eyebrow", (72, 244), eyebrow,
                              F_LABEL, self.cfg["accent"], 900, 1, (72, 234, 1008, 278))
        top = 282 if eyebrow else 246
        for title_font in (F_TITLE, sans(54, "bold"), sans(50, "bold")):
            try:
                rendered = wrap_text(draw, card["headline"], title_font, 900, 2)
                bbox = draw.multiline_textbbox((72, top), rendered, font=title_font, spacing=8)
                if bbox[3] <= 378:
                    draw.multiline_text((72, top), rendered, font=title_font, fill=IVORY, spacing=8)
                    self.record(page, "headline", bbox, (72, top - 12, 1008, 384))
                    return
            except ValueError:
                continue
        raise ValueError(f"headline cannot fit page {page}: {card['headline']}")

    def draw_date_rail(self, image, draw, page, points):
        """Cover visual drawn from the deck's own dates.

        The weekday hero asset is fixed, so it says nothing about the day's
        story. When the cover carries a `visual` block the right column becomes
        a rail of the week's dates instead, which is the story for a preview
        course. Decorative-only shapes are not allowed here (rule 5.1), so this
        renders content or nothing.
        """
        if not 2 <= len(points) <= 4:
            raise ValueError(f"date rail needs 2 to 4 points on page {page}")
        rail_x, gap = 606, 152
        top = 235 + (845 - (len(points) - 1) * gap) / 2
        draw.line((rail_x, top, rail_x, top + (len(points) - 1) * gap), fill="#4A4138", width=2)
        for index, point in enumerate(points):
            y = top + index * gap
            focus = bool(point.get("focus"))
            radius = 15 if focus else 9
            if focus:
                smooth_ellipse(image, (rail_x - 27, y - 27, rail_x + 27, y + 27), outline=self.cfg["accent2"], width=2)
            smooth_ellipse(image, (rail_x - radius, y - radius, rail_x + radius, y + radius),
                           fill=self.cfg["accent"] if focus else MUTED)
            self.draw_wrapped(draw, page, f"rail_date_{index}", (rail_x + 52, y - 40), point["date"],
                              serif(42), self.cfg["accent"] if focus else IVORY, 330, 1, (rail_x + 45, y - 54, 1008, y + 16))
            self.draw_wrapped(draw, page, f"rail_label_{index}", (rail_x + 52, y + 18), point["label"],
                              F_SMALL, IVORY if focus else MUTED, 330, 2, (rail_x + 45, y + 12, 1008, y + 92))

    def draw_cover(self, image, draw, page, card, variant):
        if variant == "split-hero":
            if "visual" in card:
                self.draw_date_rail(image, draw, page, card["visual"]["points"])
            else:
                smooth_ellipse(image, (615, 270, 1015, 670), fill="#1D1A17", outline="#4A4138", width=2)
                paste_contain(image, Image.open(self.cfg["hero"]), (520, 235, 1040, 1080))
            self.draw_wrapped(draw, page, "eyebrow", (72, 244), card["eyebrow"], F_LABEL, self.cfg["accent"], 430, 2, (72, 230, 500, 300))
            self.draw_wrapped(draw, page, "cover_headline", (72, 318), card["headline"], F_COVER, IVORY, 500, 3, (72, 300, 560, 575), 10)
            bbox = self.draw_wrapped(draw, page, "subheadline", (72, 605), card["subheadline"], F_BODY, IVORY, 455, 2, (72, 590, 530, 690))
            # Rule underlines the copy it emphasises, so it tracks its width
            draw.line((72, bbox[3] + 34, bbox[2], bbox[3] + 34), fill=self.cfg["accent"], width=4)
        else:
            self.draw_wrapped(draw, page, "eyebrow", (72, 250), card["eyebrow"], F_LABEL, self.cfg["accent"], 850, 2, (72, 235, 1008, 300))
            self.draw_wrapped(draw, page, "cover_headline", (72, 335), card["headline"], F_COVER, IVORY, 900, 3, (72, 315, 1008, 610), 10)
            self.draw_wrapped(draw, page, "subheadline", (72, 690), card["subheadline"], F_BODY, MUTED, 750, 2, (72, 670, 900, 780))

    def draw_summary(self, image, draw, page, card, variant):
        items = card["items"]
        if variant == "lead-plus-support":
            lead = (72, 400, 1008, 625)
            self.register_block("summary_lead", lead)
            smooth_rounded(image, lead, 24, fill=self.cfg["accentInk"])
            # Same number-left, copy-right structure as 02 and 03. The old
            # `01 · LEAD` was serif English in accent2 on accentInk, which read
            # as decoration at roughly 2:1 contrast.
            draw.text((110, 445), "01", font=F_NUMBER, fill=PAPER)
            self.draw_wrapped(draw, page, "summary_1", (200, 455), items[0], F_H2, PAPER, 730, 2, (190, 440, 970, 600), 9, vcenter=True)
            for index, (item, box) in enumerate(zip(items[1:], ((72, 660, 1008, 810), (72, 842, 1008, 992))), 2):
                self.paper_card(image, box, 18, name=f"summary_card_{index}")
                draw.text((110, box[1] + 45), f"0{index}", font=F_NUMBER, fill=self.cfg["accentInk"])
                self.draw_wrapped(draw, page, f"summary_{index}", (200, box[1] + 43), item, F_BODY, INK, 750, 3, (190, box[1] + 25, 970, box[3] - 20), vcenter=True)
        else:
            line_counts = [max(1, math.ceil(len(item) / 28)) for item in items]
            heights = [120 + min(lines, 3) * 22 for lines in line_counts]
            gap = 24
            y = 405
            for index, (item, height) in enumerate(zip(items, heights), 1):
                box = (72, y, 1008, y + height)
                self.paper_card(image, box, 18, name=f"summary_card_{index}")
                draw.text((110, y + 42), f"0{index}", font=F_NUMBER, fill=self.cfg["accentInk"])
                self.draw_wrapped(draw, page, f"summary_{index}", (200, y + 40), item, F_BODY, INK, 750, 3, (190, y + 20, 970, y + height - 20), vcenter=True)
                y += height + gap

    def draw_event(self, image, draw, page, card, variant):
        y_positions = (412, 610, 808)
        for index, (item, y) in enumerate(zip(card["items"], y_positions), 1):
            box = (120, y, 1008, y + 158)
            badge = (box[0] - 48, y + 45, box[0] + 20, y + 113)
            self.paper_card(image, box, 18, name=f"event_card_{index}")
            self.register_block(f"event_badge_{index}", badge, collide=False)
            smooth_rounded(image, badge, 34, fill=self.cfg["accentInk"])
            draw_centered(draw, (box[0] - 14, y + 79), f"{index:02d}", F_LEGAL, PAPER)
            head, _, body = str(item).partition("·")
            head, body = head.strip(), body.strip()
            if body:
                self.draw_stack(draw, page, f"event_{index}", (box[0] + 52, y + 16, box[2] - 25, y + 142),
                                [("when", head, F_LABEL, self.cfg["accentInk"], 1),
                                 ("body", body, F_BODY, INK, 2)])
            else:
                self.draw_wrapped(draw, page, f"event_{index}", (box[0] + 52, y + 40), item, F_BODY, INK, box[2] - box[0] - 90, 3, (box[0] + 45, y + 24, box[2] - 25, y + 138), vcenter=True)
            if index < len(card["items"]):
                draw.line((106, y + 113, 106, y + 243), fill=self.cfg["accent"], width=3)

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
            self.draw_wrapped(draw, page, f"insight_{index}", (200, y + 38), item, F_BODY, INK, 750, 3, (190, y + 20, 970, y + height - 20), vcenter=True)
            y += height + gap

    def draw_reason(self, image, draw, page, card, variant):
        nodes = [(72, 410, 870, 555), (210, 620, 1008, 765), (72, 830, 870, 975)]
        for index, (item, box) in enumerate(zip(card["items"], nodes), 1):
            self.paper_card(image, box, 18, name=f"reason_card_{index}")
            smooth_ellipse(image, (box[0] + 28, box[1] + 43, box[0] + 88, box[1] + 103), fill=self.cfg["accentInk"])
            draw_centered(draw, (box[0] + 58, box[1] + 73), str(index), F_LABEL, PAPER)
            self.draw_wrapped(draw, page, f"reason_{index}", (box[0] + 120, box[1] + 38), item, F_BODY, INK, box[2] - box[0] - 155, 3, (box[0] + 110, box[1] + 22, box[2] - 24, box[3] - 20), vcenter=True)
            if index < 3:
                start_x = box[2] - 55 if index == 1 else box[0] + 55
                end_x = 910 if index == 1 else 160
                arrow = draw_arrow(
                    image,
                    (start_x, box[3] + 16),
                    (end_x, box[3] + 53),
                    self.cfg["accent"],
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
        # The value column sits at a fixed right edge; measure the widest number
        # and stop the track clear of it, so a max-value mark can never land on
        # its own label. record() cannot catch that: the mark is not a block.
        # A chart alone does not say what to make of it; reserve a strip for the
        # author's one-line reading when the card supplies one.
        takeaway = card.get("takeaway")
        chart_bottom, chart_height = 1010, 300
        row_gap = min(82, (chart_bottom - 604) // max(1, len(points) - 1))
        value_right = 980
        value_left = value_right - max(
            draw.textbbox((0, 0), str(point["display"]), font=F_LABEL)[2] for point in points)
        track_right = value_left - 28
        low, high = min(values), max(values)
        span = high - low or 1.0
        if variant == "range-dots":
            axis_left, axis_right = 310, track_right - 13  # keep the dot radius clear
            top = 550
            draw.line((axis_left, 525, axis_right, 525), fill=OUTLINE, width=3)
            self.label(draw, page, "axis_min", (axis_left, 510), f"MIN {low:g}", F_LEGAL, MUTED, box, "ms")
            self.label(draw, page, "axis_max", (axis_right, 510), f"MAX {high:g}", F_LEGAL, MUTED, box, "ms")
            for index, (point, value) in enumerate(zip(points, values)):
                y = top + index * row_gap
                x = axis_left + round((value - low) / span * (axis_right - axis_left))
                self.label(draw, page, f"chart_label_{index}", (122, y), point["label"], F_LABEL, INK, box)
                draw.line((axis_left, y + 20, axis_right, y + 20), fill="#E4DCCE", width=8)
                dot = (x - 13, y + 7, x + 13, y + 33)
                self.register_mark(f"dot_{index}", dot)
                smooth_ellipse(image, dot, fill=self.cfg["accentInk"])
                self.label(draw, page, f"chart_value_{index}", (value_right, y), point["display"], F_LABEL, self.cfg["accentInk"], box, "ra")
        elif variant == "line-chart":
            if len(points) < 2:
                raise ValueError(f"line chart needs at least two points on page {page}")
            xs = [180 + i * (720 / (len(points) - 1)) for i in range(len(points))]
            plotted = []
            for x, point, value in zip(xs, points, values):
                y = round(chart_bottom - 120 - ((value - low) / span) * chart_height)
                plotted.append((x, y))
                self.label(draw, page, f"chart_label_{point['label']}", (x, chart_bottom - 85), point["label"], F_LABEL, INK, box, "ma")
                self.label(draw, page, f"chart_value_{point['label']}", (x, y - 28), point["display"], F_LABEL, self.cfg["accentInk"], box, "ms")
            draw.line(plotted, fill=self.cfg["accentInk"], width=8, joint="curve")
            for index, (x, y) in enumerate(plotted):
                node = (x - 10, y - 10, x + 10, y + 10)
                self.register_mark(f"node_{index}", node)
                smooth_ellipse(image, node, fill=self.cfg["accent2"])
        else:
            origin = axis_origin(low, span)
            reach = (high - origin) or 1.0
            axis_left, axis_right = 300, track_right
            bottom = 550 + (len(points) - 1) * row_gap + 42
            draw.line((axis_left, 525, axis_right, 525), fill=OUTLINE, width=3)
            self.label(draw, page, "axis_origin", (axis_left, 510), f"\uae30\uc900\uc120 {origin:g}", F_LEGAL, MUTED, box, "ls")
            self.label(draw, page, "axis_max", (axis_right, 510), f"\ucd5c\ub300 {high:g}", F_LEGAL, MUTED, box, "rs")
            draw.line((axis_left, 540, axis_left, bottom + 12), fill=OUTLINE, width=2)
            for index, (point, value) in enumerate(zip(points, values)):
                y = 550 + index * row_gap
                width = max(8, round((value - origin) / reach * (axis_right - axis_left)))
                self.label(draw, page, f"chart_label_{index}", (122, y), point["label"], F_LABEL, INK, box)
                bar = (axis_left, y, axis_left + width, y + 42)
                self.register_mark(f"bar_{index}", bar)
                smooth_rounded(image, bar, min(18, width // 2), fill=self.cfg["accentInk"])
                self.label(draw, page, f"chart_value_{index}", (value_right, y + 3), point["display"], F_LABEL, self.cfg["accentInk"], box, "ra")
            self.audit["charts"].append({"page": page, "variant": variant, "axis_origin": origin, "axis_max": high, "zero_based": origin == 0})
        if takeaway:
            # Below the paper panel, not inside it: the reading is the author's
            # voice, not part of the chart.
            smooth_rounded(image, (72, 1052, 78, 1108), 3, fill=self.cfg["accent"])
            self.draw_wrapped(draw, page, "data_takeaway", (102, 1058), takeaway,
                              F_BODY, IVORY, 900, 1, (96, 1046, 1008, 1114))

    def impact_row(self, image, draw, page, index, item, box):
        """One audience per full-width row: rank, name, then two equal columns.

        The old shape gave row one the full width and split rows two and three
        in half, so the reader had to work out whether that meant importance or
        just packing. Uniform rows carry the order in the rank badge instead.
        """
        x1, y1, x2, y2 = box
        self.paper_card(image, box, 20, name=f"impact_card_{index}")
        badge = (x1 + 26, y1 + 22, x1 + 78, y1 + 74)
        smooth_ellipse(image, badge, fill=self.cfg["accentInk"])
        draw_centered(draw, ((badge[0] + badge[2]) / 2, (badge[1] + badge[3]) / 2), f"{index:02d}", F_LEGAL, PAPER)
        self.draw_wrapped(draw, page, f"impact_name_{index}", (x1 + 98, y1 + 26), item["name"],
                          sans(36, "bold"), INK, x2 - x1 - 130, 1, (x1 + 90, y1 + 16, x2 - 22, y1 + 82))
        mid = (x1 + x2) // 2
        opp_box, risk_box = (x1 + 26, y1 + 92, mid - 8, y2 - 20), (mid + 8, y1 + 92, x2 - 26, y2 - 20)
        smooth_rounded(image, opp_box, 16, fill=GREEN_BG)
        smooth_rounded(image, risk_box, 16, fill=RED_BG)
        for name, box_, label, colour in (("opp", opp_box, f'기회 · {item["opportunity"]}', GREEN),
                                          ("risk", risk_box, f'리스크 · {item["risk"]}', RED)):
            self.draw_wrapped(draw, page, f"impact_{name}_{index}", (box_[0] + 16, box_[1] + 14), label,
                              F_CAPSULE, colour, box_[2] - box_[0] - 32, 2,
                              (box_[0] + 12, box_[1] + 8, box_[2] - 12, box_[3] - 8), vcenter=True)

    def draw_impact(self, image, draw, page, card, variant):
        items = card["items"]
        for index, item in enumerate(items, 1):
            top = 400 + (index - 1) * 210
            self.impact_row(image, draw, page, index, item, (72, top, 1008, top + 188))

    def draw_cta(self, image, draw, page, card, variant):
        if variant == "checklist-stack":
            y = 405
            for index, item in enumerate(card["checklist"], 1):
                box = (72, y, 1008, y + 120)
                self.paper_card(image, box, 18, name=f"cta_card_{index}")
                smooth_ellipse(image, (98, y + 34, 150, y + 86), fill=self.cfg["accentInk"])
                draw_centered(draw, (124, y + 60), "✓", F_LABEL, PAPER)
                self.draw_wrapped(draw, page, f"cta_item_{index}", (178, y + 36), item, F_SMALL, INK, 785, 2, (170, y + 20, 980, y + 100), vcenter=True)
                y += 140
            cta_box = (72, 985, 1008, 1085)
            self.register_block("cta_banner", cta_box)
            smooth_rounded(image, cta_box, 22, fill=self.cfg["accentInk"])
            rendered = wrap_text(draw, card["cta"], F_BODY, 820, 2)
            bbox = draw_centered(draw, (540, 1035), rendered, F_BODY, PAPER, align="center")
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
            smooth_rounded(image, (box[0] + 24, box[1] + 24, box[0] + 174, box[1] + 72), 14, fill=self.cfg["accentInk"])
            draw_centered(draw, (box[0] + 99, box[1] + 48), date, F_LEGAL, PAPER)
            self.draw_wrapped(draw, page, f"cta_item_{index}", (box[0] + 24, box[1] + 94), detail, F_SMALL, INK, box[2] - box[0] - 48, 3, (box[0] + 20, box[1] + 84, box[2] - 20, box[3] - 18))
        cta_box = (72, 862, 1008, 984)
        self.register_block("cta_banner", cta_box)
        smooth_rounded(image, cta_box, 22, fill=self.cfg["accentInk"])
        rendered = wrap_text(draw, card["cta"], F_BODY, 820, 2)
        bbox = draw_centered(draw, (540, 923), rendered, F_BODY, PAPER, align="center")
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
