#!/usr/bin/env python3
"""Paint four text-free metabolism illustrations with Pillow.

The PNGs have a genuinely transparent background so they can be placed over the
cream FitStudy cards. Everything is drawn locally as raster shapes; no fonts,
SVGs, remote assets, or image-generation services are used.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets"
WIDTH, HEIGHT = 900, 600
SCALE = 3  # Draw large, then downsample for clean curves.

# Match the September 28 FitStudy cards.
PAPER = "#F4EFE5"
WHITE = "#FFFCF6"
RED = "#92362A"
RED_DARK = "#6D2C25"
RED_MID = "#B45E50"
PALE_RED = "#EAD5CF"
BLUE = "#4B91B3"
BLUE_DARK = "#30708E"
PALE_BLUE = "#DCECF2"
GREEN = "#5D8066"
GREEN_DARK = "#42644B"
PALE_GREEN = "#DCE8DC"


def rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    return (*ImageColor.getrgb(color), alpha)


def scaled(point: tuple[float, float]) -> tuple[int, int]:
    return (round(point[0] * SCALE), round(point[1] * SCALE))


def cubic(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    steps: int = 35,
) -> list[tuple[float, float]]:
    result = []
    for i in range(steps + 1):
        t = i / steps
        q = 1 - t
        result.append(
            (
                q**3 * p0[0] + 3 * q**2 * t * p1[0] + 3 * q * t**2 * p2[0] + t**3 * p3[0],
                q**3 * p0[1] + 3 * q**2 * t * p1[1] + 3 * q * t**2 * p2[1] + t**3 * p3[1],
            )
        )
    return result


def organic(anchors: list[tuple[float, float]], steps: int = 12) -> list[tuple[float, float]]:
    """Closed Catmull-Rom outline, useful for soft anatomical silhouettes."""
    points: list[tuple[float, float]] = []
    n = len(anchors)
    for i in range(n):
        p0, p1, p2, p3 = (
            anchors[(i - 1) % n],
            anchors[i],
            anchors[(i + 1) % n],
            anchors[(i + 2) % n],
        )
        for j in range(steps):
            t = j / steps
            t2, t3 = t * t, t * t * t
            points.append(
                (
                    0.5
                    * (
                        2 * p1[0]
                        + (-p0[0] + p2[0]) * t
                        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
                    ),
                    0.5
                    * (
                        2 * p1[1]
                        + (-p0[1] + p2[1]) * t
                        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
                    ),
                )
            )
    return points


class Art:
    def __init__(self) -> None:
        # Keep the RGB of transparent pixels cream to prevent dark resize fringes.
        self.image = Image.new("RGBA", (WIDTH * SCALE, HEIGHT * SCALE), rgba(PAPER, 0))
        self.draw = ImageDraw.Draw(self.image, "RGBA")

    def ellipse(
        self,
        box: tuple[float, float, float, float],
        fill: str | tuple[int, int, int, int],
        outline: str | None = None,
        width: float = 0,
    ) -> None:
        self.draw.ellipse(
            tuple(round(v * SCALE) for v in box),
            fill=fill,
            outline=outline,
            width=round(width * SCALE),
        )

    def line(
        self,
        points: list[tuple[float, float]],
        color: str | tuple[int, int, int, int],
        width: float,
        round_caps: bool = True,
    ) -> None:
        px = [scaled(p) for p in points]
        self.draw.line(px, fill=color, width=round(width * SCALE), joint="curve")
        if round_caps:
            r = width * SCALE / 2
            for x, y in (px[0], px[-1]):
                self.draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def shape(
        self,
        points: list[tuple[float, float]],
        fill: str | tuple[int, int, int, int],
        outline: str | None = None,
        width: float = 0,
        shadow: bool = False,
    ) -> None:
        px = [scaled(p) for p in points]
        if shadow:
            layer = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer, "RGBA")
            ld.polygon([(x + 7 * SCALE, y + 11 * SCALE) for x, y in px], fill=rgba(RED_DARK, 44))
            self.image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(9 * SCALE)))
        self.draw.polygon(px, fill=fill)
        if outline:
            self.draw.line(px + [px[0]], fill=outline, width=round(width * SCALE), joint="curve")

    def curve(
        self,
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        color: str | tuple[int, int, int, int],
        width: float,
        round_caps: bool = True,
    ) -> None:
        self.line(cubic(p0, p1, p2, p3), color, width, round_caps)

    def arrow(
        self,
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        color: str,
        width: float = 11,
        head: float = 28,
        halo: bool = True,
    ) -> None:
        pts = cubic(p0, p1, p2, p3)
        if halo:
            self.line(pts, rgba(WHITE, 225), width + 9)
        self.line(pts, color, width)
        dx, dy = pts[-1][0] - pts[-3][0], pts[-1][1] - pts[-3][1]
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        vx, vy = -uy, ux
        tip = pts[-1]
        base = (tip[0] - head * ux, tip[1] - head * uy)
        self.shape(
            [tip, (base[0] + head * 0.42 * vx, base[1] + head * 0.42 * vy),
             (base[0] - head * 0.42 * vx, base[1] - head * 0.42 * vy)],
            color,
        )

    def finish(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS).save(path, optimize=True)


def glow(art: Art, cx: float, cy: float, rx: float, ry: float, color: str, alpha: int = 45) -> None:
    art.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), rgba(color, alpha))


def glucose(art: Art, x: float, y: float, radius: float = 22) -> None:
    vertices = [
        (x + radius * math.cos(math.radians(60 * i - 30)),
         y + radius * math.sin(math.radians(60 * i - 30)))
        for i in range(6)
    ]
    art.shape(vertices, WHITE, BLUE_DARK, 5)
    art.ellipse((x - 4, y - 4, x + 4, y + 4), BLUE)


def glycogen(art: Art, x: float, y: float, scale: float = 1) -> None:
    # Branched, granulated polymer rather than one free glucose hexagon.
    nodes = [
        (-64, -12, 13), (-49, -48, 10), (-35, 14, 12), (-23, -19, 15),
        (-5, -57, 10), (1, 16, 14), (15, -25, 13), (33, -50, 10),
        (43, 4, 12), (62, -20, 10), (-45, 44, 9), (24, 45, 10),
    ]
    edges = [(0, 3), (1, 3), (2, 3), (3, 4), (3, 5), (5, 6),
             (6, 7), (6, 8), (8, 9), (2, 10), (5, 11)]
    for a, b in edges:
        ax, ay, _ = nodes[a]
        bx, by, _ = nodes[b]
        art.line([(x + ax * scale, y + ay * scale),
                  (x + bx * scale, y + by * scale)], RED_MID, 6 * scale)
    for dx, dy, r in nodes:
        cx, cy, rr = x + dx * scale, y + dy * scale, r * scale
        art.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), RED, RED_DARK, 2.4 * scale)
        art.ellipse((cx - rr * 0.44, cy - rr * 0.49,
                     cx - rr * 0.06, cy - rr * 0.11), rgba(WHITE, 175))


def muscle_fiber(art: Art, x: float, y: float, w: float, h: float) -> None:
    anchors = [
        (x, y + h * 0.49), (x + w * 0.07, y + h * 0.18),
        (x + w * 0.23, y + h * 0.04), (x + w * 0.55, y + h * 0.08),
        (x + w * 0.82, y + h * 0.07), (x + w * 0.99, y + h * 0.42),
        (x + w, y + h * 0.59), (x + w * 0.85, y + h * 0.9),
        (x + w * 0.54, y + h * 0.96), (x + w * 0.19, y + h * 0.88),
        (x + w * 0.04, y + h * 0.73),
    ]
    art.shape(organic(anchors), PALE_RED, RED, 8, shadow=True)
    # Uneven, curved myofibril bundles and fine striations make this a fiber.
    for offset, shade in ((0.25, RED_MID), (0.43, RED), (0.62, RED_MID), (0.78, RED_MID)):
        yy = y + h * offset
        art.curve((x + w * 0.13, yy), (x + w * 0.34, yy - h * 0.09),
                  (x + w * 0.7, yy + h * 0.08), (x + w * 0.87, yy),
                  rgba(shade, 115), 7)
    for i in range(11):
        xx = x + w * (0.22 + 0.056 * i)
        yy = y + h * (0.2 + 0.017 * math.sin(i * 0.8))
        art.line([(xx - 5, yy), (xx + 6, yy + h * 0.62)], rgba(RED, 47), 3)
    art.curve((x + w * 0.13, y + h * 0.13), (x + w * 0.38, y - h * 0.02),
              (x + w * 0.7, y + h * 0.01), (x + w * 0.84, y + h * 0.17),
              rgba(WHITE, 190), 11)


def mitochondrion(art: Art, cx: float, cy: float, scale: float = 1) -> None:
    a = [
        (cx - 55 * scale, cy - 10 * scale),
        (cx - 33 * scale, cy - 47 * scale),
        (cx + 29 * scale, cy - 39 * scale),
        (cx + 58 * scale, cy - 5 * scale),
        (cx + 34 * scale, cy + 40 * scale),
        (cx - 35 * scale, cy + 39 * scale),
    ]
    art.shape(organic(a), PALE_GREEN, GREEN_DARK, 6 * scale, shadow=True)
    for shift in (-22, 0, 22):
        art.curve((cx + shift * scale - 13 * scale, cy - 23 * scale),
                  (cx + shift * scale + 18 * scale, cy - 13 * scale),
                  (cx + shift * scale - 20 * scale, cy + 11 * scale),
                  (cx + shift * scale + 14 * scale, cy + 25 * scale),
                  GREEN, 4.7 * scale)


def liver(art: Art, cx: float, cy: float, scale: float = 1) -> None:
    pts = [(-190, -52), (-155, -112), (-48, -125), (52, -109),
           (150, -70), (183, -30), (175, 21), (119, 43),
           (78, 71), (8, 66), (-41, 103), (-113, 95), (-177, 43)]
    anchor = [(cx + dx * scale, cy + dy * scale) for dx, dy in pts]
    art.shape(organic(anchor), RED, RED_DARK, 8 * scale, shadow=True)
    art.curve((cx - 145 * scale, cy - 75 * scale),
              (cx - 87 * scale, cy - 125 * scale),
              (cx + 15 * scale, cy - 118 * scale),
              (cx + 87 * scale, cy - 78 * scale),
              rgba(WHITE, 155), 13 * scale)
    art.curve((cx + 55 * scale, cy - 85 * scale),
              (cx + 35 * scale, cy - 31 * scale),
              (cx + 62 * scale, cy + 17 * scale),
              (cx + 94 * scale, cy + 42 * scale),
              rgba(RED_DARK, 132), 7 * scale)
    art.curve((cx - 144 * scale, cy + 26 * scale),
              (cx - 76 * scale, cy + 74 * scale),
              (cx - 12 * scale, cy + 67 * scale),
              (cx + 20 * scale, cy + 54 * scale),
              rgba(WHITE, 72), 7 * scale)


def vessel(
    art: Art,
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    width: float = 83,
) -> None:
    path = cubic(p0, p1, p2, p3)
    art.line(path, BLUE_DARK, width + 11)
    art.line(path, PALE_BLUE, width)
    # A little blue specular band stops the vessel reading as a flat bar.
    art.curve((p0[0], p0[1] - width * 0.14),
              (p1[0], p1[1] - width * 0.14),
              (p2[0], p2[1] - width * 0.14),
              (p3[0], p3[1] - width * 0.14), rgba(WHITE, 170), 8)


def adipocytes(art: Art, cx: float, cy: float, scale: float = 1) -> None:
    cells = [(-78, -21, 61), (0, -61, 71), (78, 4, 65), (-12, 58, 70)]
    for dx, dy, r in cells:
        x, y, rr = cx + dx * scale, cy + dy * scale, r * scale
        art.ellipse((x - rr, y - rr, x + rr, y + rr), PALE_GREEN, GREEN_DARK, 6 * scale)
        art.ellipse((x - rr * 0.72, y - rr * 0.69,
                     x + rr * 0.7, y + rr * 0.73), CREAM_LIPID, GREEN, 2.5 * scale)
        art.ellipse((x + rr * 0.65, y - rr * 0.58,
                     x + rr * 0.82, y - rr * 0.41), GREEN_DARK)
    art.curve((cx - 115 * scale, cy - 68 * scale),
              (cx - 84 * scale, cy - 133 * scale),
              (cx - 20 * scale, cy - 141 * scale),
              (cx + 8 * scale, cy - 115 * scale), rgba(WHITE, 170), 6)


CREAM_LIPID = "#F3F0DB"


def molecule(art: Art, x: float, y: float, color: str, scale: float = 1) -> None:
    pts = [(x - 25 * scale, y + 14 * scale),
           (x + 2 * scale, y - 13 * scale),
           (x + 30 * scale, y + 11 * scale)]
    art.line(pts, color, 7 * scale)
    for j, (px, py) in enumerate(pts):
        r = (11 if j == 1 else 9) * scale
        art.ellipse((px - r, py - r, px + r, py + r), color, WHITE, 2 * scale)


def fatty_acid(art: Art, x: float, y: float, scale: float = 1) -> None:
    pts = [(x + i * 18 * scale, y + (11 if i % 2 else -9) * scale)
           for i in range(6)]
    art.line(pts, GREEN_DARK, 6 * scale, round_caps=False)
    art.ellipse((x - 17 * scale, y - 24 * scale,
                 x + 13 * scale, y + 6 * scale), GREEN, WHITE, 2 * scale)


def sparkle(art: Art, x: float, y: float, color: str, size: float = 16) -> None:
    art.line([(x - size, y), (x + size, y)], color, 4.5)
    art.line([(x, y - size), (x, y + size)], color, 4.5)
    art.ellipse((x - 4, y - 4, x + 4, y + 4), WHITE)


def paint_muscle_glycogen() -> None:
    art = Art()
    glow(art, 450, 304, 397, 248, PALE_RED, 86)
    muscle_fiber(art, 89, 158, 725, 281)
    glycogen(art, 293, 298, 1.16)
    art.arrow((389, 303), (455, 261), (517, 263), (570, 300), RED, 11, 27)
    mitochondrion(art, 667, 303, 1.03)
    sparkle(art, 781, 243, RED_MID, 16)
    sparkle(art, 777, 354, RED_MID, 11)
    art.finish(OUTPUT / "muscle-glycogen.png")


def paint_liver_glycogen() -> None:
    art = Art()
    glow(art, 340, 292, 286, 226, PALE_RED, 91)
    glow(art, 677, 324, 203, 143, PALE_BLUE, 80)
    vessel(art, (427, 331), (556, 315), (703, 339), (835, 315), 94)
    liver(art, 322, 294, 1.18)
    glycogen(art, 261, 282, 1.05)
    art.arrow((333, 294), (379, 288), (411, 307), (473, 321), WHITE, 10, 24, False)
    for x, y, r in ((516, 320, 21), (615, 329, 25), (710, 322, 22), (787, 317, 19)):
        glucose(art, x, y, r)
    art.arrow((565, 366), (646, 379), (742, 365), (811, 349), BLUE_DARK, 7, 24, False)
    art.finish(OUTPUT / "liver-glycogen.png")


def paint_gluconeogenesis() -> None:
    art = Art()
    glow(art, 505, 287, 245, 205, PALE_RED, 69)
    glow(art, 742, 313, 150, 127, PALE_BLUE, 71)
    vessel(art, (610, 319), (694, 324), (762, 311), (850, 314), 75)
    # Lactate route: small working fiber, red three-node molecule, liver.
    muscle_fiber(art, 41, 78, 252, 151)
    glycogen(art, 156, 150, 0.43)
    molecule(art, 298, 167, RED, 0.8)
    art.arrow((316, 189), (355, 190), (376, 227), (404, 248), RED, 8, 22)
    # Glycerol route: adipose cell releases a short three-carbon molecule.
    adipocytes(art, 155, 426, 0.56)
    molecule(art, 292, 427, GREEN, 0.84)
    art.arrow((315, 422), (365, 412), (370, 360), (408, 344), GREEN, 8, 22)
    liver(art, 505, 298, 0.72)
    art.arrow((596, 307), (630, 302), (641, 307), (668, 311), BLUE_DARK, 8, 21, False)
    glucose(art, 699, 316, 19)
    glucose(art, 772, 313, 21)
    art.finish(OUTPUT / "gluconeogenesis.png")


def paint_fat_oxidation() -> None:
    art = Art()
    glow(art, 208, 306, 200, 207, PALE_GREEN, 86)
    glow(art, 674, 303, 188, 204, PALE_RED, 63)
    vessel(art, (286, 324), (388, 301), (497, 327), (590, 318), 82)
    adipocytes(art, 199, 312, 1.0)
    fatty_acid(art, 352, 324, 0.66)
    fatty_acid(art, 455, 312, 0.68)
    muscle_fiber(art, 549, 160, 303, 282)
    art.arrow((530, 326), (569, 319), (589, 306), (619, 303), GREEN_DARK, 9, 23)
    mitochondrion(art, 735, 302, 0.79)
    sparkle(art, 837, 244, GREEN, 13)
    sparkle(art, 832, 382, GREEN, 10)
    art.finish(OUTPUT / "fat-oxidation.png")


def main() -> None:
    paint_muscle_glycogen()
    paint_liver_glycogen()
    paint_gluconeogenesis()
    paint_fat_oxidation()


if __name__ == "__main__":
    main()
