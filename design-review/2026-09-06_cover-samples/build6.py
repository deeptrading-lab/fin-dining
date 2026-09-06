#!/usr/bin/env python3
"""접시 카드 A′ — P1 의 접시 하나를 유지하고 안쪽 정렬만 P2 처럼 열로 세운다.

P1 의 문제는 은유가 아니라 정렬이었다. 원 안이라 가운데로 모으니 종목명 길이(NHN 대 롯데이노베이트)
가 그대로 들쭉날쭉으로 드러나고, 가격이 이름 아래로 밀려 위아래로 훑어야 했다. 접시 안에 들어가는
가장 넓은 사각형만 쓰면 원 안에서도 열을 세울 수 있다.

원 반지름 405 기준, 중심에서 위아래 210 안쪽의 현 길이는 약 692px 이라 폭 560 의 열은 어디서도
접시 밖으로 나가지 않는다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
dish_card = data["cards"][3]
stocks = [(p["label"], *p["display"].split()) for p in dish_card["data_points"]]

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
.inner {{ position: relative; z-index: 2; height: 100%; padding: 92px 104px 84px;
         display: flex; flex-direction: column; }}
.serif {{ font-family: "New York", "Times New Roman", serif; }}
.brand {{ font-size: 21px; letter-spacing: .38em; color: {MUTED}; }}
.course {{ font-size: 22px; letter-spacing: .3em; color: #A2967F; }}
.title {{ font-size: 52px; font-weight: 700; letter-spacing: -.01em; }}
.pct {{ color: {ACCENT}; font-weight: 600; font-variant-numeric: tabular-nums; }}
.price {{ font-variant-numeric: tabular-nums; color: #6B6154; }}
.foot {{ margin-top: auto; display: flex; justify-content: space-between; align-items: center;
        font-size: 21px; color: {MUTED}; letter-spacing: .05em; }}
.hr {{ height: 1px; background: {RULE}; }}
.plate {{ border-radius: 50%; background: {PLATE}; border: 1px solid {RIM};
         box-shadow: 0 26px 54px rgba(150,128,92,.15); position: relative;
         display: flex; align-items: center; justify-content: center; }}
.plate::after {{ content: ""; position: absolute; inset: 30px; border: 1px solid {RIM}; border-radius: 50%; }}
.row {{ display: flex; align-items: baseline; gap: 18px; }}
.row .nm {{ flex: 1; font-weight: 600; white-space: nowrap; }}
"""

rows = ""
for i, (name, price, pct) in enumerate(stocks):
    lead = i == 0
    rows += (f'<div class="row" style="margin-top:{0 if lead else 26}px;'
             f'{f"padding-bottom:20px;border-bottom:1px solid {RULE};" if lead else ""}">'
             f'<span class="nm" style="font-size:{37 if lead else 30}px">{name}</span>'
             f'<span class="price" style="font-size:{24 if lead else 22}px">{price}</span>'
             f'<span class="pct" style="font-size:{34 if lead else 28}px;width:124px;text-align:right">{pct}</span>'
             f'</div>')

HTML = f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="card"><div class="frame"></div><div class="inner">
  <div style="display:flex;justify-content:space-between;align-items:baseline">
    <span class="brand">FIN DINING</span><span class="course serif">SIGNATURE</span></div>
  <div class="hr" style="margin-top:22px"></div>
  <div class="course serif" style="margin-top:30px">25개 중 17개 상승</div>
  <div class="title" style="margin-top:14px">IT 서비스</div>
  <div style="flex:1;display:flex;align-items:center;justify-content:center;margin-top:12px">
    <div class="plate" style="width:810px;height:810px">
      <div style="width:560px">{rows}</div>
    </div>
  </div>
  <div class="foot"><span>2026 · 09 · 06</span><span>등락률 상위 5종목</span></div>
</div></div>"""

(HERE / "dish-A2.html").write_text(HTML, encoding="utf-8")
print("wrote dish-A2.html")
