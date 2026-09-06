#!/usr/bin/env python3
"""밝은 파인다이닝 메뉴판 커버 시안 — HTML 4종.

Pillow 렌더러에 옮기기 전에 방향을 고르기 위한 목업이다. 폰트는 실제 렌더러와 같은 macOS
시스템 폰트(New York / Apple SD Gothic Neo)를 브라우저에서 그대로 부른다.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent.parent / "outputs/2026-09-06_sat-preview/course-content.json"

data = json.loads(CONTENT.read_text(encoding="utf-8"))
sectors = [(p["label"], p["display"]) for p in data["cards"][1]["data_points"]][:5]
leads = [(card["eyebrow"].split()[1], card["data_points"][0]["label"], card["data_points"][0]["display"].split()[-1])
         for card in data["cards"][2:]]

CSS = """
@font-face { font-family: "NY"; src: local("New York"); }
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #fff; }
.card {
  width: 1080px; height: 1350px; position: relative;
  background: #FBF7EF; color: #1F1B16;
  font-family: "Apple SD Gothic Neo", sans-serif;
  display: flex; flex-direction: column;
}
/* 크림 종이의 결 — 아주 옅은 얼룩 두 겹. */
.card::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(ellipse at 22% 18%, rgba(198,178,140,.10), transparent 55%),
    radial-gradient(ellipse at 80% 82%, rgba(198,178,140,.08), transparent 55%);
}
.serif { font-family: "New York", "Times New Roman", serif; }
.frame { position: absolute; inset: 46px; border: 2px solid #C9BCA4; }
.frame::after { content: ""; position: absolute; inset: 9px; border: 1px solid #D8CEBB; }
.inner { position: relative; z-index: 2; height: 100%;
         padding: 108px 118px; display: flex; flex-direction: column; }
.brand { font-size: 26px; letter-spacing: .42em; color: #9A8F7E; text-transform: uppercase; }
.house { font-size: 76px; letter-spacing: .06em; line-height: 1.05; }
.tag { font-size: 24px; letter-spacing: .34em; color: #9A8F7E; text-transform: uppercase; }
.rule { height: 1px; background: #CFC3AC; }
.date { font-size: 25px; color: #8C8172; letter-spacing: .03em; }
.foot { margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end;
        font-size: 22px; color: #9A8F7E; letter-spacing: .05em; }
.pct { color: #B0576F; font-weight: 600; font-variant-numeric: tabular-nums; }
.fork { width: 190px; opacity: .5; }
"""

FORK = ('<svg class="fork" viewBox="0 0 200 26" fill="none" stroke="#8C8172" stroke-width="1.4">'
        '<path d="M4 13h150M158 6c8 0 12 3 12 7s-4 7-12 7M166 13h30"/>'
        '<path d="M14 6v14M22 6v14M30 6v14M14 13h16"/></svg>')


def page(title: str, body: str) -> str:
    return (f'<!doctype html><meta charset="utf-8"><title>{title}</title>'
            f'<style>{CSS}</style><div class="card"><div class="frame"></div>'
            f'<div class="inner">{body}</div></div>')


# A — 참조 이미지 정통형. 중앙 정렬, 코스 섹션 이름 아래 업종을 요리처럼 세운다.
courses = ["AMUSE-BOUCHE", "STARTER", "FISH", "MAIN", "DESSERT"]
rows_a = "".join(
    f'<div style="margin-top:44px">'
    f'<div class="serif" style="font-size:25px;letter-spacing:.3em;color:#9A8F7E">{course}</div>'
    f'<div style="display:flex;justify-content:center;align-items:baseline;gap:18px;margin-top:12px">'
    f'<span style="font-size:41px;font-weight:600">{name}</span>'
    f'<span class="pct" style="font-size:34px">{pct}</span></div></div>'
    for course, (name, pct) in zip(courses, sectors))
A = page("A", f"""
<div style="text-align:center">
  <div class="brand">Finsight</div>
  <div class="house serif" style="margin-top:20px">FIN DINING</div>
  <div class="tag" style="margin-top:18px">오늘의 산업 코스</div>
  <div class="rule" style="width:200px;margin:52px auto 0"></div>
  {rows_a}
  <div style="margin-top:64px">{FORK}</div>
</div>
<div class="foot"><span>2026 · 09 · 06</span><span>KOSPI 업종 등락</span></div>
""")

# B — 가격표처럼 점선 리더로 이름과 등락률을 잇는다. 좌측 정렬이라 이름이 길어도 안 깨진다.
rows_b = "".join(
    f'<div style="display:flex;align-items:baseline;gap:16px;margin-top:38px">'
    f'<span class="serif" style="font-size:29px;color:#B6A98F;width:52px">{i:02d}</span>'
    f'<span style="font-size:42px;font-weight:600;white-space:nowrap">{name}</span>'
    f'<span style="flex:1;border-bottom:1.5px dotted #CBBFA8;transform:translateY(-9px)"></span>'
    f'<span class="pct" style="font-size:36px">{pct}</span></div>'
    for i, (name, pct) in enumerate(sectors, 1))
B = page("B", f"""
<div style="display:flex;justify-content:space-between;align-items:flex-start">
  <div>
    <div class="brand">Finsight</div>
    <div class="house serif" style="margin-top:18px;font-size:64px">FIN DINING</div>
  </div>
  <div class="serif" style="font-size:27px;color:#9A8F7E;text-align:right;line-height:1.6">
    COURSE 06<br>2026.09.06</div>
</div>
<div class="rule" style="margin-top:44px"></div>
<div class="tag" style="margin-top:44px">TODAY'S TASTING · 오늘의 산업 코스</div>
{rows_b}
<div class="foot">{FORK}<span>KOSPI 업종 등락 상위 5</span></div>
""")

# C — 접시를 커버에도 세운다. 2장 이후 카드와 같은 원형 언어로 시작해 코스가 이어지는 느낌.
ring = "".join(
    f'<div style="position:absolute;left:50%;top:50%;'
    f'transform:rotate({-90 + i * 72}deg) translate(300px) rotate({90 - i * 72}deg);'
    f'margin:-26px 0 0 -80px;width:160px;text-align:center">'
    f'<div style="font-size:25px;font-weight:600;white-space:nowrap">{name}</div>'
    f'<div class="pct" style="font-size:23px;margin-top:4px">{pct}</div></div>'
    for i, (name, pct) in enumerate(sectors))
C = page("C", f"""
<div style="text-align:center">
  <div class="brand">Finsight</div>
  <div class="house serif" style="margin-top:16px;font-size:62px">FIN DINING</div>
</div>
<div style="position:relative;flex:1;margin-top:26px">
  <div style="position:absolute;left:50%;top:50%;width:800px;height:800px;margin:-400px 0 0 -400px;
              border:1px solid #DCD2BF;border-radius:50%"></div>
  <div style="position:absolute;left:50%;top:50%;width:392px;height:392px;margin:-196px 0 0 -196px;
              border-radius:50%;background:#F5EFE2;border:1px solid #DCD2BF;
              box-shadow:0 20px 46px rgba(140,120,86,.16);
              display:flex;flex-direction:column;align-items:center;justify-content:center">
    <div class="serif" style="font-size:23px;letter-spacing:.3em;color:#9A8F7E">TODAY</div>
    <div style="font-size:44px;font-weight:700;margin-top:14px">{sectors[0][0]}</div>
    <div class="pct" style="font-size:40px;margin-top:8px">{sectors[0][1]}</div>
  </div>
  {ring}
</div>
<div class="foot"><span>2026 · 09 · 06</span><span>오늘의 산업 코스 5선</span></div>
""")

# D — 표지는 한 마디만. 코스 목록은 아래 한 줄로 접어 다음 장을 열어두는 구성.
strip = '<span style="color:#CBBFA8;margin:0 14px">·</span>'.join(
    f'<span style="white-space:nowrap">{name}</span>' for name, _ in sectors)
D = page("D", f"""
<div style="display:flex;justify-content:space-between;align-items:baseline">
  <div class="brand">Finsight</div>
  <div class="serif" style="font-size:25px;color:#9A8F7E">COURSE 06</div>
</div>
<div style="margin-top:auto">
  <div class="tag">2026.09.06 · 업종 등락 랭킹</div>
  <div class="serif" style="font-size:104px;line-height:1.14;margin-top:30px">오늘<br>뜨는 산업</div>
  <div style="display:flex;align-items:baseline;gap:20px;margin-top:44px">
    <span style="font-size:44px;font-weight:600">{sectors[0][0]}</span>
    <span class="pct" style="font-size:44px">{sectors[0][1]}</span>
  </div>
</div>
<div style="margin-top:auto">
  <div class="rule" style="margin-bottom:26px"></div>
  <div style="font-size:26px;color:#8C8172;letter-spacing:.02em">{strip}</div>
</div>
<div class="foot" style="margin-top:40px">{FORK}<span>FIN DINING</span></div>
""")

for name, html in (("A", A), ("B", B), ("C", C), ("D", D)):
    (HERE / f"cover-{name}.html").write_text(html, encoding="utf-8")
print("wrote", ", ".join(f"cover-{n}.html" for n in "ABCD"))
