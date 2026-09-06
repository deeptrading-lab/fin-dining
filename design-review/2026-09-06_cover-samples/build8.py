#!/usr/bin/env python3
"""S1(접시) · S3(커버) 수정안.

고친 것 셋.
  1. 대사에 거래일·요일·업종명을 넣어 문장만 읽어도 무엇의 숫자인지 알게 한다.
  2. 하단이 겹치던 문제 — 셰프와 말풍선이 바닥글 위로 흘러내렸다. 바닥글에 고정 높이를 주고
     셰프 블록을 그 위에서 끊는다.
  3. 커버의 메뉴 다섯 줄을 위쪽에서 여유 있게 가운데로 펴고, 셰프와 대사는 S1 처럼 아래로 내린다.

날짜는 게시일이 아니라 **거래일**이다. 오늘(9/6)은 일요일이라 장이 없었고 숫자는 9/4 금요일 것이다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = (HERE.parent.parent / "templates/assets").resolve()
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
rank, dish = data["cards"][1], data["cards"][3]
sectors = [(p["label"], p["display"]) for p in rank["data_points"]][:5]
stocks = [(p["label"], *p["display"].split()) for p in dish["data_points"]]

TRADE_DAY = "9월 4일 금요일"  # 거래일. 게시일(9/6 일)이 아니다.
SECTOR = "IT 서비스"
TOTAL, UP = 25, 17

PAPER, PLATE, RIM, RULE = "#FDFAF4", "#FFFDF8", "#E3D9C7", "#D5C9B4"
INK, MUTED, ACCENT = "#1F1B16", "#9A8F7E", "#B0576F"

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
.price {{ font-variant-numeric: tabular-nums; color: #6B6154; }}
.hr {{ height: 1px; background: {RULE}; }}
/* 바닥글은 고정 높이를 갖는 자기 칸이다. 위 블록이 흘러내려도 겹치지 않는다. */
.foot {{ flex: none; height: 74px; display: flex; justify-content: space-between; align-items: center;
        font-size: 21px; color: {MUTED}; letter-spacing: .05em; border-top: 1px solid {RULE}; }}
.plate {{ border-radius: 50%; background: {PLATE}; border: 1px solid {RIM};
         box-shadow: 0 22px 46px rgba(150,128,92,.14); position: relative;
         display: flex; align-items: center; justify-content: center; }}
.plate::after {{ content: ""; position: absolute; inset: 26px; border: 1px solid {RIM}; border-radius: 50%; }}
.row {{ display: flex; align-items: baseline; gap: 16px; }}
.row .nm {{ flex: 1; font-weight: 600; white-space: nowrap; }}
.bubble {{ position: relative; background: #FFFFFF; border: 1.5px solid {RIM}; border-radius: 26px;
          padding: 22px 26px; font-size: 26px; line-height: 1.52;
          box-shadow: 0 10px 26px rgba(150,128,92,.10); }}
.bubble .who {{ font-size: 18px; letter-spacing: .22em; color: {MUTED}; display: block; margin-bottom: 7px; }}
.bubble::after {{ content: ""; position: absolute; width: 19px; height: 19px; background: #FFFFFF;
  border-left: 1.5px solid {RIM}; border-bottom: 1.5px solid {RIM};
  left: -10px; bottom: 40px; transform: rotate(45deg); }}
.chef {{ flex: none; display: block; }}
"""

BULL = f'<img class="chef" src="file://{ART}/chef-bull.png" style="height:300px">'
BEAR = f'<img class="chef" src="file://{ART}/chef-bear.png" style="height:300px">'


def page(body: str) -> str:
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="card"><div class="frame"></div><div class="inner">{body}</div></div>')


# --- S1 접시 카드 --------------------------------------------------------------
rows = ""
for i, (name, price, pct) in enumerate(stocks):
    lead = i == 0
    rows += (f'<div class="row" style="margin-top:{0 if lead else 19}px;'
             f'{f"padding-bottom:15px;border-bottom:1px solid {RULE};" if lead else ""}">'
             f'<span class="nm" style="font-size:{33 if lead else 27}px">{name}</span>'
             f'<span class="price" style="font-size:21px">{price}</span>'
             f'<span class="pct" style="font-size:{30 if lead else 25}px;width:114px;'
             f'text-align:right">{pct}</span></div>')

S1 = page(f"""
<div style="display:flex;justify-content:space-between;align-items:baseline">
  <span class="brand">FIN DINING</span><span class="course serif">SIGNATURE</span></div>
<div class="hr" style="margin-top:20px"></div>
<div class="course serif" style="margin-top:26px">{TOTAL}개 중 {UP}개 상승</div>
<div class="title" style="margin-top:12px">{SECTOR}</div>
<div style="flex:1;display:flex;align-items:center;justify-content:center">
  <div class="plate" style="width:620px;height:620px"><div style="width:470px">{rows}</div></div>
</div>
<div style="flex:none;display:flex;align-items:flex-end;gap:20px;margin-bottom:24px">
  {BULL}
  <div class="bubble" style="flex:1;margin-bottom:34px">
    <span class="who">CHEF BULL</span>
    {SECTOR} 종목 {TOTAL}개 가운데 {UP}개가 올랐어요.
    그중 키다리스튜디오가 +16.50%로 가장 크게 올랐습니다.
  </div>
</div>
<div class="foot"><span>2026 · 09 · 04 종가 기준</span><span>등락률 상위 5종목</span></div>""")

# --- S3 커버 -------------------------------------------------------------------
plan = [("AMUSE-BOUCHE", 3), ("STARTER", 2), ("SIGNATURE", 1), ("MAIN", 0), ("DESSERT", 4)]
menu = ""
for label, idx in plan:
    name, pct = sectors[idx]
    main = label == "MAIN"
    menu += (f'<div style="margin-top:{26 if main else 24}px;'
             f'{f"padding:20px 0;border-top:1px solid {RULE};border-bottom:1px solid {RULE};" if main else ""}">'
             f'<div class="course serif" style="font-size:21px;'
             f'{"color:#8A7F6C;" if main else ""}">{label}</div>'
             f'<div style="display:flex;justify-content:center;align-items:baseline;gap:14px;margin-top:9px">'
             f'<span style="font-size:{46 if main else 34}px;font-weight:600">{name}</span>'
             f'<span class="pct" style="font-size:{39 if main else 28}px">{pct}</span></div></div>')

S3 = page(f"""
<div style="text-align:center">
  <div class="brand">FINSIGHT</div>
  <div class="serif" style="font-size:62px;letter-spacing:.06em;margin-top:16px">FIN DINING</div>
  <div class="course serif" style="margin-top:14px">오늘의 산업 코스</div>
</div>
<div style="flex:1;display:flex;align-items:center">
  <div style="width:100%;text-align:center">{menu}</div>
</div>
<div style="flex:none;display:flex;align-items:flex-end;gap:12px;margin-bottom:24px">
  {BEAR}{BULL}
  <div class="bubble" style="flex:1;margin-bottom:34px;margin-left:8px">
    <span class="who">CHEF BULL &amp; BEAR</span>
    {TRADE_DAY} 주도 섹터 다섯 코스, 지금 나갑니다. 메인은 의료·정밀기기예요.
  </div>
</div>
<div class="foot"><span>2026 · 09 · 04 종가 기준</span><span>KOSPI 업종 등락</span></div>""")

for name, html in (("S1b", S1), ("S3b", S3)):
    (HERE / f"chef-{name}.html").write_text(html, encoding="utf-8")
print("wrote chef-S1b.html, chef-S3b.html")
