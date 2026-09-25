#!/usr/bin/env python3
"""Sanity checks for the static site in public/. Exits non-zero on failure."""
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
errors = []

# Every SVG must be well-formed XML, or browsers render nothing.
for svg in sorted(PUBLIC.glob("*.svg")):
    try:
        ET.parse(svg)
    except ET.ParseError as e:
        errors.append(f"{svg.name}: invalid XML: {e}")

# og-image.png must really be the size index.html declares for it.
html = (PUBLIC / "index.html").read_text(encoding="utf-8")
declared = {
    dim: re.search(rf'property="og:image:{dim}" content="(\d+)"', html)
    for dim in ("width", "height")
}
png = (PUBLIC / "og-image.png").read_bytes()
if png[:8] != b"\x89PNG\r\n\x1a\n":
    errors.append("og-image.png: not a PNG file")
elif not all(declared.values()):
    errors.append("index.html: og:image:width/height meta tags missing")
else:
    width, height = struct.unpack(">II", png[16:24])  # IHDR chunk
    want = (int(declared["width"][1]), int(declared["height"][1]))
    if (width, height) != want:
        errors.append(f"og-image.png is {width}x{height}, index.html declares {want[0]}x{want[1]}")

for e in errors:
    print(f"::error::{e}")
print(f"{len(errors)} problem(s) found" if errors else "All site checks passed.")
sys.exit(1 if errors else 0)
