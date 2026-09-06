#!/usr/bin/env python3
"""접시 카드 Pillow 시제품 — 타원 웰 안에 표를 계산으로 앉힌다.

## 왜 계산이 필요한가
접시는 사각형이 아니다. 어떤 높이에 놓인 줄이냐에 따라 쓸 수 있는 가로 폭(현의 길이)이 달라진다.
중심에서 멀어질수록 좁아지므로, 블록을 눈대중으로 가운데 놓으면 첫 줄과 끝 줄이 웰 밖으로 튀어나온다.
`fit_rows` 가 줄마다 자기 높이에서의 현을 구해 폭을 검사하고, 안 들어가면 배율을 한 단계 낮춰
다시 잰다. 통과한 배율로만 그린다.

## 자리
카드가 1080×1350 고정이므로 하단(셰프·말풍선·바닥글)은 SLOTS 의 절대 좌표에 박는다.
위 내용이 길어져도 밀리지 않는다.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
ART = ROOT / "templates/assets"

W, H = 1080, 1350
SANS = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
SERIF = "/System/Library/Fonts/NewYork.ttf"

PAPER = (253, 250, 244)
PLATE_RIM = (247, 241, 230)
PLATE_WELL = (255, 253, 249)
RIM_LINE = (227, 217, 199)
RULE = (213, 201, 180)
FRAME_OUT = (201, 188, 164)
FRAME_IN = (216, 206, 187)
INK = (31, 27, 22)
MUTED = (154, 143, 126)
COURSE_INK = (162, 150, 127)
PRICE_INK = (107, 97, 84)
ACCENT = (176, 87, 111)
DOWN = (74, 110, 150)
GOLD = (195, 161, 93)

SLOTS = {
    "safe": (100, 980),
    "head_top": 88,
    "plate_cy": 585,
    "plate_rx": 438,
    "plate_ry": 290,
    "well_inset": (70, 52),      # 림 두께 — 가로, 세로
    "chef": (100, 1178, 300),    # x, 바닥 y, 높이
    "chef_bubble_gap": 18,       # 셰프 오른쪽 끝과 말풍선 사이
    "bubble_y": (946, 1122),     # 말풍선 위·아래. 좌우는 셰프 폭에서 계산한다.
    "foot_rule_y": 1214,
    "foot_text_cy": 1254,
}

SS = 4  # 곡선을 위한 슈퍼샘플 배율. Pillow 는 곡선을 계단으로 그린다.


def sans(size: int, weight: str = "regular"):
    return ImageFont.truetype(SANS, size=size, index={"regular": 0, "medium": 2, "semibold": 4, "bold": 6}[weight])


def serif(size: int):
    return ImageFont.truetype(SERIF, size=size)


def text_w(draw, s: str, font) -> int:
    return draw.textbbox((0, 0), s, font=font)[2]


def draw_tracked(draw, xy, text: str, font, fill, tracking: float, anchor_center: float | None = None):
    """자간을 벌려 그린다. Pillow 에는 letter-spacing 이 없어 글자마다 직접 옮긴다."""
    widths = [text_w(draw, ch, font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (anchor_center - total / 2) if anchor_center is not None else xy[0]
    for ch, cw in zip(text, widths):
        draw.text((x, xy[1]), ch, font=font, fill=fill)
        x += cw + tracking
    return total


def scallop(cx: float, cy: float, rx: float, ry: float, lobes: int = 34, depth: float = 4.5):
    """가장자리가 물결치는 타원의 꼭짓점. HTML 시안과 같은 식이다."""
    pts = []
    for i in range(720):
        t = i * math.pi / 360
        k = 1 + depth / max(rx, ry) * math.sin(lobes * t)
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    return pts


def smooth_shape(image: Image.Image, paint):
    """도형을 4배 크기로 그린 뒤 축소해 계단을 없앤다."""
    tile = Image.new("RGBA", (image.width * SS, image.height * SS), (0, 0, 0, 0))
    paint(ImageDraw.Draw(tile), SS)
    image.alpha_composite(tile.resize(image.size, Image.Resampling.LANCZOS))


def draw_plate(image, cx, cy, rx, ry, well_rx, well_ry):
    """겹쳐진 링과 금색 가장자리 선으로 그릇을 만든다.

    앞선 시안은 테두리 한 겹짜리 타원이라 그냥 도형으로 보였다. 실제 접시가 접시로 읽히는 이유는
    가장자리를 도는 금선과, 림 위에 겹쳐 도는 여러 개의 링이다. 여기서는 바깥부터
    금선 -> 물결 림 -> 안쪽 링 두 겹 -> 웰 순으로 쌓는다.
    """
    # 림 위를 도는 문양 띠 — 참조한 그릇처럼 작은 고리와 점이 번갈아 돈다. 고리는 원이라
    # 회전을 계산할 필요가 없고, 타원 둘레를 각도로 돌며 놓으면 자연스럽게 띠가 된다.
    band_rx, band_ry = (rx + well_rx) / 2 + 4, (ry + well_ry) / 2 + 3
    motifs = 26

    def paint(pen, s):
        def ellipse(erx, ery, **kw):
            pen.ellipse(((cx - erx) * s, (cy - ery) * s, (cx + erx) * s, (cy + ery) * s), **kw)

        pen.polygon([(px * s, py * s) for px, py in scallop(cx, cy, rx, ry)],
                    fill=PLATE_RIM + (255,))
        ellipse(rx - 5, ry - 4, outline=GOLD + (185,), width=round(1.8 * s))     # 가장자리 금선
        ellipse(band_rx + 21, band_ry + 16, outline=GOLD + (95,), width=s)       # 띠 바깥선
        ellipse(band_rx - 21, band_ry - 16, outline=GOLD + (95,), width=s)       # 띠 안선

        for i in range(motifs):
            t = 2 * math.pi * i / motifs
            mx, my = cx + band_rx * math.cos(t), cy + band_ry * math.sin(t)
            pen.ellipse(((mx - 11) * s, (my - 11) * s, (mx + 11) * s, (my + 11) * s),
                        outline=GOLD + (170,), width=round(1.5 * s))
            t2 = 2 * math.pi * (i + 0.5) / motifs
            dx, dy = cx + band_rx * math.cos(t2), cy + band_ry * math.sin(t2)
            pen.ellipse(((dx - 2.6) * s, (dy - 2.6) * s, (dx + 2.6) * s, (dy + 2.6) * s),
                        fill=GOLD + (190,))

        ellipse(well_rx + 10, well_ry + 8, outline=GOLD + (150,), width=round(1.4 * s))
        ellipse(well_rx, well_ry, fill=PLATE_WELL + (255,), outline=RIM_LINE + (255,), width=s)

    smooth_shape(image, paint)


def draw_cutlery(image, cy: float, height: int = 330):
    """접시 양옆의 포크와 나이프. 상차림대로 포크가 왼쪽, 나이프가 오른쪽이다.

    선으로 직접 그리면 캐릭터 일러스트와 화풍이 어긋난다. 같은 그림에서 떼어낸 컷아웃을 쓴다.
    """
    x1, x2 = SLOTS["safe"]
    for name, align_left in (("cutlery-fork", True), ("cutlery-knife", False)):
        art = Image.open(ART / f"{name}.png").convert("RGBA")
        art = art.resize((round(art.width * height / art.height), height), Image.Resampling.LANCZOS)
        x = x1 - 6 if align_left else x2 - art.width + 6
        image.alpha_composite(art, (round(x), round(cy - height / 2)))


def draw_bubble(image, box, tip_y: float, radius: int = 26, stroke: float = 1.5):
    """말풍선 몸통과 꼬리를 하나의 윤곽으로 그린다.

    둘을 따로 그리면 각자의 테두리가 맞닿는 자리에 선이 남아 꼬리가 덧붙인 삼각형처럼 보인다.
    여기서는 몸통과 꼬리를 한 장의 마스크에 함께 칠한 뒤, 그 마스크에서 안쪽을 깎아낸 차이를
    테두리로 쓴다. 합쳐진 실루엣의 바깥선만 남으므로 이음매가 생기지 않는다.
    """
    s = SS
    x1, y1, x2, y2 = box
    size = (image.width * s, image.height * s)
    mask = Image.new("L", size, 0)
    pen = ImageDraw.Draw(mask)
    pen.rounded_rectangle((x1 * s, y1 * s, x2 * s, y2 * s), radius=radius * s, fill=255)
    pen.polygon([((x1 + 6) * s, (tip_y - 20) * s), ((x1 + 6) * s, (tip_y + 20) * s),
                 ((x1 - 21) * s, tip_y * s)], fill=255)

    band = max(3, round(stroke * 2 * s) | 1)  # MinFilter 는 홀수 크기만 받는다.
    edge = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(band)))

    tile = Image.new("RGBA", size, (0, 0, 0, 0))
    tile.paste((255, 255, 255, 255), mask=mask)
    tile.paste(RIM_LINE + (255,), mask=edge)
    image.alpha_composite(tile.resize(image.size, Image.Resampling.LANCZOS))


def chord_half_width(rx: float, ry: float, dy: float) -> float:
    """타원 중심에서 세로로 dy 떨어진 높이에서, 중심선부터 가장자리까지의 거리."""
    if abs(dy) >= ry:
        return 0.0
    return rx * math.sqrt(1 - (dy / ry) ** 2)


def fit_rows(draw, rows, well_rx: float, well_ry: float, pad: int = 26):
    """줄 목록이 타원 웰 안에 들어가는 가장 큰 배율을 찾아 배치를 돌려준다.

    각 줄은 (이름, 가격, 등락률, 하락여부). 첫 줄은 대표 종목이라 한 단계 크게 그리고 아래 괘선을 둔다.
    돌려주는 값은 그릴 준비가 끝난 좌표 목록이라, 호출부는 그리기만 하면 된다.
    """
    for step in range(9):
        scale = 1.0 - step * 0.05
        f_lead, f_name = sans(round(38 * scale), "bold"), sans(round(31 * scale), "semibold")
        f_price = sans(round(24 * scale))
        f_lead_pct, f_pct = sans(round(35 * scale), "bold"), sans(round(29 * scale), "semibold")
        gap = round(22 * scale)
        lead_gap = round(30 * scale)
        col_gap = round(18 * scale)

        metrics = []
        for i, (name, price, pct, _) in enumerate(rows):
            fn = f_lead if not i else f_name
            fp = f_lead_pct if not i else f_pct
            ascent, descent = fn.getmetrics()
            metrics.append({
                "name_w": text_w(draw, name, fn), "price_w": text_w(draw, price, f_price),
                "pct_w": text_w(draw, pct, fp), "h": ascent + descent, "ascent": ascent,
                "f_name": fn, "f_pct": fp,
            })
        name_col = max(m["name_w"] for m in metrics)
        price_col = max(m["price_w"] for m in metrics)
        pct_col = max(m["pct_w"] for m in metrics)
        block_w = name_col + price_col + pct_col + col_gap * 2

        heights = [m["h"] for m in metrics]
        block_h = sum(heights) + gap * (len(rows) - 1) + (lead_gap - gap)
        top = -block_h / 2

        # 줄마다 자기 높이에서의 현을 재서, 그 줄이 웰 밖으로 나가는지 본다.
        placed, y, fits = [], top, True
        for i, m in enumerate(metrics):
            row_top, row_bottom = y, y + m["h"]
            limit = min(chord_half_width(well_rx, well_ry, row_top),
                        chord_half_width(well_rx, well_ry, row_bottom))
            if block_w / 2 + pad > limit:
                fits = False
                break
            placed.append({"dy": y, **m})
            y += m["h"] + (lead_gap if not i else gap)
        if fits:
            return {"scale": scale, "block_w": block_w, "block_h": block_h,
                    "name_col": name_col, "price_col": price_col, "pct_col": pct_col,
                    "col_gap": col_gap, "rows": placed, "f_price": f_price}
    raise ValueError("표가 접시 안에 들어가지 않는다 — 종목 수나 접시 크기를 조정해야 한다")


BUBBLE_STYLES = {
    # 스타일 이름 -> (굵기, 색). 본문은 얇게, 종목·업종명은 굵게, 수치는 굵게 + 등락 색.
    "body": ("regular", INK),
    "name": ("bold", INK),
    "up": ("bold", ACCENT),
    "down": ("bold", DOWN),
}


def draw_rich_wrapped(draw, segments, x: int, y: int, max_width: int, max_lines: int,
                      sizes, line_height: float = 1.54):
    """조각마다 다른 글꼴로 그리면서도 어절 단위로만 줄을 끊는다.

    한국어는 이름 뒤에 조사가 붙는다("키다리스튜디오가"). 조각 경계가 그 안에 있으므로 조각별로
    줄을 나누면 이름 한가운데가 갈라진다. 그래서 글자마다 스타일을 기억해 두고, 띄어쓰기로만
    어절을 자른 뒤 어절 안에서 다시 스타일별로 묶어 그린다.
    """
    text = "".join(t for t, _ in segments)
    styles = [st for t, st in segments for _ in t]

    for size in sizes:
        fonts = {k: sans(size, weight) for k, (weight, _) in BUBBLE_STYLES.items()}
        colors = {k: color for k, (_, color) in BUBBLE_STYLES.items()}

        tokens, i = [], 0
        while i < len(text):
            if text[i] == " ":
                i += 1
                continue
            j = i
            while j < len(text) and text[j] != " ":
                j += 1
            pieces, k = [], i
            while k < j:
                m = k
                while m < j and styles[m] == styles[k]:
                    m += 1
                pieces.append((text[k:m], styles[k]))
                k = m
            tokens.append(pieces)
            i = j

        space_w = text_w(draw, " ", fonts["body"])
        lines, cur, cur_w = [], [], 0.0
        for token in tokens:
            tw = sum(text_w(draw, t, fonts[st]) for t, st in token)
            add = tw + (space_w if cur else 0)
            if cur and cur_w + add > max_width:
                lines.append(cur)
                cur, cur_w = [token], tw
            else:
                cur.append(token)
                cur_w += add
        if cur:
            lines.append(cur)

        if len(lines) <= max_lines:
            step = round(size * line_height)
            for row, line in enumerate(lines):
                cx = x
                for n, token in enumerate(line):
                    if n:
                        cx += space_w
                    for t, st in token:
                        draw.text((cx, y + row * step), t, font=fonts[st], fill=colors[st])
                        cx += text_w(draw, t, fonts[st])
            return len(lines), size
    raise ValueError(f"대사가 {max_lines}줄을 넘는다: {text}")


def render(card: dict, course: str, breadth: str, who: str, line, out: Path, cutlery: bool = False):
    image = Image.new("RGBA", (W, H), PAPER + (255,))
    draw = ImageDraw.Draw(image)

    draw.rectangle((46, 46, W - 47, H - 47), outline=FRAME_OUT, width=2)
    draw.rectangle((55, 55, W - 56, H - 56), outline=FRAME_IN, width=1)

    x1, x2 = SLOTS["safe"]
    top = SLOTS["head_top"]
    draw_tracked(draw, (x1, top), "FIN DINING", sans(21, "medium"), MUTED, 8)
    course_font = serif(22)
    cw = sum(text_w(draw, ch, course_font) for ch in course) + 6.6 * (len(course) - 1)
    draw_tracked(draw, (x2 - cw, top - 1), course, course_font, COURSE_INK, 6.6)
    draw.line((x1, top + 40, x2, top + 40), fill=RULE, width=1)
    draw_tracked(draw, (x1, top + 66), breadth, sans(21, "medium"), COURSE_INK, 6.6)
    draw.text((x1, top + 104), card["headline"].replace(" 대장주", ""), font=sans(50, "bold"), fill=INK)

    cy = SLOTS["plate_cy"]
    rx = SLOTS["plate_rx"] - (86 if cutlery else 0)  # 식기를 두면 접시를 줄여 자리를 낸다.
    ry = SLOTS["plate_ry"]
    ix, iy = SLOTS["well_inset"]
    well_rx, well_ry = rx - ix, ry - iy
    draw_plate(image, W / 2, cy, rx, ry, well_rx, well_ry)
    if cutlery:
        draw_cutlery(image, cy)

    rows = [(p["label"], *p["display"].split(), p["value"] < 0) for p in card["data_points"]]
    plan = fit_rows(draw, rows, well_rx, well_ry)

    left = W / 2 - plan["block_w"] / 2
    name_x = left
    price_right = left + plan["name_col"] + plan["col_gap"] + plan["price_col"]
    pct_right = price_right + plan["col_gap"] + plan["pct_col"]
    for i, row in enumerate(plan["rows"]):
        name, price, pct, down = rows[i]
        # 셋 다 같은 밑선(baseline)에 앉힌다. anchor 의 s 는 baseline 을 뜻한다.
        base = cy + row["dy"] + row["ascent"]
        draw.text((name_x, base), name, font=row["f_name"], fill=INK, anchor="ls")
        draw.text((price_right, base), price, font=plan["f_price"], fill=PRICE_INK, anchor="rs")
        draw.text((pct_right, base), pct, font=row["f_pct"],
                  fill=DOWN if down else ACCENT, anchor="rs")
        if not i:
            rule_y = cy + row["dy"] + row["h"] + round(9 * plan["scale"])
            draw.line((name_x, rule_y, pct_right, rule_y), fill=RULE, width=1)

    chef_x, chef_bottom, chef_h = SLOTS["chef"]
    chef = Image.open(ART / f"chef-{'bull' if who == 'BULL' else 'bear'}.png").convert("RGBA")
    chef = chef.resize((round(chef.width * chef_h / chef.height), chef_h), Image.Resampling.LANCZOS)
    image.alpha_composite(chef, (chef_x, chef_bottom - chef_h))

    # 말풍선은 셰프 오른쪽부터 본문 오른쪽 끝까지 꽉 채운다.
    by1, by2 = SLOTS["bubble_y"]
    bx1 = chef_x + chef.width + SLOTS["chef_bubble_gap"]
    bx2 = x2

    draw_bubble(image, (bx1, by1, bx2, by2), by2 - 62)

    draw_tracked(draw, (bx1 + 28, by1 + 24), f"CHEF {who}", sans(18, "medium"), MUTED, 4)
    # 어절 단위로 끊고 세 줄을 넘기면 글자를 한 단계 줄인다.
    n_lines, size = draw_rich_wrapped(draw, line, bx1 + 28, by1 + 62, bx2 - bx1 - 56, 3,
                                      sizes=(26, 25, 24, 23, 22))

    draw.line((x1, SLOTS["foot_rule_y"], x2, SLOTS["foot_rule_y"]), fill=RULE, width=1)
    foot_font = sans(21)
    fy = SLOTS["foot_text_cy"] - 15
    draw_tracked(draw, (x1, fy), "2026 · 09 · 04 종가 기준", foot_font, MUTED, 1)
    right = "등락률 상위 5종목"
    rw = sum(text_w(draw, ch, foot_font) for ch in right) + 1 * (len(right) - 1)
    draw_tracked(draw, (x2 - rw, fy), right, foot_font, MUTED, 1)

    image.convert("RGB").save(out, "PNG", optimize=True)
    print(f"{out.name} · 표 배율 {plan['scale']:.2f} · 대사 {n_lines}줄 {size}px")


if __name__ == "__main__":
    data = json.loads((ROOT / "outputs/2026-09-06_sat-preview/course-content.json").read_text(encoding="utf-8"))
    render(data["cards"][3], "SIGNATURE", "25개 중 17개 상승", "BULL", [
        ("IT 서비스", "name"), (" 종목 ", "body"), ("25개", "up"), (" 가운데 ", "body"),
        ("17개", "up"), ("가 올랐어요. 그중 ", "body"), ("키다리스튜디오", "name"),
        ("가 ", "body"), ("+16.50%", "up"), ("로 가장 크게 올랐습니다.", "body"),
    ], HERE / "proto-up.png")
    render(data["cards"][6], "DESSERT", "4개 중 2개 상승", "BEAR", [
        ("통신", "name"), ("은 ", "body"), ("4개 중 2개", "down"), ("만 올랐어요. ", "body"),
        ("LG유플러스", "name"), ("는 ", "body"), ("-0.34%", "down"), ("로 혼자 내렸습니다.", "body"),
    ], HERE / "proto-down.png")
    render(data["cards"][3], "SIGNATURE", "25개 중 17개 상승", "BULL", [
        ("IT 서비스", "name"), (" 종목 ", "body"), ("25개", "up"), (" 가운데 ", "body"),
        ("17개", "up"), ("가 올랐어요. 그중 ", "body"), ("키다리스튜디오", "name"),
        ("가 ", "body"), ("+16.50%", "up"), ("로 가장 크게 올랐습니다.", "body"),
    ], HERE / "proto-up-cutlery.png", cutlery=True)
