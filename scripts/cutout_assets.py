#!/usr/bin/env python3
"""원본 일러스트에서 셰프와 식기를 떼어 투명 PNG 로 저장한다.

`assets/` 의 원화는 배경(도트 패턴·스캘럽 테두리)과 장식(마카롱·반짝이·하트)이 함께 그려진 한 장이다.
카드에 올리려면 대상만 남긴 알파 채널이 필요하다.

## 어떻게 떼어내는가
배경이 단색이 아니라 옅은 도트 패턴이라 색 하나로는 못 지운다. 대신 대상이 전부 진한 윤곽선으로
닫혀 있다는 점을 쓴다.

1. 테두리 여러 지점에서 flood fill 을 시작한다. 채우기는 윤곽선에 막혀 대상 안으로 못 들어간다.
2. 채워지지 않고 남은 픽셀을 연결 요소로 나눠 **가장 큰 덩어리만** 남긴다. 손에 든 도구와 발밑
   그림자는 대상에 붙어 있어 살아남고, 떨어져 있는 장식은 걸러진다.
3. 윤곽선 바깥에 한 겹 남는 배경을 깎아 가장자리 후광을 없앤다.

새 아트로 교체할 때도 CROPS 의 잘라낼 영역만 고치면 된다.

    python3 scripts/cutout_assets.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "templates/assets"

# 배경으로 칠할 표식 — 원본에 없는 색이어야 마스크로 쓸 수 있다.
MARK = (255, 0, 255)

SOURCES = {
    "fin-dining-chefs.png": {
        # 곰과 황소가 나란히 서 있다. 아래쪽 커틀러리 줄(y≈878~)은 잘라 낸다.
        "threshold": 62,
        "crops": {"chef-bear": (52, 130, 520, 878), "chef-bull": (510, 95, 1015, 878)},
    },
    "fin-dining-cutlery.png": {
        # 수저 · 젓가락 · 포크 · 나이프 순으로 서 있다. 접시 옆에 쓸 둘만 뗀다.
        "threshold": 60,
        "crops": {"cutlery-fork": (560, 200, 730, 840), "cutlery-knife": (760, 200, 910, 840)},
    },
}


def largest_component(solid: bytearray, w: int, h: int) -> tuple[bytearray, int, int]:
    """남은 픽셀을 4-이웃 연결 요소로 나누고, 가장 큰 덩어리의 라벨을 돌려준다."""
    label = bytearray(w * h)
    best_size = best_id = next_id = 0
    for start in range(w * h):
        if not solid[start] or label[start]:
            continue
        next_id += 1
        if next_id > 255:
            break  # 라벨을 1바이트로 유지하기 위한 방어. 실무상 도달하지 않는다.
        stack, size = [start], 0
        label[start] = next_id
        while stack:
            i = stack.pop()
            size += 1
            x, y = i % w, i // w
            for j, ok in ((i - 1, x > 0), (i + 1, x < w - 1), (i - w, y > 0), (i + w, y < h - 1)):
                if ok and solid[j] and not label[j]:
                    label[j] = next_id
                    stack.append(j)
        if size > best_size:
            best_size, best_id = size, next_id
    return label, best_id, best_size


def cut(src: Image.Image, box: tuple[int, int, int, int], threshold: int) -> Image.Image:
    tile = src.crop(box)
    w, h = tile.size

    work = tile.copy()
    seeds = [(x, y) for x in range(0, w, 6) for y in (0, h - 1)]
    seeds += [(x, y) for y in range(0, h, 6) for x in (0, w - 1)]
    for seed in seeds:
        if work.getpixel(seed) != MARK:
            ImageDraw.floodfill(work, seed, MARK, thresh=threshold)

    px = work.load()
    solid = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            if px[x, y] != MARK:
                solid[y * w + x] = 1

    label, best_id, size = largest_component(solid, w, h)
    if not best_id:
        # 윤곽선이 옅어 flood fill 이 대상 안까지 들어간 경우다. 이대로 두면 라벨 0(=배경)이 통째로
        # 불투명해져 사각형 이미지가 나온다. 조용히 잘못된 에셋을 내보내느니 멈춘다.
        raise ValueError(f"배경을 지우고 남은 것이 없다 — threshold 를 낮춰야 한다 (crop {box})")
    if size < (w * h) * 0.03:
        raise ValueError(f"남은 덩어리가 너무 작다({size:,}px) — crop 영역이 빗나갔을 수 있다 {box}")
    alpha = Image.new("L", (w, h), 0)
    ap = alpha.load()
    for i in range(w * h):
        if label[i] == best_id:
            ap[i % w, i // w] = 255
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.5))

    out = tile.convert("RGBA")
    out.putalpha(alpha)
    bbox = out.getbbox()
    return out.crop(bbox) if bbox else out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, spec in SOURCES.items():
        src = Image.open(ROOT / "assets" / filename).convert("RGB")
        for name, box in spec["crops"].items():
            art = cut(src, box, spec["threshold"])
            art.save(OUT / f"{name}.png")
            print(f"{name}.png {art.size}")


if __name__ == "__main__":
    main()
