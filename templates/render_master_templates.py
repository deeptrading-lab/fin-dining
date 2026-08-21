from __future__ import annotations

from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
W, H = 1080, 1350
SANS = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
SERIF = "/System/Library/Fonts/NewYork.ttf"

CHARCOAL = "#131210"
IVORY = "#F4EEE4"
PAPER = "#F8F3EA"
GOLD = "#C3A15D"
MUTED = "#B0A79B"
INK = "#1C1915"


def sans(size: int, weight: str = "regular"):
    index = {"regular": 0, "medium": 2, "semibold": 4, "bold": 6}[weight]
    return ImageFont.truetype(SANS, size=size, index=index)


def serif(size: int):
    return ImageFont.truetype(SERIF, size=size)


S18 = sans(18, "medium")
S20 = sans(20, "regular")
S22 = sans(22, "medium")
S24 = sans(24, "semibold")
S24R = sans(24, "regular")
S26 = sans(26, "semibold")
S28 = sans(28, "semibold")
S30 = sans(30, "regular")
S32 = sans(32, "semibold")
S50 = sans(50, "bold")
S54 = sans(54, "bold")
S62 = sans(62, "bold")
S66 = sans(66, "bold")
R26 = serif(26)
R28 = serif(28)
R34 = serif(34)
R36 = serif(36)


CONFIGS = {
    "mon-policy": {
        "id": "fin_dining_mon_policy_v3", "course": "COURSE 01",
        "label": "POLICY · 정책", "korean": "월요일 정책 코스",
        "accent": "#6F8FFF", "accentInk": "#3557C7", "accent2": "#AFC0FF",
        "hero": ASSETS / "fin-dining-mon-policy-hero.png",
        "preview": ["정책의 한 문장이", "내 돈을 바꿉니다", "결정에서 생활 영향까지"],
    },
    "tue-global": {
        "id": "fin_dining_tue_global_v3", "course": "COURSE 02",
        "label": "GLOBAL · 글로벌", "korean": "화요일 글로벌 코스",
        "accent": "#A68CFF", "accentInk": "#6E50C9", "accent2": "#61C6CF",
        "hero": ASSETS / "fin-dining-tue-global-hero.png",
        "preview": ["밤사이 움직인 돈", "한국 시장에 닿는 길", "글로벌 사건부터 연결해서"],
    },
    "wed-market": {
        "id": "fin_dining_wed_market_v3", "course": "COURSE 03",
        "label": "K-MARKET · 국내시장", "korean": "수요일 국내시장 코스",
        "accent": "#F07B68", "accentInk": "#B44736", "accent2": "#3AA79B",
        "hero": ASSETS / "fin-dining-wed-market-hero.png",
        "preview": ["지수는 올랐는데", "내 계좌는 왜 다를까", "수급과 업종의 온도 차이"],
    },
    "thu-industry": {
        "id": "fin_dining_thu_industry_v3", "course": "COURSE 04",
        "label": "INDUSTRY · 산업", "korean": "목요일 산업 코스",
        "accent": "#E4A953", "accentInk": "#8F5D18", "accent2": "#E4C88A",
        "hero": ASSETS / "fin-dining-thu-industry-hero.png",
        "preview": ["뉴스 한 줄 뒤의", "산업 구조를 해체합니다", "밸류체인에서 기업까지"],
    },
    "fri-weekly": {
        "id": "fin_dining_fri_weekly_v3", "course": "COURSE 05",
        "label": "WEEKLY CLOSE · 주간결산", "korean": "금요일 주간결산 코스",
        "accent": "#E0748E", "accentInk": "#97374D", "accent2": "#D9A1A8",
        "hero": ASSETS / "fin-dining-fri-weekly-hero.png",
        "preview": ["이번 주 시장을", "한 접시에 정리합니다", "강했던 것과 약했던 것"],
    },
    "sat-preview": {
        "id": "fin_dining_sat_preview_v3", "course": "COURSE 06",
        "label": "NEXT WEEK · 다음주", "korean": "토요일 다음주 코스",
        "accent": "#C584B2", "accentInk": "#7D466C", "accent2": "#D2A8C2",
        "hero": ASSETS / "fin-dining-sat-preview-hero.png",
        "preview": ["다음 주 시장의", "예약표를 먼저 봅니다", "일정과 시나리오를 차분하게"],
    },
}

