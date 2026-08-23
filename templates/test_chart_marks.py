#!/usr/bin/env python3
"""Chart audit check: a data-driven mark must never cover a chart label.

record() only proves a text run sits inside the container it was handed, and
marks are not registered blocks, so a max-value dot landing on its own number
used to render `4.68` as `68` with the audit still reporting passed. This
rebuilds that geometry and asserts the audit now rejects it.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_adaptive_course as R

SAMPLE = json.loads((Path(__file__).resolve().parent / "sample-course-content.json").read_text(encoding="utf-8"))


def payload(points):
    deck = json.loads(json.dumps(SAMPLE))
    deck["cards"][4]["data_points"] = points
    return deck


def audit(deck, out):
    renderer = R.AdaptiveRenderer(deck, R.make_plan(deck), Path(out))
    try:
        renderer.render()
    except ValueError:
        pass
    return renderer.audit


# Values clustered at the top so the last dot sits at the end of the track.
CLUSTERED = [{"label": f"{m}월", "value": v, "display": str(v)}
             for m, v in zip(range(3, 8), [4.65, 4.66, 4.67, 4.66, 4.68])]
# A long display string pushes the value column left into the bars.
WIDE = [{"label": n, "value": v, "display": d} for n, v, d in
        [("원재료", 92, "1,092억"), ("장비", 108, "1,108억"), ("부품", 104, "1,104억"),
         ("제조", 121, "1,121억"), ("수요", 116, "1,116억")]]

for name, points in (("clustered range-dots", CLUSTERED), ("wide labels rank-bars", WIDE)):
    result = audit(payload(points), f"/tmp/chart-marks-{name.split()[0]}")
    covered = [e for e in result["errors"] if "is covered by mark" in e]
    assert result["passed"], f"{name}: {result['errors']}"
    assert not covered, f"{name}: {covered}"
    assert result["marks"], f"{name}: no marks registered, the check would be vacuous"
    labels = [r["name"] for r in result["records"] if r["name"].startswith("chart_value")]
    assert len(labels) == len(points), f"{name}: {len(labels)} value labels recorded for {len(points)} points"
    print(f"{name:24s} ok  marks={len(result['marks'])} value_labels={len(labels)}")

print("chart marks clear of labels")
