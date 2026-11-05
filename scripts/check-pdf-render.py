#!/usr/bin/env python3
"""Verify rendered PDF proof images are readable, nonblank A4 page layouts."""
import sys
from pathlib import Path
from PIL import Image, ImageChops

def main(folder):
    files = sorted(Path(folder).glob("*.png"))
    if len(files) != 3:
        raise ValueError("Expected 3 rendered PDF proof pages")
    for file in files:
        with Image.open(file) as picture:
            if picture.width < 500 or picture.height < 700:
                raise ValueError("PDF print proof too small: " + str(file))
            white = Image.new("RGB", picture.size, "white")
            bounds = ImageChops.difference(picture.convert("RGB"), white).getbbox()
            if not bounds or (bounds[2] - bounds[0]) < 140 or (bounds[3] - bounds[1]) < 110:
                raise ValueError("Blank or clipped print proof: " + str(file))
            print("RENDER PASS", file.name, picture.size, bounds)

if __name__ == "__main__":
    main(sys.argv[1])