PAGE_NAMES = ["cover", "summary", "event", "reason", "data", "impact", "cta"]
SLOTS = {
    "cover": {"eyebrow": [72, 202, 560, 246], "headline": [72, 280, 590, 520], "subheadline": [72, 570, 580, 660], "visual": [535, 215, 1045, 1065]},
    "summary": {"headline": [72, 230, 1008, 340], "cards": [[72, 398, 1008, 566], [72, 598, 1008, 766], [72, 798, 1008, 966]]},
    "event": {"headline": [72, 230, 1008, 340], "main": [72, 396, 1008, 1000]},
    "reason": {"headline": [72, 230, 1008, 340], "steps": [[72, 410, 1008, 558], [72, 600, 1008, 748], [72, 790, 1008, 938]]},
    "data": {"headline": [72, 230, 1008, 340], "chart": [72, 398, 1008, 1002]},
    "impact": {"headline": [72, 230, 1008, 340], "cards": [[72, 395, 1008, 580], [72, 610, 1008, 795], [72, 825, 1008, 1010]]},
    "cta": {"headline": [72, 230, 1008, 340], "checklist": [72, 390, 1008, 820], "cta": [72, 858, 1008, 1018], "sources": [72, 1040, 1008, 1110]},
}


def text(draw, xy, value, font, fill, anchor=None, spacing=7, align="left"):
    draw.multiline_text(xy, value, font=font, fill=fill, anchor=anchor, spacing=spacing, align=align)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def paper_card(image, box, radius=18):
    x1, y1, x2, y2 = box
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x1, y1 + 8, x2, y2 + 8), radius=radius, fill=(0, 0, 0, 58))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    image.alpha_composite(shadow)
    rounded(ImageDraw.Draw(image), box, radius, PAPER, "#D7CBB8", 1)


def add_micro_grain(image):
    """Add deterministic, nearly invisible texture to avoid a sterile flat fill."""
    grain = Image.new("RGBA", image.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    for i in range(1800):
        x = (i * 73 + 17) % W
        y = (i * 151 + 29) % H
        fill = (255, 244, 220, 7) if i % 3 else (0, 0, 0, 9)
        gd.point((x, y), fill=fill)
    image.alpha_composite(grain)


def paste_contain(background, foreground, box):
    x1, y1, x2, y2 = box
    item = foreground.copy().convert("RGBA")
    ratio = min((x2 - x1) / item.width, (y2 - y1) / item.height)
    item = item.resize((round(item.width * ratio), round(item.height * ratio)), Image.Resampling.LANCZOS)
    x = round(x1 + (x2 - x1 - item.width) / 2)
    y = round(y1 + (y2 - y1 - item.height) / 2)
    background.alpha_composite(item, (x, y))


def draw_brand(draw):
    text(draw, (72, 76), "FIN DINING", R36, IVORY)
    text(draw, (72, 118), "by Finsight", S20, MUTED)
    draw.line((72, 151, 1008, 151), fill=GOLD, width=2)


def draw_decorators(draw, cfg, kind):
    accent, second = cfg["accent"], cfg["accent2"]
    if kind == "mon-policy":
        for x in (690, 766, 842, 918, 994):
            draw.line((x, 178, x, 1136), fill="#25231F", width=1)
        rounded(draw, (958, 180, 994, 216), 8, None, accent, 3)
    elif kind == "tue-global":
        draw.arc((690, 170, 1120, 600), 115, 315, fill=accent, width=3)
        draw.arc((-140, 750, 360, 1250), 290, 110, fill=second, width=3)
    elif kind == "wed-market":
        draw.line((690, 1074, 1004, 1074), fill="#39332C", width=2)
        for x, height, color in [(716, 68, accent), (770, 112, second), (824, 84, accent), (878, 142, second), (932, 98, accent)]:
            rounded(draw, (x, 1074 - height, x + 24, 1074), 8, color)
    elif kind == "thu-industry":
        points = [(718, 1035), (790, 960), (862, 1005), (934, 920), (1000, 965)]
        draw.line(points, fill=accent, width=5, joint="curve")
        for x, y in points:
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=second)
    elif kind == "fri-weekly":
        for y in range(206, 1120, 88):
            for x in range(728, 1008, 34):
                draw.ellipse((x, y, x + 3, y + 3), fill="#574D43")
    elif kind == "sat-preview":
        for i, x in enumerate(range(724, 1004, 54)):
            draw.ellipse((x, 1034, x + 18, 1052), fill=accent if i == 5 else "#3A332F")


