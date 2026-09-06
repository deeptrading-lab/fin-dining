#!/usr/bin/env python3
"""접시 카드 시안 — 업종별 대장주 5종목을 담는 3안 + 업종 랭킹 보드 1안.

랭킹(10행)은 접시에 올리지 않는다. 원 안에 10행을 넣으면 행마다 쓸 수 있는 폭(현)이 달라져
글자 크기를 맞출 수 없다. 커버가 메뉴판이면 랭킹은 메뉴 전체, 대장주 5장이 접시에 나온 요리다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
rank_card = data["cards"][1]
dish_card = data["cards"][3]  # 2위 IT 서비스 — 이름 길이가 제각각이라 레이아웃이 잘 드러난다.

sectors = [(p["label"], p["display"]) for p in rank_card["data_points"]]
stocks = [(p["label"], *p["display"].split()) for p in dish_card["data_points"]]

PAPER = "#FDFAF4"
PLATE = "#FFFDF8"
RIM = "#E3D9C7"
RULE = "#D5C9B4"
INK = "#1F1B16"
MUTED = "#9A8F7E"
ACCENT = "#B0576F"

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
/* 접시 — 바깥 림 한 겹, 안쪽 림 한 겹, 아래로 퍼지는 옅은 그림자. */
.plate {{ border-radius: 50%; background: {PLATE}; border: 1px solid {RIM};
         box-shadow: 0 26px 54px rgba(150,128,92,.15); position: relative; }}
.plate::after {{ content: ""; position: absolute; inset: 26px; border: 1px solid {RIM}; border-radius: 50%; }}
"""


def head(course: str, title: str, sub: str) -> str:
    return (f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<span class="brand">FIN DINING</span>'
            f'<span class="course serif">{course}</span></div>'
            f'<div class="hr" style="margin-top:22px"></div>'
            f'<div class="course serif" style="margin-top:30px">{sub}</div>'
            f'<div class="title" style="margin-top:14px">{title}</div>')


def foot(right: str) -> str:
    return f'<div class="foot"><span>2026 · 09 · 06</span><span>{right}</span></div>'


def page(body: str) -> str:
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="card"><div class="frame"></div><div class="inner">{body}</div></div>')


HEAD = head("SIGNATURE", "IT 서비스", "COURSE 03 · 25개 중 17개 상승")

# P1 — 접시 하나에 다섯 가지를 담는다. 원 안이라 행마다 쓸 수 있는 폭이 달라 가운데 정렬로 맞춘다.
rows_1 = ""
for i, (name, price, pct) in enumerate(stocks):
    lead = i == 0
    rows_1 += (f'<div style="margin-top:{0 if lead else 22}px">'
               f'<div style="display:flex;justify-content:center;align-items:baseline;gap:14px">'
               f'<span style="font-size:{40 if lead else 31}px;font-weight:{700 if lead else 600}">{name}</span>'
               f'<span class="pct" style="font-size:{36 if lead else 28}px">{pct}</span></div>'
               f'<div class="price" style="font-size:{25 if lead else 22}px;margin-top:4px">{price}</div>'
               f'</div>')
P1 = page(f"""{HEAD}
<div style="flex:1;display:flex;align-items:center;justify-content:center;margin-top:18px">
  <div class="plate" style="width:800px;height:800px;display:flex;align-items:center;justify-content:center">
    <div style="width:560px;text-align:center">{rows_1}</div>
  </div>
</div>
{foot("등락률 상위 5종목")}""")

# P2 — 메인 요리 하나를 접시에 올리고 나머지 넷은 곁들임처럼 아래에 깐다.
lead_name, lead_price, lead_pct = stocks[0]
sides = ""
for name, price, pct in stocks[1:]:
    sides += (f'<div style="display:flex;align-items:baseline;gap:14px;padding:17px 0;'
              f'border-top:1px solid {RULE}">'
              f'<span style="font-size:30px;font-weight:600;flex:1">{name}</span>'
              f'<span class="price" style="font-size:25px">{price}</span>'
              f'<span class="pct" style="font-size:29px;width:132px;text-align:right">{pct}</span></div>')
P2 = page(f"""{HEAD}
<div style="display:flex;justify-content:center;margin-top:26px">
  <div class="plate" style="width:470px;height:470px;display:flex;flex-direction:column;
       align-items:center;justify-content:center">
    <div class="course serif" style="font-size:19px">TODAY'S PICK</div>
    <div style="font-size:44px;font-weight:700;margin-top:12px">{lead_name}</div>
    <div class="pct" style="font-size:48px;margin-top:8px">{lead_pct}</div>
    <div class="price" style="font-size:25px;margin-top:6px">{lead_price}원</div>
  </div>
</div>
<div style="margin-top:38px">{sides}</div>
{foot("등락률 상위 5종목")}""")

# P3 — 종목마다 접시 하나. 등락률을 접시에 담고 이름과 가격을 곁에 둔다.
rows_3 = ""
for i, (name, price, pct) in enumerate(stocks):
    size = 132 if i == 0 else 108
    rows_3 += (f'<div style="display:flex;align-items:center;gap:32px;margin-top:{0 if i == 0 else 20}px">'
               f'<div class="plate" style="width:{size}px;height:{size}px;flex:none;'
               f'display:flex;align-items:center;justify-content:center">'
               f'<span class="pct" style="font-size:{27 if i == 0 else 23}px">{pct}</span></div>'
               f'<div style="flex:1">'
               f'<div style="font-size:{36 if i == 0 else 31}px;font-weight:600">{name}</div>'
               f'<div class="price" style="font-size:24px;margin-top:5px">{price}원</div></div>'
               f'<div class="course serif" style="font-size:20px">{i + 1:02d}</div></div>')
P3 = page(f'{HEAD}<div style="margin-top:34px">{rows_3}</div>{foot("등락률 상위 5종목")}')

# R1 — 랭킹 보드. 접시가 아니라 메뉴 전체를 적어 둔 판이다. 점선 리더로 이름과 등락률을 잇는다.
rows_r = ""
for i, (name, pct) in enumerate(sectors, 1):
    rows_r += (f'<div style="display:flex;align-items:baseline;gap:16px;margin-top:24px">'
               f'<span class="course serif" style="width:44px;font-size:20px">{i:02d}</span>'
               f'<span style="font-size:33px;font-weight:600;white-space:nowrap">{name}</span>'
               f'<span style="flex:1;border-bottom:1.5px dotted #CBBFA8;transform:translateY(-8px)"></span>'
               f'<span class="pct" style="font-size:31px">{pct}</span></div>')
R1 = page(f"""{head("TODAY'S MENU", "지금 뜨는 산업", "COURSE 02 · 업종 등락 랭킹")}
<div style="margin-top:14px">{rows_r}</div>
{foot("KOSPI 업종 상위 10")}""")

for name, html in (("P1", P1), ("P2", P2), ("P3", P3), ("R1", R1)):
    (HERE / f"dish-{name}.html").write_text(html, encoding="utf-8")
print("wrote", ", ".join(f"dish-{n}.html" for n in ("P1", "P2", "P3", "R1")))
