#!/usr/bin/env python3
"""FIN DINING 주도 섹터 코스 렌더러 — 메뉴판 커버 + 접시 5장 + 오늘의 메뉴 보드.

`render_adaptive_course.py`(v4.1)와 별개다. 그쪽은 어두운 셸 위에 아키타입을 골라 얹는 편집형이고,
이쪽은 밝은 종이 위 파인다이닝 상차림이라 배경부터 카드 구성까지 공유하는 것이 없다. 한 파일에
모드 플래그로 두 체계를 넣으면 서로를 망가뜨리므로 렌더러를 따로 둔다. 요일 브랜드 토큰
(`templates/<day>/layout.json` 의 accent 계열)은 그대로 읽어 쓴다.

## 자리는 고정이다
카드가 1080×1350 으로 고정이므로 하단(셰프·말풍선·바닥글)을 흐름에 맡기지 않고 SLOTS 의 절대 좌표에
박는다. 위 내용이 길어져도 바닥글이 프레임 밖으로 밀리지 않는다.

## 넘치면 줄인다, 자르지 않는다
접시 안 표와 말풍선 대사는 각각 `fit_rows` / `draw_rich_wrapped` 가 들어갈 크기를 찾는다. 못 찾으면
예외를 던진다. 글자가 잘리거나 겹친 채 조용히 나가는 것보다 렌더를 멈추는 편이 낫다.

    python3 templates/render_sector_course.py course-content.json 출력폴더/
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
ART = ROOT / "assets"
MANIFEST = ROOT / "templates-manifest.json"

W, H = 1080, 1350
SS = 4  # 곡선용 슈퍼샘플 배율. Pillow 는 곡선·사선을 계단으로 그린다.

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
GOLD = (195, 161, 93)
# 등락 색은 요일 브랜드 색과 분리한다. 등락은 뜻이 고정된 값이라 요일마다 색이 달라지면 의미가 흐려진다.
# 요일 accent 는 MAIN 코스 라벨·태그라인처럼 브랜드가 말하는 자리에만 쓴다.
UP = (224, 71, 58)
DOWN = (47, 111, 208)

SLOTS = {
    "safe": (100, 980),
    "head_top": 88,
    "plate_cy": 585,
    "plate_rx": 438,
    "plate_ry": 290,
    "well_inset": (70, 52),
    "cutlery_squeeze": 86,        # 식기를 세우면 접시 반지름을 이만큼 줄인다.
    "chef": (100, 1178, 300),     # x, 바닥 y, 높이
    "chef_bubble_gap": 18,
    "bubble_y": (946, 1122),
    "foot_rule_y": 1214,
    "foot_text_cy": 1254,
    "body_bottom": 900,           # 본문이 침범하면 안 되는 하단 경계(셰프 머리 위).
}

# 코스는 요리의 무게 순서 그대로 두고, 자리에 앉는 업종만 등락 순위로 정한다. 읽어 내려가면
# 4위 → 3위 → 2위 → 1위(MAIN)로 올라갔다가 5위로 가볍게 닫힌다.
# 하이픈은 Pillow 가 New York 에서 그리지 않는다(폭은 잡는데 글리프가 찍히지 않는다). 자간을 넓힌
# 대문자 조판이라 빼도 읽히므로 AMUSE BOUCHE 로 둔다.
COURSE_PLAN = [("AMUSE BOUCHE", 3), ("STARTER", 2), ("SIGNATURE", 1), ("MAIN", 0), ("DESSERT", 4)]


# ── 글꼴 ──────────────────────────────────────────────────────────────────────

def sans(size: int, weight: str = "regular"):
    return ImageFont.truetype(SANS, size=size, index={"regular": 0, "medium": 2, "semibold": 4, "bold": 6}[weight])


def serif(size: int):
    return ImageFont.truetype(SERIF, size=size)


def text_w(draw, s: str, font) -> float:
    return draw.textbbox((0, 0), s, font=font)[2]


def tracked_w(draw, s: str, font, tracking: float) -> float:
    return sum(text_w(draw, ch, font) for ch in s) + tracking * max(0, len(s) - 1)


def draw_tabular(draw, right: float, baseline: float, text: str, font, fill):
    """숫자를 등폭 슬롯에 넣어 오른쪽 끝을 맞춘다.

    Apple SD Gothic Neo 의 숫자는 폭이 제각각이라("1"이 좁다) 오른쪽 정렬만으로는 값이 세로로 늘어설 때
    끝이 들쭉날쭉해 보인다. OpenType `tnum` 은 이 Pillow 빌드에 libraqm 이 없어 못 쓴다. 대신 0~9 중
    가장 넓은 폭을 슬롯으로 삼아 숫자만 그 안에서 오른쪽에 붙인다. 부호·소수점·% 는 제 폭 그대로 둔다.
    """
    digit_w = max(text_w(draw, d, font) for d in "0123456789")
    total = sum(digit_w if ch.isdigit() else text_w(draw, ch, font) for ch in text)
    x = right - total
    for ch in text:
        if ch.isdigit():
            draw.text((x + digit_w, baseline), ch, font=font, fill=fill, anchor="rs")
            x += digit_w
        else:
            draw.text((x, baseline), ch, font=font, fill=fill, anchor="ls")
            x += text_w(draw, ch, font)
    return total


def tabular_w(draw, text: str, font) -> float:
    digit_w = max(text_w(draw, d, font) for d in "0123456789")
    return sum(digit_w if ch.isdigit() else text_w(draw, ch, font) for ch in text)


def draw_tracked(draw, xy, text: str, font, fill, tracking: float):
    """자간을 벌려 그린다. Pillow 에는 letter-spacing 이 없어 글자마다 직접 옮긴다."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += text_w(draw, ch, font) + tracking


