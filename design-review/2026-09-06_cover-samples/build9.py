#!/usr/bin/env python3
"""확정 시안 3종 — 커버 / 상승 카드(황소) / 하락 카드(곰).

셰프 배정 규칙: 그 업종에 내린 종목이 있으면 곰이 그 대목을 말하고, 전부 올랐으면 황소가 말한다.
커버는 둘이 함께 나와 가운데 대사를 나눈다.

말풍선은 어절 단위로 끊는다(`word-break: keep-all`). Pillow 렌더러에서는 기존 `wrap_text` 가
`text.split()` 으로 같은 일을 하고, 세 줄을 넘기면 ValueError 를 던지므로 `page_heading` 처럼
글자 크기를 한 단계씩 낮춰 재시도한다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = (HERE.parent.parent / "templates/assets").resolve()
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
cards = data["cards"]
sectors = [(p["label"], p["display"]) for p in cards[1]["data_points"]][:5]

TRADE_DAY = "9월 4일 금요일"
PAPER, PLATE, RIM, RULE = "#FDFAF4", "#FFFDF8", "#E3D9C7", "#D5C9B4"
INK, MUTED, ACCENT, DOWN = "#1F1B16", "#9A8F7E", "#B0576F", "#4A6E96"

CSS = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
.card {{ width: 1080px; height: 1350px; position: relative; background: {PAPER}; color: {INK};
        font-family: "Apple SD Gothic Neo", sans-serif; }}
.card::before {{ content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse at 22% 18%, rgba(198,178,140,.09), transparent 55%),
              radial-gradient(ellipse at 80% 82%, rgba(198,178,140,.07), transparent 55%); }}
.frame {{ position: absolute; inset: 46px; border: 2px solid #C9BCA4; }}
.frame::after {{ content: ""; position: absolute; inset: 9px; border: 1px solid #D8CEBB; }}
.inner {{ position: relative; z-index: 2; height: 100%; padding: 88px 100px 66px;
         display: flex; flex-direction: column; }}
.serif {{ font-family: "New York", "Times New Roman", serif; }}
.brand {{ font-size: 21px; letter-spacing: .38em; color: {MUTED}; }}
.course {{ font-size: 22px; letter-spacing: .3em; color: #A2967F; }}
.title {{ font-size: 50px; font-weight: 700; letter-spacing: -.01em; }}
.pct {{ color: {ACCENT}; font-weight: 600; font-variant-numeric: tabular-nums; }}
.pct.dn {{ color: {DOWN}; }}
.price {{ font-variant-numeric: tabular-nums; color: #6B6154; }}
.hr {{ height: 1px; background: {RULE}; }}
.foot {{ flex: none; height: 74px; display: flex; justify-content: space-between; align-items: center;
        font-size: 21px; color: {MUTED}; letter-spacing: .05em; border-top: 1px solid {RULE}; }}
.plate {{ border-radius: 50%; background: {PLATE}; border: 1px solid {RIM};
         box-shadow: 0 22px 46px rgba(150,128,92,.14); position: relative;
         display: flex; align-items: center; justify-content: center; }}
.plate::after {{ content: ""; position: absolute; inset: 26px; border: 1px solid {RIM}; border-radius: 50%; }}
.row {{ display: flex; align-items: baseline; gap: 16px; }}
.row .nm {{ flex: 1; font-weight: 600; white-space: nowrap; }}
/* keep-all — 한국어를 어절 단위로만 끊는다. 종목명이 중간에서 갈라지지 않는다. */
.bubble {{ position: relative; background: #FFFFFF; border: 1.5px solid {RIM}; border-radius: 26px;
          padding: 22px 26px; font-size: 26px; line-height: 1.52; word-break: keep-all;
          box-shadow: 0 10px 26px rgba(150,128,92,.10); }}
.bubble .who {{ font-size: 18px; letter-spacing: .22em; color: {MUTED}; display: block; margin-bottom: 7px; }}
.tail {{ position: absolute; width: 19px; height: 19px; background: #FFFFFF;
        border-left: 1.5px solid {RIM}; border-bottom: 1.5px solid {RIM}; bottom: 40px; }}
.tail.l {{ left: -10px; transform: rotate(45deg); }}
.tail.r {{ right: -10px; transform: rotate(-135deg); }}
.chef {{ flex: none; display: block; }}
"""

BULL = f'<img class="chef" src="file://{ART}/chef-bull.png" style="height:300px">'
BEAR = f'<img class="chef" src="file://{ART}/chef-bear.png" style="height:300px">'


def page(body: str) -> str:
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="card"><div class="frame"></div><div class="inner">{body}</div></div>')


