#!/usr/bin/env python3
"""메뉴판 커버 A안 변주 — 코스 위계와 등락 순위를 맞춘 3종.

A안의 문제는 코스명(AMUSE→DESSERT)은 요리의 무게 순서인데 그 자리에 앉힌 업종은 등락 순위라
두 위계가 서로를 배반한 것이었다. 여기서는 코스를 무게 순서로 두되 1위를 MAIN 에 앉히고,
나머지를 메인으로 올라가는 크레센도와 가벼운 마무리에 나눠 담는다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
sectors = [(p["label"], p["display"]) for p in data["cards"][1]["data_points"]][:5]

# 인쇄 순서는 실제 코스 순서 그대로. 자리에 앉는 업종은 등락 순위로, 정점인 MAIN 에 1위가 온다.
# 읽어 내려가면 4위 → 3위 → 2위 → 1위로 올라갔다가 5위로 가볍게 닫힌다.
PLAN = [
    ("AMUSE-BOUCHE", "한 입", 3),
    ("STARTER", "전채", 2),
    ("FISH", "생선", 1),
    ("MAIN", "메인", 0),
    ("DESSERT", "디저트", 4),
]

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
.card {
  width: 1080px; height: 1350px; position: relative;
  background: #FBF7EF; color: #1F1B16;
  font-family: "Apple SD Gothic Neo", sans-serif;
}
.card::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(ellipse at 22% 18%, rgba(198,178,140,.10), transparent 55%),
    radial-gradient(ellipse at 80% 82%, rgba(198,178,140,.08), transparent 55%);
}
.frame { position: absolute; inset: 46px; border: 2px solid #C9BCA4; }
.frame::after { content: ""; position: absolute; inset: 9px; border: 1px solid #D8CEBB; }
.inner { position: relative; z-index: 2; height: 100%;
         padding: 100px 112px; display: flex; flex-direction: column; }
.serif { font-family: "New York", "Times New Roman", serif; }
.brand { font-size: 25px; letter-spacing: .42em; color: #9A8F7E; }
.house { font-size: 70px; letter-spacing: .06em; }
.tag { font-size: 23px; letter-spacing: .32em; color: #9A8F7E; }
.course { font-size: 23px; letter-spacing: .3em; color: #A2967F; }
.name { font-size: 40px; font-weight: 600; }
.pct { color: #B0576F; font-weight: 600; font-variant-numeric: tabular-nums; }
.rank { font-size: 21px; color: #BCAF95; letter-spacing: .16em; }
.foot { margin-top: auto; display: flex; justify-content: space-between; align-items: center;
        font-size: 22px; color: #9A8F7E; letter-spacing: .05em; }
.hr { height: 1px; background: #D5C9B4; }
"""

# 세 갈래 3개 + 목 + 손잡이. 이전 시안의 장식은 경로가 엉켜 깨져 나왔다.
FORK = ('<svg width="26" height="62" viewBox="0 0 20 56" fill="none" '
        'stroke="#A2967F" stroke-width="1.3" stroke-linecap="round">'
        '<path d="M3 4v13M10 4v13M17 4v13"/><path d="M3 17h14"/><path d="M10 17v35"/></svg>')


def ornament(width: int = 150) -> str:
    return (f'<div style="display:flex;align-items:center;justify-content:center;gap:22px">'
            f'<div class="hr" style="width:{width}px"></div>{FORK}'
            f'<div class="hr" style="width:{width}px"></div></div>')


def page(body: str) -> str:
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="card"><div class="frame"></div><div class="inner">{body}</div></div>')


HEAD = """
<div style="text-align:center">
  <div class="brand">FINSIGHT</div>
  <div class="house serif" style="margin-top:18px">FIN DINING</div>
  <div class="tag" style="margin-top:16px">오늘의 산업 코스</div>
</div>
"""

