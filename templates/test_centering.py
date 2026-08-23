#!/usr/bin/env python3
"""Glyph centering check: marks drawn inside circles and badges must sit on the
geometric centre, not 1-2px high the way Pillow's "mm" anchor leaves them."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_adaptive_course import F_BODY, F_LABEL, F_LEGAL, draw_centered

CASES = [
    ("event badge", "01", F_LEGAL, (540, 400)),
    ("reason node", "3", F_LABEL, (130, 480)),
    ("impact dot", "●", F_LEGAL, (123, 451)),
    ("checklist tick", "✓", F_LABEL, (124, 465)),
    ("calendar date", "8/26", F_LEGAL, (195, 477)),
    ("cta banner", "댓글로 다음 코스를\n예약해 주세요", F_BODY, (540, 923)),
]

draw = ImageDraw.Draw(Image.new("RGB", (1080, 1350)))
for name, text, font_obj, center in CASES:
    box = draw_centered(draw, center, text, font_obj, "#FFFFFF", align="center")
    off = ((box[0] + box[2]) / 2 - center[0], (box[1] + box[3]) / 2 - center[1])
    assert abs(off[0]) <= 0.5 and abs(off[1]) <= 0.5, f"{name} off by {off}"
    print(f"{name:16s} ok  offset={off}")
print("all centered")