# ── 도형 ──────────────────────────────────────────────────────────────────────

def smooth_shape(image: Image.Image, paint):
    """도형을 SS 배 크기로 그린 뒤 축소해 계단을 없앤다."""
    tile = Image.new("RGBA", (image.width * SS, image.height * SS), (0, 0, 0, 0))
    paint(ImageDraw.Draw(tile), SS)
    image.alpha_composite(tile.resize(image.size, Image.Resampling.LANCZOS))


def scallop(cx: float, cy: float, rx: float, ry: float, lobes: int = 34, depth: float = 4.5):
    """가장자리가 물결치는 타원의 꼭짓점."""
    pts = []
    for i in range(720):
        t = i * math.pi / 360
        k = 1 + depth / max(rx, ry) * math.sin(lobes * t)
        pts.append((cx + rx * k * math.cos(t), cy + ry * k * math.sin(t)))
    return pts


def draw_plate(image, cx, cy, rx, ry, well_rx, well_ry):
    """겹쳐진 링과 금색 문양 띠로 그릇을 만든다.

    테두리 한 겹짜리 타원은 그냥 도형으로 보인다. 실제 그릇이 그릇으로 읽히는 이유는 가장자리를 도는
    금선과 림 위를 도는 반복 문양이다. 바깥부터 금선 → 물결 림 → 문양 띠 → 웰 둘레 금선 → 웰 순으로 쌓는다.
    """
    band_rx, band_ry = (rx + well_rx) / 2 + 4, (ry + well_ry) / 2 + 3
    motifs = 26

    def paint(pen, s):
        def ellipse(erx, ery, **kw):
            pen.ellipse(((cx - erx) * s, (cy - ery) * s, (cx + erx) * s, (cy + ery) * s), **kw)

        pen.polygon([(px * s, py * s) for px, py in scallop(cx, cy, rx, ry)], fill=PLATE_RIM + (255,))
        ellipse(rx - 5, ry - 4, outline=GOLD + (185,), width=round(1.8 * s))
        ellipse(band_rx + 21, band_ry + 16, outline=GOLD + (95,), width=s)
        ellipse(band_rx - 21, band_ry - 16, outline=GOLD + (95,), width=s)
        for i in range(motifs):
            t = 2 * math.pi * i / motifs
            mx, my = cx + band_rx * math.cos(t), cy + band_ry * math.sin(t)
            pen.ellipse(((mx - 11) * s, (my - 11) * s, (mx + 11) * s, (my + 11) * s),
                        outline=GOLD + (170,), width=round(1.5 * s))
            t2 = 2 * math.pi * (i + 0.5) / motifs
            dx, dy = cx + band_rx * math.cos(t2), cy + band_ry * math.sin(t2)
            pen.ellipse(((dx - 2.6) * s, (dy - 2.6) * s, (dx + 2.6) * s, (dy + 2.6) * s), fill=GOLD + (190,))
        ellipse(well_rx + 10, well_ry + 8, outline=GOLD + (150,), width=round(1.4 * s))
        ellipse(well_rx, well_ry, fill=PLATE_WELL + (255,), outline=RIM_LINE + (255,), width=s)

    smooth_shape(image, paint)


