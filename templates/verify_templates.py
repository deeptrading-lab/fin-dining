#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageFont

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
PYTHON = sys.executable
EXPECTED = ["mon-policy", "tue-global", "wed-market", "thu-industry", "fri-weekly", "sat-preview"]
PAGES = ["cover", "summary", "event", "reason", "data", "impact", "cta"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot():
    return {
        f"{day}/{page:02d}_{name}_master.png": digest(ROOT / day / f"{page:02d}_{name}_master.png")
        for day in EXPECTED
        for page, name in enumerate(PAGES, 1)
    }


def inspect_files(manifest):
    checks = []
    checks.append((manifest["brand"] == "FIN DINING by Finsight", "brand is current"))
    checks.append((manifest["version"] == "4.1", "manifest version is v4.1"))
    checks.append((manifest["mode"] == "concept-locked-adaptive", "adaptive mode is active"))
    checks.append((manifest["renderer"] == "templates/render_adaptive_course.py", "adaptive renderer is default"))
    checks.append((manifest["cardRange"] == [5, 7], "adaptive card range is 5-7"))
    checks.append((manifest["week"] == EXPECTED, "manifest contains Monday-Saturday in order"))
    checks.append((set(manifest["templates"]) == set(EXPECTED), "manifest contains exactly six templates"))
    for day in EXPECTED:
        entry = manifest["templates"][day]
        layout = json.loads((PROJECT / entry["layout"]).read_text(encoding="utf-8"))
        checks.append((layout["brand"] == manifest["brand"], f"{day}: brand matches"))
        checks.append((layout["canvas"] == {"width": 1080, "height": 1350}, f"{day}: canvas declaration"))
        for font_spec in layout["fonts"].values():
            font_path = Path(font_spec["path"])
            checks.append((font_path.exists(), f"{day}: font exists: {font_path.name}"))
            if font_path.exists():
                ImageFont.truetype(str(font_path), size=28)
        for page, name in enumerate(PAGES, 1):
            path = ROOT / day / f"{page:02d}_{name}_master.png"
            image = Image.open(path)
            checks.append((image.size == (1080, 1350), f"{day}/{page}: 1080x1350"))
            checks.append((image.mode == "RGB", f"{day}/{page}: RGB"))
            checks.append((digest(path) == layout["masterSha256"][path.name], f"{day}/{page}: SHA-256 matches layout"))
        preview = PROJECT / entry["preview"]
        checks.append((preview.exists(), f"{day}: preview exists"))
    checks.append(((ROOT / "all-weekday-master-preview.png").exists(), "3x2 weekly preview exists"))
    return checks


rounds = []
baseline = None
for round_number in range(1, 4):
    result = subprocess.run([PYTHON, str(ROOT / "render_master_templates.py")], cwd=PROJECT, capture_output=True, text=True)
    current = snapshot() if result.returncode == 0 else {}
    stable = result.returncode == 0 and (baseline is None or current == baseline)
    if baseline is None and current:
        baseline = current
    rounds.append({"round": round_number, "rendererExitCode": result.returncode, "stableAgainstRound1": stable, "stderr": result.stderr.strip()})

manifest = json.loads((ROOT / "templates-manifest.json").read_text(encoding="utf-8"))
checks = inspect_files(manifest)
passed = all(item[0] for item in checks) and all(item["stableAgainstRound1"] for item in rounds)
report = {
    "brand": "FIN DINING by Finsight",
    "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
    "passed": passed,
    "renderRounds": rounds,
    "checks": [{"passed": ok, "name": name} for ok, name in checks],
    "masterCount": len(snapshot()),
}
(ROOT / "qa-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
raise SystemExit(0 if passed else 1)
