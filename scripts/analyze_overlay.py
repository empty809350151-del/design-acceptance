#!/usr/bin/env python3
"""Generate masked overlay metrics, heatmap, mask, and anchored font evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter


def load_image(path: Path, viewport: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    width, height = viewport
    if image.width < width or image.height < height:
        raise ValueError(f"{path} is {image.size}, smaller than viewport {viewport}")
    return image.crop((0, 0, width, height))


def line_bands(mask: np.ndarray) -> list[tuple[int, int]]:
    rows = (mask.sum(axis=1) >= 3).astype(np.uint8)
    for index in range(1, len(rows) - 1):
        if rows[index] == 0 and rows[index - 1] and rows[index + 1]:
            rows[index] = 1
    groups: list[tuple[int, int]] = []
    start = None
    for index, value in enumerate(rows):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(rows) - 1):
            end = index if value and index == len(rows) - 1 else index - 1
            if end - start + 1 >= 4:
                groups.append((start, end))
            start = None
    return groups


def measure(image: Image.Image, rect: tuple[int, int, int, int], mode: str) -> dict:
    x0, y0, _, _ = rect
    rgb = np.asarray(image.crop(rect).convert("RGB"), dtype=np.int16)
    lum = rgb.mean(axis=2)
    spread = rgb.max(axis=2) - rgb.min(axis=2)
    binary = lum > 210 if mode == "light" else ((lum < 180) | ((spread > 32) & (lum < 225)))
    bands = line_bands(binary)
    if not bands:
        return {"anchor": [x0, y0], "ink_height": 0, "ink_width": 0}
    top, bottom = bands[0]
    _, xs = np.where(binary[top : bottom + 1])
    left, right = int(xs.min()), int(xs.max() + 1)
    return {"anchor": [x0 + left, y0 + top], "ink_height": bottom - top + 1, "ink_width": right - left}


def yiq_delta(actual: np.ndarray, design: np.ndarray) -> np.ndarray:
    a = actual.astype(np.float32)
    d = design.astype(np.float32)
    dr, dg, db = (a[:, :, i] - d[:, :, i] for i in range(3))
    dy = 0.29889531 * dr + 0.58662247 * dg + 0.11448223 * db
    di = 0.59597799 * dr - 0.27417610 * dg - 0.32180189 * db
    dq = 0.21147017 * dr - 0.52261711 * dg + 0.31114694 * db
    return (0.5053 * dy * dy + 0.299 * di * di + 0.1957 * dq * dq) / (255.0 * 255.0)


def structural_fidelity(actual: Image.Image, design: Image.Image, mask: Image.Image) -> tuple[float, dict]:
    scores = {}
    for scale in (2, 4, 8, 16):
        size = (actual.width // scale, actual.height // scale)
        a = actual.convert("L").resize(size, Image.Resampling.BOX).filter(ImageFilter.FIND_EDGES)
        d = design.convert("L").resize(size, Image.Resampling.BOX).filter(ImageFilter.FIND_EDGES)
        include = ImageChops.invert(mask.resize(size, Image.Resampling.NEAREST))
        ea = ImageChops.multiply(a.point(lambda v: 255 if v >= 18 else 0), include)
        ed = ImageChops.multiply(d.point(lambda v: 255 if v >= 18 else 0), include)
        da, dd = ea.filter(ImageFilter.MaxFilter(3)), ed.filter(ImageFilter.MaxFilter(3))
        pa, pd, pda, pdd = map(np.asarray, (ea, ed, da, dd))
        ca, cd = np.count_nonzero(pa), np.count_nonzero(pd)
        ma = np.count_nonzero((pa > 0) & (pdd > 0))
        md = np.count_nonzero((pd > 0) & (pda > 0))
        precision = ma / ca if ca else 1.0
        recall = md / cd if cd else 1.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores[str(scale)] = round(f1 * 100, 2)
    return round(sum(scores.values()) / len(scores), 2), scores


def analyze(config: dict) -> dict:
    viewport = tuple(config.get("viewport", [750, 1624]))
    actual = load_image(Path(config["actual"]), viewport)
    design = load_image(Path(config["design"]), viewport)
    output_dir = Path(config["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = config["slug"]

    mask = Image.new("L", viewport, 0)
    draw = ImageDraw.Draw(mask)
    for rect in config.get("exclude_rects", []):
        draw.rectangle(tuple(rect), fill=255)
    mask_visual = Image.new("RGBA", viewport, (54, 211, 255, 0))
    mask_visual.putalpha(mask.point(lambda value: 68 if value else 0))
    mask_visual.save(output_dir / f"{slug}-mask.png")

    a = np.asarray(actual.convert("RGB"))
    d = np.asarray(design.convert("RGB"))
    eligible = np.asarray(mask) == 0
    changed = (yiq_delta(a, d) > float(config.get("threshold", 0.02)) ** 2) & eligible
    heat = np.zeros((viewport[1], viewport[0], 4), dtype=np.uint8)
    heat[changed] = [255, 38, 58, 176]
    Image.fromarray(heat).save(output_dir / f"{slug}-heatmap.png")
    eligible_count = int(np.count_nonzero(eligible))
    diff_count = int(np.count_nonzero(changed))
    pixel = round(100 * (1 - diff_count / eligible_count), 2) if eligible_count else 100.0
    structural, scales = structural_fidelity(actual, design, mask)

    fields = []
    for field in config.get("fields", []):
        actual_measure = measure(actual, tuple(field["actual_rect"]), field.get("mode", "dark"))
        design_measure = measure(design, tuple(field["design_rect"]), field.get("mode", "dark"))
        expected = float(field["expected"])
        estimates = []
        if design_measure["ink_height"]:
            estimates.append(expected * actual_measure["ink_height"] / design_measure["ink_height"])
        if field.get("same_text", True) and design_measure["ink_width"]:
            estimates.append(expected * actual_measure["ink_width"] / design_measure["ink_width"])
        estimate = round(max(estimates, key=lambda value: abs(value - expected)), 1) if estimates else None
        delta = round(estimate - expected, 1) if estimate is not None else None
        fields.append({
            "name": field["name"], "expected": field["expected"], "estimate": estimate, "delta": delta,
            "flag": delta is not None and abs(delta) >= float(config.get("font_delta_threshold", 1.5)),
            "actual_anchor": actual_measure["anchor"], "design_anchor": design_measure["anchor"],
            "crop": field.get("crop", [420, 96]), "actual_ink_height": actual_measure["ink_height"],
            "design_ink_height": design_measure["ink_height"], "actual_ink_width": actual_measure["ink_width"],
            "design_ink_width": design_measure["ink_width"], "issue": field.get("issue")
        })

    result = {
        "engine": "YIQ numpy threshold + multi-scale edge F1",
        "threshold": float(config.get("threshold", 0.02)),
        "pixel_fidelity": pixel,
        "structural_fidelity": structural,
        "structural_scales": scales,
        "combined": round(0.7 * pixel + 0.3 * structural, 2),
        "diff_pixels": diff_count,
        "eligible_pixels": eligible_count,
        "fields": fields
    }
    (output_dir / f"{slug}-metrics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.config.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