def base(cfg, kind, page):
    image = Image.new("RGBA", (W, H), CHARCOAL)
    add_micro_grain(image)
    draw = ImageDraw.Draw(image)
    draw_brand(draw)
    draw_decorators(draw, cfg, kind)
    text(draw, (72, 181), cfg["course"], R28, cfg["accent"])
    text(draw, (1008, 181), cfg["label"], S24R, IVORY, anchor="ra")
    draw.line((72, 1176, 1008, 1176), fill="#3B352E", width=2)
    text(draw, (72, 1214), "DATE · KST", S24R, MUTED)
    text(draw, (1008, 1214), f"{page:02d} / 07", R28, cfg["accent"], anchor="ra")
    text(draw, (72, 1270), "정보 제공 목적이며 특정 종목의 매수·매도를 권유하지 않습니다.", S24R, MUTED)
    return image, draw


def empty_layout(cfg, kind, page):
    image, draw = base(cfg, kind, page)
    if page == 1:
        draw.ellipse((610, 268, 1010, 668), fill="#1D1A17", outline="#3B352E", width=2)
        paste_contain(image, Image.open(cfg["hero"]), SLOTS["cover"]["visual"])
        draw.line((72, 704, 382, 704), fill=cfg["accent"], width=4)
    elif page == 2:
        for card in SLOTS["summary"]["cards"]:
            paper_card(image, card)
    elif page == 3:
        paper_card(image, SLOTS["event"]["main"])
        draw.line((188, 492, 188, 901), fill=cfg["accentInk"], width=5)
        for y in (526, 690, 854):
            draw.ellipse((173, y - 15, 203, y + 15), fill=PAPER, outline=cfg["accentInk"], width=4)
    elif page == 4:
        for index, card in enumerate(SLOTS["reason"]["steps"], 1):
            paper_card(image, card)
            rounded(draw, (98, card[1] + 38, 158, card[1] + 98), 30, cfg["accentInk"])
    elif page == 5:
        paper_card(image, SLOTS["data"]["chart"])
        x1, y1, x2, y2 = SLOTS["data"]["chart"]
        draw.line((x1 + 78, y2 - 92, x2 - 50, y2 - 92), fill="#CEC2AF", width=3)
        draw.line((x1 + 78, y1 + 64, x1 + 78, y2 - 92), fill="#CEC2AF", width=3)
    elif page == 6:
        for card in SLOTS["impact"]["cards"]:
            paper_card(image, card)
    elif page == 7:
        paper_card(image, SLOTS["cta"]["checklist"])
        for i in range(4):
            y = 430 + i * 88
            rounded(draw, (100, y, 146, y + 46), 12, IVORY, cfg["accentInk"], 3)
            if i < 3:
                draw.line((176, y + 66, 974, y + 66), fill="#D8CDBA", width=2)
        rounded(draw, SLOTS["cta"]["cta"], 18, cfg["accentInk"])
    return image


