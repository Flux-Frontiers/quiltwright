#!/usr/bin/env python3
"""Draw the Quiltwright logo in Art Techno and write every size the repo uses.

The mark is the quilt: the grid of views Quiltwright writes, four columns by
three rows, with the subject shifting a little from each view to the next. The palette, drawing helpers and outlined lettering come from the
Art Techno brand build, so the SVGs render the same everywhere.

Usage::

    python scripts/build_logo.py

Needs ``fonttools`` and Pillow, Google Chrome for the PNG renders, and a clone
of https://github.com/Flux-Frontiers/art_techno beside this repo. Set ``CHROME``
to the browser binary if it is not at the default macOS path.

Writes:

- ``assets/quiltwright_logo.svg`` and ``assets/quiltwright_logo.png``: the square
  mark (1024 px PNG)
- ``assets/quiltwright_icon.svg``: the mark reduced for 64 px and below
- ``assets/quiltwright_banner.svg`` and ``assets/quiltwright_banner.png``
- ``docs/assets/logo.png`` and ``docs/assets/favicon.png``: the docs site's
  header logo and favicon, from the icon
"""

import importlib.util
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
AT_BUILD = ROOT.parent / "art_techno" / "docs" / "brand" / "build.py"

_spec = importlib.util.spec_from_file_location("at_build", AT_BUILD)
at = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(at)

f, line, pad, via, diamond, clipped_rect = (
    at.f,
    at.line,
    at.pad,
    at.via,
    at.diamond,
    at.clipped_rect,
)
OBSIDIAN, PANEL, COPPER, GOLD, GREEN, MINT, SILK = (
    at.OBSIDIAN,
    at.PANEL,
    at.COPPER,
    at.GOLD,
    at.GREEN,
    at.MINT,
    at.SILK,
)

NAME = "QUILTWRIGHT"
PART = "HANG IT IN THE AIR"


def rect(
    x: float, y: float, w: float, h: float, fill: str, stroke: str = "", width: float = 0
) -> str:
    s = f' stroke="{stroke}" stroke-width="{f(width)}"' if stroke else ""
    return f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" fill="{fill}"{s}/>'


def die(x: float, y: float, s: float, core: str) -> str:
    """A square green die in a gold line, centered on ``x, y``.

    :param x: Center x.
    :param y: Center y.
    :param s: Side length.
    :param core: Color of the square at its center.
    """
    return rect(x - s / 2, y - s / 2, s, s, GREEN, GOLD, s / 9) + rect(
        x - s / 6, y - s / 6, s / 3, s / 3, core
    )


def tile(x: float, y: float, w: float, h: float, c: float, width: float) -> str:
    """One view of the quilt: a dark tile with 45-degree corners in a gold line.

    :param x: Left edge.
    :param y: Top edge.
    :param w: Width.
    :param h: Height.
    :param c: Corner cut.
    :param width: Stroke width.
    """
    return (
        f'<path d="{clipped_rect(x, y, w, h, c)}" fill="{PANEL}" stroke="{GOLD}" '
        f'stroke-width="{f(width)}"/>'
    )