# A1 — 코스만 크레센도로 배치하고 MAIN 한 줄만 키운다. 순위 숫자는 적지 않는다.
rows_1 = ""
for label, _, idx in PLAN:
    name, pct = sectors[idx]
    main = label == "MAIN"
    rows_1 += (
        f'<div style="margin-top:{34 if main else 30}px;'
        f'{"padding:22px 0;border-top:1px solid #D5C9B4;border-bottom:1px solid #D5C9B4;" if main else ""}">'
        f'<div class="course serif" style="{"color:#8A7F6C;" if main else ""}">{label}</div>'
        f'<div style="display:flex;justify-content:center;align-items:baseline;gap:16px;margin-top:10px">'
        f'<span class="name" style="font-size:{52 if main else 38}px">{name}</span>'
        f'<span class="pct" style="font-size:{44 if main else 32}px">{pct}</span>'
        f'</div></div>')
A1 = page(f'{HEAD}<div style="text-align:center;margin-top:34px">{rows_1}</div>'
          f'<div style="margin-top:44px">{ornament()}</div>'
          f'<div class="foot"><span>2026 · 09 · 06</span><span>KOSPI 업종 등락</span></div>')

# A2 — A1 과 같은 배치에 순위를 작게 병기한다. 코스는 무게, 배지는 데이터로 역할을 갈라 둔다.
rows_2 = ""
for label, ko, idx in PLAN:
    name, pct = sectors[idx]
    main = label == "MAIN"
    rows_2 += (
        f'<div style="display:flex;align-items:center;gap:26px;margin-top:{26 if main else 22}px;'
        f'{"padding:20px 0;border-top:1px solid #D5C9B4;border-bottom:1px solid #D5C9B4;" if main else ""}">'
        f'<div style="width:190px;text-align:left">'
        f'<div class="course serif">{label}</div>'
        f'<div class="rank" style="margin-top:6px">등락 {idx + 1}위</div></div>'
        f'<div class="name" style="font-size:{50 if main else 38}px;flex:1">{name}</div>'
        f'<div class="pct" style="font-size:{44 if main else 33}px">{pct}</div></div>')
A2 = page(f'{HEAD}<div style="margin-top:40px">{rows_2}</div>'
          f'<div style="margin-top:40px">{ornament(180)}</div>'
          f'<div class="foot"><span>2026 · 09 · 06</span><span>KOSPI 업종 등락 상위 5</span></div>')

# A3 — 메인을 먼저 크게 내어 놓고 나머지 네 코스를 곁들임처럼 아래에 깐다.
lead_name, lead_pct = sectors[0]
sides = ""
for label, _, idx in PLAN:
    if label == "MAIN":
        continue
    name, pct = sectors[idx]
    sides += (f'<div style="width:50%;padding:20px 0">'
              f'<div class="course serif" style="font-size:21px">{label}</div>'
              f'<div style="display:flex;align-items:baseline;gap:12px;margin-top:8px">'
              f'<span class="name" style="font-size:32px">{name}</span>'
              f'<span class="pct" style="font-size:27px">{pct}</span></div></div>')
A3 = page(f"""{HEAD}
<div style="text-align:center;margin-top:52px">
  <div class="course serif" style="color:#8A7F6C">MAIN COURSE</div>
  <div class="name serif" style="font-size:66px;margin-top:20px;letter-spacing:-.01em">{lead_name}</div>
  <div class="pct" style="font-size:56px;margin-top:14px">{lead_pct}</div>
</div>
<div style="margin-top:44px">{ornament(190)}</div>
<div style="display:flex;flex-wrap:wrap;margin-top:26px;text-align:center">{sides}</div>
<div class="foot"><span>2026 · 09 · 06</span><span>KOSPI 업종 등락</span></div>
""")

for name, html in (("A1", A1), ("A2", A2), ("A3", A3)):
    (HERE / f"cover-{name}.html").write_text(html, encoding="utf-8")
print("wrote cover-A1.html, cover-A2.html, cover-A3.html")
