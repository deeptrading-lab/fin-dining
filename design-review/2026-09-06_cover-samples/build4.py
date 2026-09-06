#!/usr/bin/env python3
"""커버 확정안(A1 · SIGNATURE) — 종이 밝기 3단 비교.

바꾸는 값은 배경색 하나뿐이다. 테두리·괘선·글자색은 고정해 밝기 차이만 보이게 둔다.
커틀러리는 이전 시안에서 너무 작아 보여 한 단계 키웠다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
sectors = [(p["label"], p["display"]) for p in data["cards"][1]["data_points"]][:5]

PLAN = [("AMUSE-BOUCHE", 3), ("STARTER", 2), ("SIGNATURE", 1), ("MAIN", 0), ("DESSERT", 4)]

PAPERS = {
    "0-current": "#FBF7EF",  # 지금 시안
    "1-lighter": "#FDFAF4",  # 한 단계 밝게
    "2-lightest": "#FEFCF8",  # 두 단계 — 거의 흰 종이
}

CUTLERY = ('<svg width="150" height="92" viewBox="0 0 96 58" fill="none" '
           'stroke="#A2967F" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">'
           '<ellipse cx="14" cy="14" rx="7" ry="10"/><path d="M14 24v30"/>'
           '<path d="M41 5v13M48 5v13M55 5v13"/><path d="M41 18h14"/><path d="M48 18v36"/>'
           '<path d="M78 24V11c0-4 3-7 6-7v20z"/><path d="M81 24v30"/>'
           '</svg>')


def build(paper: str) -> str:
    css = f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
.card {{
  width: 1080px; height: 1350px; position: relative;
  background: {paper}; color: #1F1B16;
  font-family: "Apple SD Gothic Neo", sans-serif;
}}
.card::before {{
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(ellipse at 22% 18%, rgba(198,178,140,.10), transparent 55%),
    radial-gradient(ellipse at 80% 82%, rgba(198,178,140,.08), transparent 55%);
}}
.frame {{ position: absolute; inset: 46px; border: 2px solid #C9BCA4; }}
.frame::after {{ content: ""; position: absolute; inset: 9px; border: 1px solid #D8CEBB; }}
.inner {{ position: relative; z-index: 2; height: 100%;
         padding: 100px 112px 88px; display: flex; flex-direction: column; text-align: center; }}
.serif {{ font-family: "New York", "Times New Roman", serif; }}
.brand {{ font-size: 25px; letter-spacing: .42em; color: #9A8F7E; }}
.house {{ font-size: 70px; letter-spacing: .06em; }}
.tag {{ font-size: 23px; letter-spacing: .32em; color: #9A8F7E; }}
.course {{ font-size: 23px; letter-spacing: .3em; color: #A2967F; }}
.pct {{ color: #B0576F; font-weight: 600; font-variant-numeric: tabular-nums; }}
.foot {{ display: flex; justify-content: space-between; align-items: center;
        font-size: 22px; color: #9A8F7E; letter-spacing: .05em; }}
"""
    rows = ""
    for label, idx in PLAN:
        name, pct = sectors[idx]
        main = label == "MAIN"
        rows += (
            f'<div style="margin-top:{34 if main else 30}px;'
            f'{"padding:22px 0;border-top:1px solid #D5C9B4;border-bottom:1px solid #D5C9B4;" if main else ""}">'
            f'<div class="course serif" style="{"color:#8A7F6C;" if main else ""}">{label}</div>'
            f'<div style="display:flex;justify-content:center;align-items:baseline;gap:16px;margin-top:10px">'
            f'<span style="font-size:{52 if main else 38}px;font-weight:600">{name}</span>'
            f'<span class="pct" style="font-size:{44 if main else 32}px">{pct}</span>'
            f'</div></div>')
    return (f'<!doctype html><meta charset="utf-8"><style>{css}</style>'
            f'<div class="card"><div class="frame"></div><div class="inner">'
            f'<div class="brand">FINSIGHT</div>'
            f'<div class="house serif" style="margin-top:18px">FIN DINING</div>'
            f'<div class="tag" style="margin-top:16px">오늘의 산업 코스</div>'
            f'<div style="margin-top:34px">{rows}</div>'
            f'<div style="margin-top:auto;padding-bottom:26px">{CUTLERY}</div>'
            f'<div class="foot"><span>2026 · 09 · 06</span><span>KOSPI 업종 등락</span></div>'
            f'</div></div>')


for key, paper in PAPERS.items():
    (HERE / f"paper-{key}.html").write_text(build(paper), encoding="utf-8")
print("wrote", ", ".join(f"paper-{k}.html" for k in PAPERS))
