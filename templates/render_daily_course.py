#!/usr/bin/env python3
"""Render one FIN DINING daily carousel from fixed weekday masters.

Usage:
  python render_daily_course.py course-content.json output-directory
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "templates-manifest.json"
PAGE_NAMES = ["cover", "summary", "event", "reason", "data", "impact", "cta"]


def font(path, size, index=0):
    return ImageFont.truetype(path, size=size, index=index)


def wrap(draw, value, font_obj, max_width, max_lines):
    words = value.split()
    if not words:
        return ""
    lines, current = [], ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == max_lines:
            raise ValueError(f"copy exceeds {max_lines} lines: {value}")
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        raise ValueError(f"copy exceeds {max_lines} lines: {value}")
    return "\n".join(lines)


def draw_wrapped(draw, xy, value, font_obj, fill, max_width, max_lines, spacing=8):
    rendered = wrap(draw, value, font_obj, max_width, max_lines)
    draw.multiline_text(xy, rendered, font=font_obj, fill=fill, spacing=spacing)


def require_list(value, length, label):
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} must contain exactly {length} items")
    return value


def render(payload, output_dir):
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    day_key = payload["day_key"]
    if day_key not in manifest["templates"]:
        raise ValueError(f"unknown day_key: {day_key}")
    entry = manifest["templates"][day_key]
    layout = json.loads((ROOT.parent / entry["layout"]).read_text(encoding="utf-8"))
    folder = ROOT.parent / entry["directory"]
    colors = layout["colors"]
    sans_path = layout["fonts"]["korean"]["path"]
    serif_path = layout["fonts"]["display"]["path"]

    body = font(sans_path, 32, 0)
    body_small = font(sans_path, 30, 0)
    title = font(sans_path, 56, 6)
    cover_title = font(sans_path, 66, 6)
    label = font(sans_path, 28, 4)
    number = font(serif_path, 36)
    date_font = font(sans_path, 24, 0)
    accent_ink = colors.get("accentInk", colors["accent"])
    muted = colors.get("muted", "#B0A79B")

    cards = require_list(payload["cards"], 7, "cards")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for page, name in enumerate(PAGE_NAMES, 1):
        master = Image.open(folder / f"{page:02d}_{name}_master.png").convert("RGB")
        draw = ImageDraw.Draw(master)
        card = cards[page - 1]

        # Replace the baked DATE placeholder without touching any other fixed element.
        draw.rectangle((70, 1192, 300, 1245), fill=colors["background"])
        draw.text((72, 1214), f'{payload["date"]} · KST', font=date_font, fill=muted)

        if page == 1:
            draw.text((72, 236), card.get("eyebrow", layout["label"]), font=label, fill=colors["accent"])
            draw_wrapped(draw, (72, 296), card["headline"], cover_title, colors["ivory"], 500, 3, 10)
            draw_wrapped(draw, (72, 592), card["subheadline"], body_small, muted, 500, 2)
        else:
            draw.text((72, 230), card["section"], font=number, fill=colors["accent"])
            draw_wrapped(draw, (72, 276), card["headline"], title, colors["ivory"], 900, 2)

        if page == 2:
            items = require_list(card["items"], 3, "summary.items")
            for i, (item, y) in enumerate(zip(items, (430, 630, 830)), 1):
                draw.text((110, y), f"0{i}", font=number, fill=accent_ink)
                draw_wrapped(draw, (194, y + 2), item, body, colors["ink"], 750, 3)
        elif page == 3:
            items = require_list(card["items"], 3, "event.items")
            for item, y in zip(items, (515, 679, 843)):
                draw_wrapped(draw, (236, y), item, body, colors["ink"], 690, 3)
        elif page == 4:
            items = require_list(card["items"], 3, "reason.items")
            for i, (item, y) in enumerate(zip(items, (445, 635, 825)), 1):
                draw.text((128, y + 30), str(i), font=label, fill="#FFFBF4", anchor="mm")
                draw_wrapped(draw, (194, y), item, body, colors["ink"], 735, 3)
        elif page == 5:
            points = require_list(card["data_points"], 5, "data.data_points")
            values = [float(point["value"]) for point in points]
            low, high = min(values), max(values)
            span = high - low or 1.0
            xs = [258, 426, 594, 762, 930]
            plotted = []
            for x, point, value in zip(xs, points, values):
                y = round(875 - ((value - low) / span) * 330)
                plotted.append((x, y))
                draw.text((x, 906), point["label"], font=label, fill=colors["ink"], anchor="ma")
                draw.text((x, y - 28), point["display"], font=label, fill=accent_ink, anchor="ms")
            draw.line(plotted, fill=accent_ink, width=9, joint="curve")
            for x, y in plotted:
                draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=colors["accent2"])
            draw_wrapped(draw, (154, 450), card["note"], body_small, colors["ink"], 780, 2)
        elif page == 6:
            items = require_list(card["items"], 3, "impact.items")
            for index, (item, y) in enumerate(zip(items, (395, 610, 825)), 1):
                draw.ellipse((100, y + 25, 148, y + 73), fill=accent_ink)
                draw.text((124, y + 49), f"{index:02d}", font=date_font, fill=colors["paper"], anchor="mm")
                draw_wrapped(draw, (176, y + 31), item["name"], body, colors["ink"], 760, 1)

                opportunity = f'기회 · {item["opportunity"]}'
                risk = f'리스크 · {item["risk"]}'
                opportunity_width = draw.textbbox((0, 0), opportunity, font=body_small)[2]
                risk_width = draw.textbbox((0, 0), risk, font=body_small)[2]
                if opportunity_width <= 385 and risk_width <= 405:
                    draw.rounded_rectangle((100, y + 105, 518, y + 158), radius=16, fill="#E8EFE9")
                    draw.rounded_rectangle((540, y + 105, 980, y + 158), radius=16, fill="#F2E6E5")
                    draw.text((116, y + 112), opportunity, font=body_small, fill="#416B52")
                    draw.text((556, y + 112), risk, font=body_small, fill="#8B4A49")
                else:
                    draw.rounded_rectangle((100, y + 83, 980, y + 121), radius=14, fill="#E8EFE9")
                    draw.rounded_rectangle((100, y + 128, 980, y + 166), radius=14, fill="#F2E6E5")
                    draw.text((116, y + 84), opportunity, font=body_small, fill="#416B52")
                    draw.text((116, y + 129), risk, font=body_small, fill="#8B4A49")
        elif page == 7:
            checklist = require_list(card["checklist"], 4, "cta.checklist")
            for item, y in zip(checklist, (430, 518, 606, 694)):
                draw.text((123, y + 23), "✓", font=label, fill=accent_ink, anchor="mm")
                draw_wrapped(draw, (178, y + 5), item, body_small, colors["ink"], 760, 2)
            draw.text((540, 938), card["cta"], font=body_small, fill="#FFFBF4", anchor="mm")
            draw_wrapped(draw, (72, 1050), "출처 · " + " · ".join(card["sources"]), label, muted, 920, 2)

        filename = f'{payload["date"]}_{day_key.upper().replace("-", "_")}_{page:02d}_{name}.png'
        master.save(output_dir / filename, "PNG", optimize=True)
        outputs.append(output_dir / filename)

    thumb_w, thumb_h = 270, 338
    preview = Image.new("RGB", (thumb_w * 4 + 36 * 5, thumb_h * 2 + 60 * 3), colors["background"])
    for i, path in enumerate(outputs):
        image = Image.open(path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = 36 + (i % 4) * (thumb_w + 36)
        y = 36 + (i // 4) * (thumb_h + 60)
        preview.paste(image, (x, y))
    preview_path = output_dir / f'{payload["date"]}_{day_key}_preview.png'
    preview.save(preview_path, "PNG", optimize=True)
    return outputs, preview_path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: render_daily_course.py course-content.json output-directory")
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    outputs, preview = render(payload, Path(sys.argv[2]))
    print(json.dumps({"images": [str(path) for path in outputs], "preview": str(preview)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