def annotated(master, cfg, page):
    image = master.copy()
    draw = ImageDraw.Draw(image)
    if page == 1:
        first, headline, sub = cfg["preview"]
        text(draw, (72, 236), first, S30, cfg["accent"])
        text(draw, (72, 300), headline, S66, IVORY, spacing=10)
        text(draw, (72, 592), sub, S30, MUTED)
        text(draw, (72, 730), cfg["korean"], S26, IVORY)
    else:
        sections = ["", "TASTING NOTES", "THE EVENT", "WHY IT MATTERS", "THE NUMBERS", "YOUR MONEY", "NEXT RESERVATION"]
        titles = ["", "핵심 결론 세 가지", "확인된 사실과 일정", "원인에서 영향까지", "숫자로 읽는 흐름", "기회와 리스크를 함께", "저장해두고 다시 확인"]
        text(draw, (72, 230), sections[page - 1], R28, cfg["accent"])
        text(draw, (72, 276), titles[page - 1], S54, IVORY)
        if page == 2:
            for i, y in enumerate((430, 630, 830), 1):
                text(draw, (110, y), f"0{i}", R36, cfg["accentInk"])
                text(draw, (194, y + 4), "핵심 요약이 들어가는 고정 영역", S30, INK)
        elif page == 3:
            for y, label in ((515, "발표 시점"), (679, "핵심 변화"), (843, "다음 일정")):
                text(draw, (236, y), label, S32, INK)
        elif page == 4:
            for i, (y, label) in enumerate(((445, "첫 번째 원인"), (635, "시장으로 전달되는 과정"), (825, "내 돈에 미치는 영향")), 1):
                text(draw, (128, y + 31), str(i), S24, PAPER, anchor="mm")
                text(draw, (194, y), label, S30, INK)
        elif page == 5:
            text(draw, (154, 450), "차트 · 비교 · 밸류체인 고정 영역", S30, INK)
        elif page == 6:
            for index, (y, label) in enumerate(((395, "영향 대상 또는 기업 1"), (610, "영향 대상 또는 기업 2"), (825, "영향 대상 또는 기업 3")), 1):
                draw.ellipse((100, y + 25, 148, y + 73), fill=cfg["accentInk"])
                text(draw, (124, y + 49), f"{index:02d}", S20, PAPER, anchor="mm")
                text(draw, (176, y + 31), label, S30, INK)
                rounded(draw, (100, y + 105, 518, y + 158), 16, "#E8EFE9")
                rounded(draw, (540, y + 105, 980, y + 158), 16, "#F2E6E5")
                text(draw, (116, y + 112), "기회 · 확인 조건", S24R, "#416B52")
                text(draw, (556, y + 112), "리스크 · 확인 조건", S24R, "#8B4A49")
        elif page == 7:
            for i, y in enumerate((430, 518, 606, 694), 1):
                text(draw, (123, y + 23), "✓", S24, cfg["accentInk"], anchor="mm")
                text(draw, (178, y + 6), f"확인할 지표 또는 일정 {i}", S30, INK)
            text(draw, (540, 938), "저장 · 공유 · 댓글로 다음 코스 예약", S30, PAPER, anchor="mm")
    return image


