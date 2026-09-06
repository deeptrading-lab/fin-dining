#!/usr/bin/env python3
"""접시 모양 3종 비교 + 하단 슬롯 고정.

## 하단이 밀려나던 이유
지금까지 하단(셰프·말풍선·바닥글)을 세로 흐름(flex)에 얹어 뒀다. 그러면 위 내용이 한 줄만 길어져도
아래가 통째로 밀려 프레임 밖으로 나간다. 카드 크기가 1080×1350 으로 고정이므로 흐름에 맡길 이유가
없다. 아래 SLOTS 의 좌표에 절대 배치해 위에서 무슨 일이 나든 움직이지 않게 한다.

## 접시가 원처럼만 보이던 이유
테두리 한 겹짜리 정원이라 그릇의 림(테)과 웰(음식이 놓이는 안쪽 면)이 구분되지 않았다.
셋 다 림과 웰을 톤으로 갈라 두고, 형태만 달리한다. 글은 가로로 긴 다섯 줄이라 세로로 남는 정원보다
가로로 퍼진 타원이 폭을 더 준다.
"""

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = (HERE.parent.parent / "templates/assets").resolve()
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
card = data["cards"][3]

W, H = 1080, 1350
# 카드가 고정 크기이므로 자리도 고정한다. 값은 전부 카드 좌상단 기준 절대 좌표다.
SLOTS = {
    "safe_x": (100, 980),          # 프레임 안쪽 여백을 뺀 본문 폭
    "head_top": 88,
    "plate_cy": 585,               # 접시 중심 y
    "chef": (100, 1178, 300),      # 셰프 좌측 x, 바닥 y, 높이
    "bubble": (430, 946, 980, 1122),  # 말풍선 x1, y1, x2, y2
    "foot_rule_y": 1214,           # 바닥글 위 괘선
    "foot_text_cy": 1254,          # 바닥글 글자 세로 중심 (프레임 안쪽 1295 위)
}

PAPER, RIM, RULE = "#FDFAF4", "#E3D9C7", "#D5C9B4"
PLATE_RIM, PLATE_WELL = "#F7F1E6", "#FFFDF9"  # 림은 살짝 어둡게, 웰은 밝게 — 그래야 그릇으로 읽힌다.
INK, MUTED, ACCENT, DOWN = "#1F1B16", "#9A8F7E", "#B0576F", "#4A6E96"

CSS = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
.card {{ width: {W}px; height: {H}px; position: relative; background: {PAPER}; color: {INK};
        font-family: "Apple SD Gothic Neo", sans-serif; overflow: hidden; }}
.card::before {{ content: ""; position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse at 22% 18%, rgba(198,178,140,.09), transparent 55%),
              radial-gradient(ellipse at 80% 82%, rgba(198,178,140,.07), transparent 55%); }}
