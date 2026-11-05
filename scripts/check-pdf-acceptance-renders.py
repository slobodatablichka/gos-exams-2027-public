#!/usr/bin/env python3
"""Validate A4 proof images for all nine books, with readable nonblank content."""
import sys
from pathlib import Path
from PIL import Image, ImageChops

def check(folder):
    base = Path(folder)
    files = sorted(base.glob("*.png"))
    if len(files) != 18:
        raise ValueError("Need cover and body render for each of nine books")
    inspected = []
    for file in files:
        with Image.open(file) as picture:
            rgb = picture.convert("RGB")
            if picture.width < 700 or picture.height < 900:
                raise ValueError("PDF page resolution too low: " + str(file))
            bounds = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white")).getbbox()
            if not bounds or bounds[2] - bounds[0] < 180 or bounds[3] - bounds[1] < 95:
                raise ValueError("PDF page is blank/visually incomplete: " + str(file))
            top = bounds[1] / picture.height
            bottom = bounds[3] / picture.height
            left = bounds[0] / picture.width
            right = bounds[2] / picture.width
            if min(top, left, 1 - right, 1 - bottom) < 0.015:
                raise ValueError("Content possibly clipped: " + str(file))
            inspected.append(str(file))
            print("PASS RENDER", file.name, rgb.size, bounds)
    return inspected

if __name__ == "__main__":
    try:
        check(sys.argv[1])
    except (OSError, ValueError) as exc:
        print("ERROR", exc, file=sys.stderr)
        sys.exit(1)