def plate_rows(card: dict) -> str:
    out = ""
    for i, point in enumerate(card["data_points"]):
        price, pct = point["display"].split()
        down = point["value"] < 0
        out += (f'<div class="row" style="margin-top:{0 if not i else 22}px;'
                f'{f"padding-bottom:15px;border-bottom:1px solid {RULE};" if not i else ""}">'
                f'<span class="nm" style="font-size:{38 if not i else 31}px">{point["label"]}</span>'
                f'<span class="price" style="font-size:24px">{price}</span>'
                f'<span class="pct{" dn" if down else ""}" style="font-size:{35 if not i else 29}px;'
                f'width:132px;text-align:right">{pct}</span></div>')
    return out


def dish(card: dict, course: str, breadth: str, who: str, line: str) -> str:
    chef = BULL if who == "BULL" else BEAR
    return page(f"""
<div style="display:flex;justify-content:space-between;align-items:baseline">
  <span class="brand">FIN DINING</span><span class="course serif">{course}</span></div>
<div class="hr" style="margin-top:20px"></div>
<div class="course serif" style="margin-top:26px">{breadth}</div>
<div class="title" style="margin-top:12px">{card["headline"].replace(" 대장주", "")}</div>
<div style="flex:1;display:flex;align-items:center;justify-content:center">
  <div class="plate" style="width:700px;height:700px"><div style="width:540px">{plate_rows(card)}</div></div>
</div>
<div style="flex:none;display:flex;align-items:flex-end;gap:20px;margin-bottom:24px">
  {chef}
  <div class="bubble" style="flex:1;margin-bottom:34px">
    <div class="tail l"></div><span class="who">CHEF {who}</span>{line}</div>
</div>
<div class="foot"><span>2026 · 09 · 04 종가 기준</span><span>등락률 상위 5종목</span></div>""")


# 상승 카드 — 다섯 종목이 모두 올랐다. 황소가 말한다.
UP_CARD = dish(cards[3], "SIGNATURE", "25개 중 17개 상승", "BULL",
               "IT 서비스 종목 25개 가운데 17개가 올랐어요. 그중 키다리스튜디오가 +16.50%로 가장 크게 올랐습니다.")

# 하락 카드 — 업종은 올랐지만 내린 종목이 섞여 있다. 곰이 그 대목을 짚는다.
DOWN_CARD = dish(cards[6], "DESSERT", "4개 중 2개 상승", "BEAR",
                 "통신은 4개 중 2개만 올랐어요. LG유플러스는 -0.34%로 혼자 내렸습니다.")

# 커버 — 둘이 양쪽에 서고 대사가 가운데 놓인다.
plan = [("AMUSE-BOUCHE", 3), ("STARTER", 2), ("SIGNATURE", 1), ("MAIN", 0), ("DESSERT", 4)]
menu = ""
for label, idx in plan:
    name, pct = sectors[idx]
    main = label == "MAIN"
    menu += (f'<div style="margin-top:{26 if main else 24}px;'
             f'{f"padding:20px 0;border-top:1px solid {RULE};border-bottom:1px solid {RULE};" if main else ""}">'
             f'<div class="course serif" style="font-size:21px;{"color:#8A7F6C;" if main else ""}">{label}</div>'
             f'<div style="display:flex;justify-content:center;align-items:baseline;gap:14px;margin-top:9px">'
             f'<span style="font-size:{46 if main else 34}px;font-weight:600">{name}</span>'
             f'<span class="pct" style="font-size:{39 if main else 28}px">{pct}</span></div></div>')

COVER = page(f"""
<div style="text-align:center">
  <div class="brand">FINSIGHT</div>
  <div class="serif" style="font-size:62px;letter-spacing:.06em;margin-top:16px">FIN DINING</div>
  <div class="course serif" style="margin-top:14px">오늘의 산업 코스</div>
</div>
<div style="flex:1;display:flex;align-items:center">
  <div style="width:100%;text-align:center">{menu}</div>
</div>
<div style="flex:none;display:flex;align-items:flex-end;justify-content:space-between;
            gap:14px;margin-bottom:24px">
  {BEAR}
  <div class="bubble" style="flex:1;margin-bottom:44px;text-align:center">
    <div class="tail l"></div><div class="tail r"></div>
    <span class="who">CHEF BEAR &amp; BULL</span>
    {TRADE_DAY} 주도 섹터 다섯 코스, 지금 나갑니다.</div>
  {BULL}
</div>
<div class="foot"><span>2026 · 09 · 04 종가 기준</span><span>KOSPI 업종 등락</span></div>""")

for name, html in (("cover", COVER), ("up", UP_CARD), ("down", DOWN_CARD)):
    (HERE / f"final-{name}.html").write_text(html, encoding="utf-8")
print("wrote final-cover.html, final-up.html, final-down.html")