.frame {{ position: absolute; inset: 46px; border: 2px solid #C9BCA4; }}
.frame::after {{ content: ""; position: absolute; inset: 9px; border: 1px solid #D8CEBB; }}
.serif {{ font-family: "New York", "Times New Roman", serif; }}
.brand {{ font-size: 21px; letter-spacing: .38em; color: {MUTED}; }}
.course {{ font-size: 22px; letter-spacing: .3em; color: #A2967F; }}
.title {{ font-size: 50px; font-weight: 700; letter-spacing: -.01em; }}
.pct {{ color: {ACCENT}; font-weight: 600; font-variant-numeric: tabular-nums; }}
.pct.dn {{ color: {DOWN}; }}
.price {{ font-variant-numeric: tabular-nums; color: #6B6154; }}
.row {{ display: flex; align-items: baseline; gap: 16px; }}
.row .nm {{ flex: 1; font-weight: 600; white-space: nowrap; }}
.bubble {{ position: absolute; background: #FFFFFF; border: 1.5px solid {RIM}; border-radius: 26px;
          padding: 22px 28px; font-size: 26px; line-height: 1.52; word-break: keep-all;
          box-shadow: 0 10px 26px rgba(150,128,92,.10); display: flex; flex-direction: column;
          justify-content: center; }}
.bubble .who {{ font-size: 18px; letter-spacing: .22em; color: {MUTED}; margin-bottom: 7px; }}
.bubble::after {{ content: ""; position: absolute; width: 19px; height: 19px; background: #FFFFFF;
  border-left: 1.5px solid {RIM}; border-bottom: 1.5px solid {RIM};
  left: -10px; bottom: 52px; transform: rotate(45deg); }}
"""


def rows(scale: float = 1.0) -> str:
    out = ""
    for i, point in enumerate(card["data_points"]):
        price, pct = point["display"].split()
        dn = point["value"] < 0
        out += (f'<div class="row" style="margin-top:{0 if not i else round(22 * scale)}px;'
                f'{f"padding-bottom:15px;border-bottom:1px solid {RULE};" if not i else ""}">'
                f'<span class="nm" style="font-size:{round((38 if not i else 31) * scale)}px">{point["label"]}</span>'
                f'<span class="price" style="font-size:{round(24 * scale)}px">{price}</span>'
                f'<span class="pct{" dn" if dn else ""}" style="font-size:{round((35 if not i else 29) * scale)}px;'
                f'width:{round(132 * scale)}px;text-align:right">{pct}</span></div>')
    return out


def scallop_path(cx: float, cy: float, rx: float, ry: float, lobes: int = 22, depth: float = 9.0) -> str:
    """가장자리가 물결치는 타원. 같은 계산을 Pillow 에서 polygon 으로 그대로 쓸 수 있다."""
    pts = []
    for i in range(360):
        t = math.radians(i)
        k = 1 + depth / max(rx, ry) * math.sin(lobes * t)
        pts.append(f"{cx + rx * k * math.cos(t):.1f},{cy + ry * k * math.sin(t):.1f}")
    return "M" + "L".join(pts) + "Z"


HEAD = f'''
<div style="position:absolute;left:100px;top:{SLOTS["head_top"]}px;width:880px">
  <div style="display:flex;justify-content:space-between;align-items:baseline">
    <span class="brand">FIN DINING</span><span class="course serif">SIGNATURE</span></div>
  <div style="height:1px;background:{RULE};margin-top:20px"></div>
  <div class="course serif" style="margin-top:26px">25개 중 17개 상승</div>
  <div class="title" style="margin-top:12px">IT 서비스</div>
</div>'''

FOOT = f'''
<div style="position:absolute;left:100px;top:{SLOTS["foot_rule_y"]}px;width:880px;height:1px;background:{RULE}"></div>
<div style="position:absolute;left:100px;top:{SLOTS["foot_text_cy"] - 15}px;width:880px;
            display:flex;justify-content:space-between;font-size:21px;color:{MUTED};letter-spacing:.05em">
  <span>2026 · 09 · 04 종가 기준</span><span>등락률 상위 5종목</span></div>'''

cx, cy, chh = SLOTS["chef"]
CHEF = f'<img src="file://{ART}/chef-bull.png" style="position:absolute;left:{cx}px;top:{cy - chh}px;height:{chh}px">'
bx1, by1, bx2, by2 = SLOTS["bubble"]
BUBBLE = (f'<div class="bubble" style="left:{bx1}px;top:{by1}px;width:{bx2 - bx1}px;height:{by2 - by1}px">'
          f'<span class="who">CHEF BULL</span>'
          f'IT 서비스 종목 25개 가운데 17개가 올랐어요. 그중 키다리스튜디오가 +16.50%로 가장 크게 올랐습니다.</div>')


def page(plate_html: str) -> str:
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="card"><div class="frame"></div>{HEAD}{plate_html}{CHEF}{BUBBLE}{FOOT}</div>')


SHADOW = "filter:drop-shadow(0 24px 34px rgba(150,128,92,.20))"

# A — 가로로 퍼진 타원 접시. 림을 넓게 두고 웰을 밝게 파 글이 웰 안에 놓이게 한다.
RX, RY = 452, 300
A = page(f'''
<svg width="{W}" height="{H}" style="position:absolute;left:0;top:0;{SHADOW}">
  <ellipse cx="{W/2}" cy="{SLOTS["plate_cy"]}" rx="{RX}" ry="{RY}" fill="{PLATE_RIM}" stroke="{RIM}" stroke-width="1.5"/>
  <ellipse cx="{W/2}" cy="{SLOTS["plate_cy"]}" rx="{RX-52}" ry="{RY-40}" fill="{PLATE_WELL}" stroke="{RIM}" stroke-width="1"/>
</svg>
<div style="position:absolute;left:{W/2-280}px;top:{SLOTS["plate_cy"]-215}px;width:560px">{rows(1.0)}</div>''')

# B — 정원이되 림을 넓게 잡아 그릇처럼 보이게 한다. 폭이 좁아 글자를 한 단계 줄인다.
R = 320
B = page(f'''
<svg width="{W}" height="{H}" style="position:absolute;left:0;top:0;{SHADOW}">
  <circle cx="{W/2}" cy="{SLOTS["plate_cy"]}" r="{R}" fill="{PLATE_RIM}" stroke="{RIM}" stroke-width="1.5"/>
  <circle cx="{W/2}" cy="{SLOTS["plate_cy"]}" r="{R-58}" fill="{PLATE_WELL}" stroke="{RIM}" stroke-width="1"/>
</svg>
<div style="position:absolute;left:{W/2-232}px;top:{SLOTS["plate_cy"]-198}px;width:464px">{rows(.86)}</div>''')

# C — 가장자리가 물결치는 타원. 캐릭터 일러스트의 스캘럽 테두리와 결이 맞는다.
C = page(f'''
<svg width="{W}" height="{H}" style="position:absolute;left:0;top:0;{SHADOW}">
  <path d="{scallop_path(W/2, SLOTS["plate_cy"], RX-14, RY-10)}" fill="{PLATE_RIM}" stroke="{RIM}" stroke-width="1.5"/>
  <ellipse cx="{W/2}" cy="{SLOTS["plate_cy"]}" rx="{RX-70}" ry="{RY-52}" fill="{PLATE_WELL}" stroke="{RIM}" stroke-width="1"/>
</svg>
<div style="position:absolute;left:{W/2-270}px;top:{SLOTS["plate_cy"]-205}px;width:540px">{rows(.96)}</div>''')

for name, html in (("A", A), ("B", B), ("C", C)):
    (HERE / f"plate-{name}.html").write_text(html, encoding="utf-8")
print("wrote plate-A.html, plate-B.html, plate-C.html")
