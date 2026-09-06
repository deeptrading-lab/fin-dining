#!/usr/bin/env python3
"""셰프 스토리텔링 시안 — 실제 캐릭터 아트가 오기 전 배치와 대사 흐름만 확인한다.

캐릭터는 자리표시자(모자·머리·몸통 실루엣)다. 크기와 앉는 위치, 말풍선 꼬리 방향, 대사 길이가
카드 안에서 성립하는지만 본다.

역할은 캐릭터가 이미 정해 준다. 황소는 오른 쪽을 말하고, 곰은 온도차와 주의를 짚는다.
대사는 전부 데이터에서 만들어지므로 사람이 매일 쓰지 않는다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
rank = data["cards"][1]
dish = data["cards"][3]
sectors = [(p["label"], p["display"]) for p in rank["data_points"]][:5]
stocks = [(p["label"], *p["display"].split()) for p in dish["data_points"]]

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
.title {{ font-size: 50px; font-weight: 700; letter-spacing: -.01em; }}
.pct {{ color: {ACCENT}; font-weight: 600; font-variant-numeric: tabular-nums; }}
.price {{ font-variant-numeric: tabular-nums; color: #6B6154; }}
.foot {{ margin-top: auto; display: flex; justify-content: space-between; align-items: center;
        font-size: 21px; color: {MUTED}; letter-spacing: .05em; }}
.hr {{ height: 1px; background: {RULE}; }}
.plate {{ border-radius: 50%; background: {PLATE}; border: 1px solid {RIM};
         box-shadow: 0 22px 46px rgba(150,128,92,.14); position: relative;
         display: flex; align-items: center; justify-content: center; }}
.plate::after {{ content: ""; position: absolute; inset: 26px; border: 1px solid {RIM}; border-radius: 50%; }}
.row {{ display: flex; align-items: baseline; gap: 16px; }}
.row .nm {{ flex: 1; font-weight: 600; white-space: nowrap; }}

/* 말풍선 — 흰 종이 위 흰 풍선이라 테두리로만 분리한다. 꼬리는 회전한 사각형. */
.bubble {{ position: relative; background: #FFFFFF; border: 1.5px solid {RIM}; border-radius: 26px;
          padding: 24px 28px; font-size: 27px; line-height: 1.5;
          box-shadow: 0 10px 26px rgba(150,128,92,.10); }}
.bubble .who {{ font-size: 19px; letter-spacing: .22em; color: {MUTED}; display: block; margin-bottom: 8px; }}
.bubble::after {{ content: ""; position: absolute; width: 20px; height: 20px; background: #FFFFFF;
  border-left: 1.5px solid {RIM}; border-bottom: 1.5px solid {RIM}; }}
.tail-left::after  {{ left: -11px; bottom: 34px; transform: rotate(45deg); }}
.tail-right::after {{ right: -11px; bottom: 34px; transform: rotate(-135deg); }}
.tail-down::after  {{ left: 64px; bottom: -11px; transform: rotate(-45deg); }}

.chef {{ flex: none; display: block; }}
"""

ART = (HERE.parent.parent / "templates/assets").resolve()
BULL = f'<img class="chef" src="file://{ART}/chef-bull.png" style="height:320px">'
BEAR = f'<img class="chef" src="file://{ART}/chef-bear.png" style="height:320px">'


def page(body: str) -> str:
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="card"><div class="frame"></div><div class="inner">{body}</div></div>')


def rows_html(scale: float = 1.0) -> str:
    out = ""
    for i, (name, price, pct) in enumerate(stocks):
        lead = i == 0
        out += (f'<div class="row" style="margin-top:{0 if lead else round(20 * scale)}px;'
                f'{f"padding-bottom:16px;border-bottom:1px solid {RULE};" if lead else ""}">'
                f'<span class="nm" style="font-size:{round((34 if lead else 28) * scale)}px">{name}</span>'
                f'<span class="price" style="font-size:{round(21 * scale)}px">{price}</span>'
                f'<span class="pct" style="font-size:{round((31 if lead else 26) * scale)}px;'
                f'width:{round(116 * scale)}px;text-align:right">{pct}</span></div>')
    return out