def make_day_preview(images, destination):
    thumb_w, thumb_h = 270, 338
    sheet = Image.new("RGB", (thumb_w * 4 + 36 * 5, thumb_h * 2 + 74 * 3), CHARCOAL)
    draw = ImageDraw.Draw(sheet)
    for i, image in enumerate(images):
        x = 36 + (i % 4) * (thumb_w + 36)
        y = 36 + (i // 4) * (thumb_h + 74)
        sheet.paste(image.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
        text(draw, (x + thumb_w // 2, y + thumb_h + 18), f"{i + 1:02d}", S18, MUTED, anchor="ma")
    sheet.save(destination, "PNG", optimize=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = {
    "brand": "FIN DINING by Finsight",
    "version": "4.1",
    "mode": "concept-locked-adaptive",
    "renderer": "templates/render_adaptive_course.py",
    "legacyRenderer": "templates/render_daily_course.py",
    "cardRange": [5, 7],
    "archetypes": {
        "cover": ["split-hero", "centered-editorial"],
        "summary": ["lead-plus-support", "editorial-list"],
        "event": ["timeline-cards", "stacked-insights"],
        "reason": ["causal-flow", "stacked-insights"],
        "data": ["range-dots", "line-chart", "rank-bars"],
        "impact": ["featured-plus-grid"],
        "cta": ["calendar-grid", "checklist-stack"],
    },
    "canvas": [W, H],
    "week": list(CONFIGS),
    "templates": {},
}
cover_previews = []

for kind, cfg in CONFIGS.items():
    folder = ROOT / kind
    folder.mkdir(parents=True, exist_ok=True)
    annotated_images, files, hashes = [], [], {}
    for page, name in enumerate(PAGE_NAMES, 1):
        master = empty_layout(cfg, kind, page)
        filename = f"{page:02d}_{name}_master.png"
        path = folder / filename
        master.convert("RGB").save(path, "PNG", optimize=True)
        files.append(filename)
        hashes[filename] = sha256(path)
        preview = annotated(master, cfg, page)
        annotated_images.append(preview)
        if page == 1:
            cover_previews.append((kind, preview))
    preview_name = f"{kind}-preview.png"
    make_day_preview(annotated_images, folder / preview_name)
    layout = {
        "brand": manifest["brand"], "templateId": cfg["id"], "course": cfg["course"], "label": cfg["label"],
        "canvas": {"width": W, "height": H},
        "colors": {"background": CHARCOAL, "paper": PAPER, "ivory": IVORY, "ink": INK, "gold": GOLD, "muted": MUTED, "accent": cfg["accent"], "accentInk": cfg["accentInk"], "accent2": cfg["accent2"]},
        "fonts": {
            "display": {"family": "New York", "path": SERIF, "minimumSize": 28},
            "korean": {"family": "Apple SD Gothic Neo", "path": SANS, "headlineWeight": "Bold", "bodyWeight": "Regular", "minimumBodySize": 30, "minimumLegalSize": 24},
        },
        "heroAsset": str(cfg["hero"].relative_to(ROOT)), "files": files, "masterSha256": hashes, "slots": SLOTS,
        "rules": [
            "Never move, resize, recolor, regenerate, or replace fixed master elements for weekly posts.",
            "Reuse the saved hero asset; do not generate a new cover layout.",
            "Replace DATE and editable content only.",
            "Render every Korean character, number, chart label, and source with the declared system fonts.",
            "Use accent for text on dark backgrounds and accentInk for text or fills on light surfaces.",
            "Rewrite overflowing copy instead of shrinking below the declared minimum sizes.",
        ],
    }
    (folder / "layout.json").write_text(json.dumps(layout, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["templates"][kind] = {
        "templateId": cfg["id"], "directory": f"templates/{kind}", "layout": f"templates/{kind}/layout.json",
        "preview": f"templates/{kind}/{preview_name}", "masterSha256": hashes,
    }

(ROOT / "templates-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

thumb_w, thumb_h = 360, 450
overview = Image.new("RGB", (thumb_w * 3 + 48 * 4, thumb_h * 2 + 94 * 3), CHARCOAL)
draw = ImageDraw.Draw(overview)
for i, (kind, image) in enumerate(cover_previews):
    x = 48 + (i % 3) * (thumb_w + 48)
    y = 46 + (i // 3) * (thumb_h + 94)
    overview.paste(image.convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y))
    text(draw, (x + thumb_w // 2, y + thumb_h + 22), CONFIGS[kind]["korean"], S22, IVORY, anchor="ma")
overview.save(ROOT / "all-weekday-master-preview.png", "PNG", optimize=True)