def quilt() -> str:
    """The quilt on a 512 field: four columns by three rows of views.

    A quilt counts its views from the bottom left, so the subject (a die)
    sits furthest left in the bottom-left tile and furthest right in the
    top-right one: the parallax the panel turns into depth. The two middle
    views carry a silk core. The copper run beneath marks the order, from a
    via at the first view to a pad at the last.
    """
    out = []
    cols, rows, w, h, gap = 4, 3, 72, 62, 10
    x0 = 256 - (cols * w + (cols - 1) * gap) / 2
    y0 = 212 - (rows * h + (rows - 1) * gap) / 2
    n = cols * rows
    for r in range(rows):
        for c in range(cols):
            view = (rows - 1 - r) * cols + c
            x, y = x0 + c * (w + gap), y0 + r * (h + gap)
            out.append(tile(x, y, w, h, 7, 2.6))
            shift = (view / (n - 1) - 0.5) * (w - 30)
            mid = view in (n // 2 - 1, n // 2)
            out.append(die(x + w / 2 + shift, y + h / 2, 17, SILK if mid else GOLD))
    yb = y0 + rows * (h + gap) + 4
    x1 = x0 + cols * (w + gap) - gap
    out.append(line([(x0, yb), (x1, yb)], COPPER, 3.5))
    out.append(via(x0, yb, 7, COPPER) + pad(x1, yb, 7, COPPER))
    return "".join(out)


def quilt_small() -> str:
    """The quilt reduced for 64 px and below: two by two views, the die shifting."""
    out = []
    for i, (x, y) in enumerate(((12, 34), (34, 34), (12, 12), (34, 12))):
        out.append(tile(x, y, 18, 18, 3, 1.8))
        out.append(die(x + 9 + (i - 1.5) * 2.4, y + 9, 7, GOLD))
    return "".join(out)


def border(w: float, h: float, inset: float, c: float, heavy: float) -> str:
    """Double frame with 45-degree corners and a green diamond at each corner.

    :param w: Canvas width.
    :param h: Canvas height.
    :param inset: Distance of the heavy line from the canvas edge.
    :param c: Corner cut of the heavy line.
    :param heavy: Stroke width of the heavy line.
    """
    out = [
        f'<path d="{clipped_rect(inset, inset, w - 2 * inset, h - 2 * inset, c)}" fill="none" stroke="{GOLD}" stroke-width="{f(heavy)}"/>',
        f'<path d="{clipped_rect(inset * 1.9, inset * 1.9, w - 3.8 * inset, h - 3.8 * inset, c * 0.75)}" fill="none" stroke="{GOLD}" stroke-width="{f(heavy * 0.4)}" stroke-opacity=".6"/>',
    ]
    d = inset * 1.45 + c * 0.4375
    for cx, cy in ((d, d), (w - d, d), (d, h - d), (w - d, h - d)):
        out.append(diamond(cx, cy, inset * 0.5, GREEN))
    return "".join(out)


def svg(w: int, h: int, title: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f"<title>{title}</title>"
        f'<rect width="{w}" height="{h}" fill="{OBSIDIAN}"/>{body}</svg>\n'
    )


def mark(display, mono) -> str:
    """512 square mark: the quilt, the name and the part line beneath."""
    body = border(512, 512, 10, 26, 5) + quilt()
    size = min(40, 40 * 400 / display.width(NAME, 40, 0.2))
    body += display.path(NAME, 256, 430, size, 0.2, "middle", GOLD)
    body += mono.path(PART, 256, 462, 13.5, 0.3, "middle", MINT)
    return svg(512, 512, "Quiltwright mark, Art Techno", body)


def icon() -> str:
    """64 icon: the reduced quilt in one heavy frame, no lettering."""
    body = f'<path d="{clipped_rect(2.5, 2.5, 59, 59, 7.5)}" fill="none" stroke="{GOLD}" stroke-width="3"/>'
    return svg(64, 64, "Quiltwright icon, Art Techno", body + quilt_small())


def banner(display, mono) -> str:
    """1280 x 320 banner: the quilt left, the name and part line right.

    The name is set as large as the room right of the quilt allows, and the
    pair is centered on the banner's height.
    """
    s = 0.78
    body = border(1280, 320, 10, 18, 3)
    body += (
        f'<g transform="translate({f(230 - 256 * s)} {f(160 - 210 * s)}) scale({s})">{quilt()}</g>'
    )
    cx, room, gap = 820, 760, 34
    size = min(120, 120 * room / display.width(NAME, 120, 0.2))
    part = min(26, 26 * room / mono.width(PART, 26, 0.3))
    cap = display.cap * size / display.upm
    pcap = mono.cap * part / mono.upm
    base = (320 - (cap + gap + pcap)) / 2 + cap
    body += display.path(NAME, cx, base, size, 0.2, "middle", GOLD)
    body += mono.path(PART, cx, base + gap + pcap, part, 0.3, "middle", MINT)
    return svg(1280, 320, "Quiltwright banner, Art Techno", body)


def render(src: Path, out: Path, w: int, h: int) -> None:
    """Render the SVG ``src`` to ``out`` at ``w`` x ``h`` px with headless Chrome.

    :param src: SVG file; its ``width`` attribute sets the CSS width.
    :param out: PNG to write.
    :param w: Output width in px.
    :param h: Output height in px.
    """
    svg_w = int(src.read_text().split('width="', 1)[1].split('"', 1)[0])
    subprocess.run(
        [
            at.CHROME,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--window-size={svg_w},{svg_w * h // w}",
            f"--force-device-scale-factor={w / svg_w}",
            f"--screenshot={out}",
            src.as_uri(),
        ],
        check=True,
        capture_output=True,
    )


def resized(master: Path, dest: Path, px: int) -> None:
    Image.open(master).convert("RGB").resize((px, px), Image.LANCZOS).save(dest, optimize=True)


def main() -> None:
    at.fetch_fonts()
    display = at.Face(at.CACHE / "JosefinSans.ttf", weight=600)
    mono = at.Face(at.CACHE / "IBMPlexMono-Medium.ttf")

    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    mark_svg = assets / "quiltwright_logo.svg"
    icon_svg = assets / "quiltwright_icon.svg"
    banner_svg = assets / "quiltwright_banner.svg"
    mark_svg.write_text(mark(display, mono))
    icon_svg.write_text(icon())
    banner_svg.write_text(banner(display, mono))

    mark_png = mark_svg.with_suffix(".png")
    render(mark_svg, mark_png, 1024, 1024)
    render(banner_svg, banner_svg.with_suffix(".png"), 2560, 640)
    docs = ROOT / "docs" / "assets"
    docs.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        icon_png = Path(tmp) / "icon.png"
        render(icon_svg, icon_png, 1024, 1024)
        resized(icon_png, docs / "logo.png", 256)
        resized(icon_png, docs / "favicon.png", 32)


if __name__ == "__main__":
    main()
