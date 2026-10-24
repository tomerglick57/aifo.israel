#!/usr/bin/env python3
"""Draws public/israel_on_the_map.txt, the map curl gets, from the SVG's country outlines."""
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
SVG = "{http://www.w3.org/2000/svg}"
COLS = 76  # plus a 2-space margin, so the map fits an 80-column terminal
SUB = 4  # land samples per half-cell, per side
TOKEN = re.compile(r"[a-df-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", re.I)

root = ET.parse(PUBLIC / "israel_on_the_map.svg").getroot()
groups = {g.get("id"): g for g in root.iter(SVG + "g")}
if "MILLER" not in groups["layer1"].find(SVG + "text").text:
    raise SystemExit("israel_on_the_map.svg is no longer a Miller projection; update project()")
width, height = float(root.get("width")), float(root.get("height"))


def project(lat, lon):
    """Miller projection of the whole globe onto the SVG's canvas."""
    y = 1.25 * math.log(math.tan(math.pi / 4 + 0.4 * math.radians(lat)))
    return (lon + 180) / 360 * width, height / 2 - y * width / (2 * math.pi)


# Country outlines are relative m/l/h/v paths; each m starts a new ring.
countries = groups["Countries"]
shift = float(re.fullmatch(r"translate\(0,(-?[\d.]+)\)", countries.get("transform"))[1])
shapes = []
for path in countries.iter(SVG + "path"):
    if "fill-opacity:0" in path.get("style", ""):
        continue  # invisible on the site, so not drawn here either
    rings, nums, x, y = [], [], 0.0, 0.0
    for tok in TOKEN.findall(path.get("d")):
        if tok.isalpha():
            if tok not in "mlhv":
                raise SystemExit(f"{path.get('id')}: unsupported path command {tok!r}")
            cmd = tok
            if cmd == "m":
                rings.append([])
            continue
        nums.append(float(tok))
        if cmd in "ml":
            if len(nums) < 2:
                continue
            x, y = x + nums[0], y + nums[1]
        elif cmd == "h":
            x += nums[0]
        else:
            y += nums[0]
        nums.clear()
        rings[-1].append((x, y + shift))
    shapes.append(rings)

# A character cell is about twice as tall as it is wide. Israel's point comes from
# the API, so the two can't disagree, and the rows are shifted to put it mid-row.
cell = width / COLS
where = json.loads((PUBLIC / "api/v1/where.json").read_text(encoding="utf-8"))
israel_x, israel_y = project(where["latitude"], where["longitude"])
israel_col = int(israel_x // cell)
israel_row = math.floor((israel_y - project(84, 0)[1]) / (2 * cell))  # 84°N clears Greenland
top = israel_y - (israel_row + 0.5) * 2 * cell
rows = math.ceil((project(-57, 0)[1] - top) / (2 * cell))  # 57°S clears Cape Horn, skips Antarctica

step = cell / SUB
land = [[False] * (COLS * SUB) for _ in range(rows * 2 * SUB)]
for rings in shapes:  # even-odd scanline fill, one path at a time
    edges = [
        (x1, y1, x2, y2)
        for ring in rings
        for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1])
        if y1 != y2
    ]
    for j, line in enumerate(land):
        sy = top + (j + 0.5) * step
        xs = sorted(x1 + (sy - y1) * (x2 - x1) / (y2 - y1) for x1, y1, x2, y2 in edges if (y1 <= sy) != (y2 <= sy))
        for a, b in zip(xs[::2], xs[1::2]):
            for i in range(max(0, math.ceil(a / step - 0.5)), min(len(line), math.floor(b / step - 0.5) + 1)):
                line[i] = True


def filled(r, c):
    """Whether at least a third of half-cell row r, column c is land."""
    samples = [land[j][i] for j in range(r * SUB, (r + 1) * SUB) for i in range(c * SUB, (c + 1) * SUB)]
    return sum(samples) * 3 >= len(samples)


# Each character draws two half-cells: ' is land on top, . is land below, : is both.
grid = [[" '.:"[filled(2 * r, c) + 2 * filled(2 * r + 1, c)] for c in range(COLS)] for r in range(rows)]


def draw(r, c, lines, clear=()):
    """Draws lines of art with their top-left at row r, column c, after blanking `clear` boxes."""
    for r0, r1, c0, c1 in clear:
        for rr in range(r0, r1 + 1):
            grid[rr][c0:c1 + 1] = [" "] * (c1 + 1 - c0)
    for dr, text in enumerate(lines):
        for dc, ch in enumerate(text):
            if ch != " ":
                grid[r + dr][c + dc] = ch


# Like the SVG's marker: a loop around Israel, then a tail up to a hand-lettered פה
# (ה on the left, פ on the right, so it reads right to left). The land around them
# is blanked so they stand out.
LABEL = [
    "____   ____",
    "    |   ' |",
    "|   |     |",
    "|   |  ___|",
]
r, c = israel_row, israel_col
label_row, label_col = r - 2 - len(LABEL), c + 3
draw(r - 1, c - 2, [" .-. ", "( * )", " '-' "], clear=[(r - 1, r + 1, c - 3, c + 3)])
draw(r - 2, c + 2, ["/"], clear=[(label_row, r - 2, c + 1, label_col + len(LABEL[0]))])
draw(label_row, label_col, LABEL)

text = "\n".join(("  " + "".join(line)).rstrip() for line in grid)
(PUBLIC / "israel_on_the_map.txt").write_text(f"\n{text}\n\n", encoding="ascii")