DISH_HEAD = ('<div style="display:flex;justify-content:space-between;align-items:baseline">'
             '<span class="brand">FIN DINING</span><span class="course serif">SIGNATURE</span></div>'
             '<div class="hr" style="margin-top:20px"></div>'
             '<div class="course serif" style="margin-top:26px">25개 중 17개 상승</div>'
             '<div class="title" style="margin-top:12px">IT 서비스</div>')

# S1 — 접시를 줄여 위로 올리고, 아래에 셰프와 말풍선을 나란히 앉힌다.
S1 = page(f"""{DISH_HEAD}
<div style="display:flex;justify-content:center;margin-top:20px">
  <div class="plate" style="width:660px;height:660px"><div style="width:490px">{rows_html(.9)}</div></div>
</div>
<div style="display:flex;align-items:flex-end;gap:24px;margin-top:26px">
  {BULL}
  <div class="bubble tail-left" style="flex:1;margin-bottom:26px">
    <span class="who">CHEF BULL</span>
    25개 중 17개가 올랐어요. 키다리스튜디오가 +16.50%로 제일 크게 올랐고요.
  </div>
</div>
<div class="foot"><span>2026 · 09 · 06</span><span>등락률 상위 5종목</span></div>""")

# S2 — 셰프를 접시 옆에 세우고 말풍선을 위로 올린다. 접시를 덜 줄여도 된다.
S2 = page(f"""{DISH_HEAD}
<div style="display:flex;align-items:center;gap:8px;margin-top:14px">
  <div style="flex:1">
    <div class="bubble tail-down" style="margin-bottom:26px">
      <span class="who">CHEF BULL</span>
      25개 중 17개가 올랐어요. 키다리스튜디오가 +16.50%로 제일 크게 올랐습니다.
    </div>
    {BULL}
  </div>
  <div class="plate" style="width:600px;height:600px;margin-right:-40px">
    <div style="width:440px">{rows_html(.82)}</div></div>
</div>
<div class="foot"><span>2026 · 09 · 06</span><span>등락률 상위 5종목</span></div>""")

# S3 — 커버. 두 셰프가 나란히 서서 오늘 코스를 여는 인사를 나눈다.
plan = [("AMUSE-BOUCHE", 3), ("STARTER", 2), ("SIGNATURE", 1), ("MAIN", 0), ("DESSERT", 4)]
menu = ""
for label, idx in plan:
    name, pct = sectors[idx]
    main = label == "MAIN"
    menu += (f'<div style="margin-top:{20 if main else 17}px;'
             f'{f"padding:14px 0;border-top:1px solid {RULE};border-bottom:1px solid {RULE};" if main else ""}">'
             f'<div class="course serif" style="font-size:19px">{label}</div>'
             f'<div style="display:flex;justify-content:center;align-items:baseline;gap:13px;margin-top:6px">'
             f'<span style="font-size:{40 if main else 30}px;font-weight:600">{name}</span>'
             f'<span class="pct" style="font-size:{34 if main else 25}px">{pct}</span></div></div>')
S3 = page(f"""
<div style="text-align:center">
  <div class="brand">FINSIGHT</div>
  <div class="serif" style="font-size:60px;letter-spacing:.06em;margin-top:14px">FIN DINING</div>
  <div class="course serif" style="margin-top:12px">오늘의 산업 코스</div>
  <div style="margin-top:16px">{menu}</div>
</div>
<div style="display:flex;align-items:flex-end;justify-content:space-between;margin-top:28px">
  {BEAR}
  <div class="bubble" style="flex:1;margin:0 18px 40px;text-align:center;font-size:26px">
    오늘 다섯 코스, 지금 나갑니다
  </div>
  {BULL}
</div>
<div class="foot"><span>2026 · 09 · 06</span><span>KOSPI 업종 등락</span></div>""")

for name, html in (("S1", S1), ("S2", S2), ("S3", S3)):
    (HERE / f"chef-{name}.html").write_text(html, encoding="utf-8")
print("wrote chef-S1.html, chef-S2.html, chef-S3.html")
