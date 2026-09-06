#!/usr/bin/env python3
"""A1 확정안 — 커틀러리 장식을 하단으로 내리고 FISH 자리 문구를 세 가지로 비교한다.

FISH 는 재료를 지시하는 말이라 업종명 위에 얹히면 엉뚱한 뜻이 붙는다. 자리(코스의 순서)만
가리키거나 무게를 가리키는 말로 바꾼다. 나머지 네 자리는 재료를 말하지 않으므로 그대로 둔다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
sectors = [(p["label"], p["display"]) for p in data["cards"][1]["data_points"]][:5]

CANDIDATES = {
    "second": "SECOND COURSE",  # 자리만 가리킨다. 재료 뜻이 전혀 없어 가장 안전하다.
    "signature": "SIGNATURE",   # 메인 직전의 대표 요리. 2위가 앉는 자리와 무게가 맞는다.
    "intermezzo": "INTERMEZZO", # 실제 코스명이지만 원래는 입가심용 가벼운 요리다.
}

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
         padding: 100px 112px 88px; display: flex; flex-direction: column; text-align: center; }
.serif { font-family: "New York", "Times New Roman", serif; }
.brand { font-size: 25px; letter-spacing: .42em; color: #9A8F7E; }
.house { font-size: 70px; letter-spacing: .06em; }
.tag { font-size: 23px; letter-spacing: .32em; color: #9A8F7E; }
.course { font-size: 23px; letter-spacing: .3em; color: #A2967F; }
.pct { color: #B0576F; font-weight: 600; font-variant-numeric: tabular-nums; }
.foot { display: flex; justify-content: space-between; align-items: center;
        font-size: 22px; color: #9A8F7E; letter-spacing: .05em; }
"""

# 수저 · 포크 · 나이프 순. 셋 다 같은 굵기의 선으로만 그려 종이 위 각인처럼 보이게 둔다.
CUTLERY = ('<svg width="118" height="72" viewBox="0 0 96 58" fill="none" '
           'stroke="#A2967F" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">'
           # 수저 — 타원 볼 + 자루
           '<ellipse cx="14" cy="14" rx="7" ry="10"/><path d="M14 24v30"/>'
           # 포크 — 갈래 셋 + 목 + 자루
           '<path d="M41 5v13M48 5v13M55 5v13"/><path d="M41 18h14"/><path d="M48 18v36"/>'
           # 나이프 — 날 윤곽 + 자루
           '<path d="M78 24V11c0-4 3-7 6-7v20z"/><path d="M81 24v30"/>'
           '</svg>')


def build(slot_label: str) -> str:
    plan = [
        ("AMUSE-BOUCHE", 3),
        ("STARTER", 2),
        (slot_label, 1),
        ("MAIN", 0),
        ("DESSERT", 4),
    ]
    rows = ""
    for label, idx in plan:
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
    return (f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>'
            f'<div class="card"><div class="frame"></div><div class="inner">'
            f'<div class="brand">FINSIGHT</div>'
            f'<div class="house serif" style="margin-top:18px">FIN DINING</div>'
            f'<div class="tag" style="margin-top:16px">오늘의 산업 코스</div>'
            f'<div style="margin-top:34px">{rows}</div>'
            f'<div style="margin-top:auto;padding-bottom:34px">{CUTLERY}</div>'
            f'<div class="foot"><span>2026 · 09 · 06</span><span>KOSPI 업종 등락</span></div>'
            f'</div></div>')


for key, label in CANDIDATES.items():
    (HERE / f"cover-A1-{key}.html").write_text(build(label), encoding="utf-8")
print("wrote", ", ".join(f"cover-A1-{k}.html" for k in CANDIDATES))