def draw_cutlery(image, cy: float, height: int = 330):
    """접시 양옆의 포크와 나이프. 상차림대로 포크가 왼쪽, 나이프가 오른쪽이다.

    선으로 직접 그리면 캐릭터 일러스트와 화풍이 어긋난다. 같은 그림에서 떼어낸 컷아웃을 쓴다.
    """
    x1, x2 = SLOTS["safe"]
    for name, left in (("cutlery-fork", True), ("cutlery-knife", False)):
        art = Image.open(ART / f"{name}.png").convert("RGBA")
        art = art.resize((round(art.width * height / art.height), height), Image.Resampling.LANCZOS)
        x = x1 - 6 if left else x2 - art.width + 6
        image.alpha_composite(art, (round(x), round(cy - height / 2)))


def draw_bubble(image, box, tip_y: float, radius: int = 26, stroke: float = 1.5):
    """말풍선 몸통과 꼬리를 하나의 윤곽으로 그린다.

    둘을 따로 그리면 테두리가 맞닿는 자리에 선이 남아 꼬리가 덧붙인 삼각형처럼 보인다. 여기서는 둘을
    한 장의 마스크에 함께 칠한 뒤, 그 마스크에서 안쪽을 깎아낸 차이만 테두리로 쓴다. 합쳐진 실루엣의
    바깥선만 남으므로 이음매가 생기지 않는다.
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


# ── 배치 계산 ─────────────────────────────────────────────────────────────────

def chord_half_width(rx: float, ry: float, dy: float) -> float:
    """타원 중심에서 세로로 dy 떨어진 높이에서, 중심선부터 가장자리까지의 거리."""
    if abs(dy) >= ry:
        return 0.0
    return rx * math.sqrt(1 - (dy / ry) ** 2)


def fit_rows(draw, rows, well_rx: float, well_ry: float, pad: int = 26):
    """표가 타원 웰 안에 들어가는 가장 큰 배율을 찾아 배치를 돌려준다.

    접시는 사각형이 아니다. 어떤 높이에 놓인 줄이냐에 따라 쓸 수 있는 가로 폭(현)이 달라지고 중심에서
    멀수록 좁아진다. 눈대중으로 가운데 놓으면 첫 줄과 끝 줄이 웰 밖으로 튀어나온다. 줄마다 자기 높이의
    현을 재서 검사하고, 안 들어가면 배율을 5%씩 낮춰 다시 잰다.
    """
    # 위에서부터 내려오며 들어가는 첫 배율을 쓴다. 상한을 1 보다 크게 둔 이유는 줄 수가 적을 때다.
    # 오른 종목이 둘뿐인 업종이면 1.0 으로는 접시가 텅 비어 보인다.
    for step in range(14):
        scale = 1.25 - step * 0.05
        f_lead, f_name = sans(round(38 * scale), "bold"), sans(round(31 * scale), "semibold")
        f_price = sans(round(24 * scale))
        f_lead_pct, f_pct = sans(round(35 * scale), "bold"), sans(round(29 * scale), "semibold")
        gap, lead_gap, col_gap = round(22 * scale), round(30 * scale), round(18 * scale)

        metrics = []
        for i, row in enumerate(rows):
            fn = f_lead if not i else f_name
            fp = f_lead_pct if not i else f_pct
            ascent, descent = fn.getmetrics()
            metrics.append({
                "name_w": text_w(draw, row["name"], fn),
                "price_w": text_w(draw, row["price"], f_price),
                "pct_w": tabular_w(draw, row["pct"], fp),
                "h": ascent + descent, "ascent": ascent, "f_name": fn, "f_pct": fp,
            })
        name_col = max(m["name_w"] for m in metrics)
        price_col = max(m["price_w"] for m in metrics)
        pct_col = max(m["pct_w"] for m in metrics)
        block_w = name_col + price_col + pct_col + col_gap * 2
        block_h = sum(m["h"] for m in metrics) + gap * (len(rows) - 1) + (lead_gap - gap)

        placed, y, fits = [], -block_h / 2, True
        for i, m in enumerate(metrics):
            limit = min(chord_half_width(well_rx, well_ry, y),
                        chord_half_width(well_rx, well_ry, y + m["h"]))
            if block_w / 2 + pad > limit:
                fits = False
                break
            placed.append({"dy": y, **m})
            y += m["h"] + (lead_gap if not i else gap)
        if fits:
            return {"scale": scale, "block_w": block_w, "name_col": name_col,
                    "price_col": price_col, "pct_col": pct_col, "col_gap": col_gap,
                    "rows": placed, "f_price": f_price}
    raise ValueError("표가 접시 안에 들어가지 않는다 — 종목 수나 접시 크기를 조정해야 한다")


def draw_fitted_rows(draw, plan, cx: float, cy: float, rows):
    """fit_rows 가 잡아 준 배치대로 그린다. 세 열은 밑선을 공유한다."""
    left = cx - plan["block_w"] / 2
    price_right = left + plan["name_col"] + plan["col_gap"] + plan["price_col"]
    pct_right = price_right + plan["col_gap"] + plan["pct_col"]
    for i, placed in enumerate(plan["rows"]):
        row = rows[i]
        base = cy + placed["dy"] + placed["ascent"]  # anchor 의 s 는 baseline 을 뜻한다.
        draw.text((left, base), row["name"], font=placed["f_name"], fill=INK, anchor="ls")
        draw_tabular(draw, price_right, base, row["price"], plan["f_price"], PRICE_INK)
        draw_tabular(draw, pct_right, base, row["pct"], placed["f_pct"],
                     DOWN if row.get("down") else UP)
        if not i:
            rule_y = cy + placed["dy"] + placed["h"] + round(9 * plan["scale"])
            draw.line((left, rule_y, pct_right, rule_y), fill=RULE, width=1)


def draw_rich_wrapped(draw, segments, x: float, y: float, max_width: float, max_lines: int,
                      sizes, line_height: float = 1.54):
    """조각마다 다른 글꼴로 그리면서도 어절 단위로만 줄을 끊는다.

    한국어는 이름 뒤에 조사가 붙는다("키다리스튜디오가"). 조각 경계가 그 안에 있으므로 조각별로 줄을
    나누면 이름 한가운데가 갈라진다. 그래서 글자마다 스타일을 기억해 두고, 띄어쓰기로만 어절을 자른 뒤
    어절 안에서 다시 스타일별로 묶어 그린다.
    """
    styles = {"body": ("regular", INK), "name": ("bold", INK),
              "up": ("bold", UP), "down": ("bold", DOWN)}
    text = "".join(t for t, _ in segments)
    per_char = [st for t, st in segments for _ in t]

    for size in sizes:
        fonts = {k: sans(size, weight) for k, (weight, _) in styles.items()}
        colors = {k: color for k, (_, color) in styles.items()}

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
                while m < j and per_char[m] == per_char[k]:
                    m += 1
                pieces.append((text[k:m], per_char[k]))
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


# ── 카드 공통 ─────────────────────────────────────────────────────────────────

def new_card():
    image = Image.new("RGBA", (W, H), PAPER + (255,))
    draw = ImageDraw.Draw(image)
    draw.rectangle((46, 46, W - 47, H - 47), outline=FRAME_OUT, width=2)
    draw.rectangle((55, 55, W - 56, H - 56), outline=FRAME_IN, width=1)
    return image, draw


def draw_footer(draw, left: str, right: str):
    x1, x2 = SLOTS["safe"]
    draw.line((x1, SLOTS["foot_rule_y"], x2, SLOTS["foot_rule_y"]), fill=RULE, width=1)
    font = sans(21)
    y = SLOTS["foot_text_cy"] - 15
    draw_tracked(draw, (x1, y), left, font, MUTED, 1)
    draw_tracked(draw, (x2 - tracked_w(draw, right, font, 1), y), right, font, MUTED, 1)


def draw_chef_and_bubble(image, draw, who: str, dialogue):
    """셰프를 세우고 그 오른쪽부터 본문 오른쪽 끝까지 말풍선을 채운다.

    말풍선 왼쪽은 셰프 그림의 실제 폭에서 정한다. 캐릭터마다 폭이 달라 고정값이면 사이가 벌어진다.
    """
    x2 = SLOTS["safe"][1]
    chef_x, chef_bottom, chef_h = SLOTS["chef"]
    art = Image.open(ART / f"chef-{'bull' if who == 'BULL' else 'bear'}.png").convert("RGBA")
    art = art.resize((round(art.width * chef_h / art.height), chef_h), Image.Resampling.LANCZOS)
    image.alpha_composite(art, (chef_x, chef_bottom - chef_h))

    by1, by2 = SLOTS["bubble_y"]
    bx1 = chef_x + art.width + SLOTS["chef_bubble_gap"]
    draw_bubble(image, (bx1, by1, x2, by2), by2 - 62)
    draw_tracked(draw, (bx1 + 28, by1 + 24), f"CHEF {who}", sans(18, "medium"), MUTED, 4)
    return draw_rich_wrapped(draw, dialogue, bx1 + 28, by1 + 62, x2 - bx1 - 56, 3,
                             sizes=(26, 25, 24, 23, 22))


# ── 카드별 렌더 ───────────────────────────────────────────────────────────────

def render_cover(card: dict, cfg: dict) -> Image.Image:
    """메뉴판 커버 — 코스 다섯 줄과 두 셰프.

    다섯 줄이 헤더와 셰프 사이 영역을 넘지 않는 가장 큰 배율을 찾아 세로 가운데에 앉힌다.
    """
    image, draw = new_card()
    x1, x2 = SLOTS["safe"]
    accent = cfg["accent"]

    cx = W / 2
    top = SLOTS["head_top"]
    brand_font = sans(25, "medium")
    draw_tracked(draw, (cx - tracked_w(draw, "FINSIGHT", brand_font, 10.5) / 2, top),
                 "FINSIGHT", brand_font, MUTED, 10.5)
    house = serif(62)
    draw_tracked(draw, (cx - tracked_w(draw, "FIN DINING", house, 3.7) / 2, top + 34),
                 "FIN DINING", house, INK, 3.7)
    tag_font = sans(22, "medium")
    draw_tracked(draw, (cx - tracked_w(draw, card["tagline"], tag_font, 7) / 2, top + 118),
                 card["tagline"], tag_font, accent, 7)

    area_top, area_bottom = top + 176, SLOTS["body_bottom"]
    entries = card["courses"]
    for step in range(8):
        scale = 1.0 - step * 0.05
        f_label = serif(round(21 * scale))
        rows = []
        for entry in entries:
            main = entry["main"]
            f_name = sans(round((46 if main else 34) * scale), "semibold")
            f_pct = sans(round((39 if main else 28) * scale), "bold")
            rows.append({"label": entry["label"], "name": entry["name"], "pct": entry["pct"],
                         "main": main, "f_name": f_name, "f_pct": f_pct,
                         "h": round(f_label.size * 1.5) + round(f_name.size * 1.35)})
        pad = round(20 * scale)
        gap = round(24 * scale)
        total = sum(r["h"] + (pad * 2 if r["main"] else 0) for r in rows) + gap * (len(rows) - 1)
        if total <= area_bottom - area_top:
            break
    else:
        raise ValueError("커버 코스 목록이 카드에 들어가지 않는다")

    y = (area_top + area_bottom) / 2 - total / 2
    for row in rows:
        if row["main"]:
            draw.line((x1, y, x2, y), fill=RULE, width=1)
            y += pad
        lw = tracked_w(draw, row["label"], f_label, 6.3)
        draw_tracked(draw, (cx - lw / 2, y), row["label"], f_label,
                     accent if row["main"] else COURSE_INK, 6.3)
        line_y = y + round(f_label.size * 1.5)
        name_w = text_w(draw, row["name"], row["f_name"])
        pct_w = tabular_w(draw, row["pct"], row["f_pct"])
        span = name_w + 14 + pct_w
        ascent = row["f_name"].getmetrics()[0]
        draw.text((cx - span / 2, line_y + ascent), row["name"], font=row["f_name"], fill=INK, anchor="ls")
        draw_tabular(draw, cx - span / 2 + name_w + 14 + pct_w, line_y + ascent, row["pct"],
                     row["f_pct"], DOWN if row.get("down") else UP)
        y = line_y + round(row["f_name"].size * 1.35)
        if row["main"]:
            y += pad
            draw.line((x1, y, x2, y), fill=RULE, width=1)
        y += gap

    # 커버는 둘이 함께 나온다. 곰이 왼쪽, 황소가 오른쪽, 대사는 가운데.
    chef_x, chef_bottom, chef_h = SLOTS["chef"]
    arts = []
    for name in ("chef-bear", "chef-bull"):
        art = Image.open(ART / f"{name}.png").convert("RGBA")
        arts.append(art.resize((round(art.width * chef_h / art.height), chef_h), Image.Resampling.LANCZOS))
    image.alpha_composite(arts[0], (chef_x, chef_bottom - chef_h))
    image.alpha_composite(arts[1], (x2 - arts[1].width, chef_bottom - chef_h))

    by1, by2 = SLOTS["bubble_y"]
    bx1 = chef_x + arts[0].width + SLOTS["chef_bubble_gap"]
    bx2 = x2 - arts[1].width - SLOTS["chef_bubble_gap"]
    draw_bubble(image, (bx1, by1, bx2, by2), by2 - 62)
    draw_rich_wrapped(draw, card["dialogue"], bx1 + 26, by1 + 34, bx2 - bx1 - 52, 3,
                      sizes=(25, 24, 23, 22))

    draw_footer(draw, card["footer_left"], card["footer_right"])
    return image


def render_dish(card: dict, cfg: dict) -> Image.Image:
    """접시 카드 — 업종 하나의 대장주를 접시에 담고 셰프가 해설한다."""
    image, draw = new_card()
    x1, x2 = SLOTS["safe"]

    top = SLOTS["head_top"]
    draw_tracked(draw, (x1, top), "FIN DINING", sans(21, "medium"), MUTED, 8)
    course_font = serif(22)
    draw_tracked(draw, (x2 - tracked_w(draw, card["course"], course_font, 6.6), top - 1),
                 card["course"], course_font, COURSE_INK, 6.6)
    draw.line((x1, top + 40, x2, top + 40), fill=RULE, width=1)
    draw_tracked(draw, (x1, top + 66), card["breadth"], sans(21, "medium"), COURSE_INK, 6.6)
    draw.text((x1, top + 104), card["sector"], font=sans(50, "bold"), fill=INK)

    cy = SLOTS["plate_cy"]
    rx = SLOTS["plate_rx"] - SLOTS["cutlery_squeeze"]
    ry = SLOTS["plate_ry"]
    ix, iy = SLOTS["well_inset"]
    well_rx, well_ry = rx - ix, ry - iy
    draw_plate(image, W / 2, cy, rx, ry, well_rx, well_ry)
    draw_cutlery(image, cy)

    plan = fit_rows(draw, card["rows"], well_rx, well_ry)
    draw_fitted_rows(draw, plan, W / 2, cy, card["rows"])

    draw_chef_and_bubble(image, draw, card["chef"], card["dialogue"])
    draw_footer(draw, card["footer_left"], card["footer_right"])
    return image


def render_board(card: dict, cfg: dict) -> Image.Image:
    """오늘의 메뉴 보드 — 업종 랭킹 전체. 접시에는 열 줄이 안 올라간다.

    원 안에 열 줄을 넣으면 줄마다 쓸 수 있는 폭이 달라져 글자 크기를 맞출 수 없다. 커버가 메뉴판이면
    이 장은 메뉴 전체를 적어 둔 판이고, 접시 다섯 장이 실제로 나온 요리다.
    """
    image, draw = new_card()
    x1, x2 = SLOTS["safe"]

    top = SLOTS["head_top"]
    draw_tracked(draw, (x1, top), "FIN DINING", sans(21, "medium"), MUTED, 8)
    course_font = serif(22)
    draw_tracked(draw, (x2 - tracked_w(draw, "TODAY'S MENU", course_font, 6.6), top - 1),
                 "TODAY'S MENU", course_font, COURSE_INK, 6.6)
    draw.line((x1, top + 40, x2, top + 40), fill=RULE, width=1)
    draw_tracked(draw, (x1, top + 66), card["breadth"], sans(21, "medium"), COURSE_INK, 6.6)
    draw.text((x1, top + 104), card["title"], font=sans(50, "bold"), fill=INK)

    rows = card["rows"]
    area_top, area_bottom = top + 186, SLOTS["body_bottom"]
    for step in range(8):
        scale = 1.0 - step * 0.05
        f_rank, f_name = serif(round(20 * scale)), sans(round(33 * scale), "semibold")
        f_pct = sans(round(31 * scale), "bold")
        gap = round(24 * scale)
        line_h = round(f_name.size * 1.3)
        if len(rows) * line_h + (len(rows) - 1) * gap <= area_bottom - area_top:
            break
    else:
        raise ValueError("랭킹 보드가 카드에 들어가지 않는다")

    rank_w = max(tracked_w(draw, f"{i:02d}", f_rank, 3) for i in range(1, len(rows) + 1))
    pct_w = max(tabular_w(draw, r["pct"], f_pct) for r in rows)
    y = area_top
    for i, row in enumerate(rows, 1):
        ascent = f_name.getmetrics()[0]
        base = y + ascent
        draw_tracked(draw, (x1, y + round(f_name.size * 0.24)), f"{i:02d}", f_rank, (188, 175, 149), 3)
        name_x = x1 + rank_w + 22
        draw.text((name_x, base), row["name"], font=f_name, fill=INK, anchor="ls")
        draw_tabular(draw, x2, base, row["pct"], f_pct, DOWN if row.get("down") else UP)
        # 이름과 등락률 사이를 점선 리더로 잇는다 — 메뉴판 가격표의 어법.
        lead_x1 = name_x + text_w(draw, row["name"], f_name) + 16
        lead_x2 = x2 - pct_w - 16
        dot_y = base - round(f_name.size * 0.18)
        x = lead_x1
        while x < lead_x2:
            draw.ellipse((x, dot_y, x + 1.6, dot_y + 1.6), fill=(203, 191, 168))
            x += 9
        y += line_h + gap

    draw_chef_and_bubble(image, draw, card["chef"], card["dialogue"])
    draw_footer(draw, card["footer_left"], card["footer_right"])
    return image


RENDERERS = {"cover": render_cover, "dish": render_dish, "board": render_board}


# ── 진입점 ────────────────────────────────────────────────────────────────────

def runtime_config(day_key: str) -> dict:
    """요일 브랜드 토큰을 기존 layout.json 에서 읽는다. 색만 요일마다 달라진다."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if day_key not in manifest["templates"]:
        raise ValueError(f"unknown day_key: {day_key}")
    layout = json.loads((ROOT.parent / manifest["templates"][day_key]["layout"]).read_text(encoding="utf-8"))
    colors = layout["colors"]
    return {"accent": _hex(colors.get("accentInk", colors["accent"]))}


def _hex(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def make_preview(paths, out_dir: Path, stem: str):
    tw, th, gap = 390, 488, 28
    rows = math.ceil(len(paths) / 2)
    canvas = Image.new("RGB", (tw * 2 + gap * 3, rows * (th + 50) + gap * 2), PAPER)
    draw = ImageDraw.Draw(canvas)
    for i, path in enumerate(paths):
        canvas.paste(Image.open(path).resize((tw, th), Image.Resampling.LANCZOS),
                     (gap + (i % 2) * (tw + gap), gap + (i // 2) * (th + 50)))
        draw.text((gap + (i % 2) * (tw + gap) + tw // 2, gap + (i // 2) * (th + 50) + th + 10),
                  f"{i + 1:02d}", font=sans(24), fill=MUTED, anchor="ma")
    path = out_dir / f"{stem}_preview.png"
    canvas.save(path, "PNG", optimize=True)
    return path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: render_sector_course.py course-content.json 출력폴더")
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = runtime_config(payload["day_key"])
    stem = f'{payload["date"]}_{payload["day_key"]}'
    prefix = f'{payload["date"]}_{payload["day_key"].upper().replace("-", "_")}'

    paths = []
    for index, card in enumerate(payload["cards"], 1):
        kind = card["kind"]
        if kind not in RENDERERS:
            raise ValueError(f"알 수 없는 카드 종류: {kind}")
        image = RENDERERS[kind](card, cfg)
        path = out_dir / f"{prefix}_{index:02d}_{kind}.png"
        image.convert("RGB").save(path, "PNG", optimize=True)
        paths.append(path)

    preview = make_preview(paths, out_dir, stem)
    print(json.dumps({"images": [str(p) for p in paths], "preview": str(preview)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
