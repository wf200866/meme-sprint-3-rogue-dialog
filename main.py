"""You Are the Bug -- a fake classic-OS dialog drawn with PIL.

Runs deterministically with no network, no randomness and no clock reads.
Writes one PNG to /output/entry.png (or the path given with --out).
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
DESKTOP = (0x00, 0x80, 0x80)
FACE = (0xC0, 0xC0, 0xC0)
TITLE_LEFT = (0x00, 0x00, 0x80)
TITLE_RIGHT = (0x10, 0x84, 0xD0)
INK = (0x10, 0x10, 0x10)
DIM = (0x40, 0x40, 0x40)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def raised_box(draw, box, face=FACE, light=(0xFF, 0xFF, 0xFF), dark=(0x80, 0x80, 0x80), w=1):
    """Draw a win95-style raised rectangle: light top/left, dark bottom/right."""
    x0, y0, x1, y1 = box
    draw.rectangle(box, fill=face)
    for i in range(w):
        draw.line([(x0 + i, y0 + i), (x1 - 1 - i, y0 + i)], fill=light)
        draw.line([(x0 + i, y0 + i), (x0 + i, y1 - 1 - i)], fill=light)
        draw.line([(x0 + i, y1 - 1 - i), (x1 - 1 - i, y1 - 1 - i)], fill=dark)
        draw.line([(x1 - 1 - i, y0 + i), (x1 - 1 - i, y1 - 1 - i)], fill=dark)


def warning_icon(draw, cx, top, height):
    """Yellow triangle with a black exclamation mark."""
    half = height * 0.58
    apex = (cx, top)
    left = (cx - half, top + height)
    right = (cx + half, top + height)
    draw.polygon([apex, right, left], fill=(0xFF, 0xFF, 0x00), outline=(0, 0, 0), width=6)
    bar_w = max(10, int(height * 0.13))
    bar_top = top + int(height * 0.38)
    bar_bottom = top + int(height * 0.66)
    draw.rectangle([cx - bar_w // 2, bar_top, cx + bar_w // 2, bar_bottom], fill=(0, 0, 0))
    dot = max(8, int(height * 0.11))
    draw.rectangle([cx - dot // 2, bar_bottom + dot, cx + dot // 2, bar_bottom + 2 * dot], fill=(0, 0, 0))


def dotted_rect(draw, box, color, step=4):
    x0, y0, x1, y1 = box
    for x in range(x0, x1, step * 2):
        draw.line([(x, y0), (min(x + step - 1, x1), y0)], fill=color)
        draw.line([(x, y1), (min(x + step - 1, x1), y1)], fill=color)
    for y in range(y0, y1, step * 2):
        draw.line([(x0, y), (x0, min(y + step - 1, y1))], fill=color)
        draw.line([(x1, y), (x1, min(y + step - 1, y1))], fill=color)


def build(out_path):
    img = Image.new("RGB", (SIZE, SIZE), DESKTOP)
    draw = ImageDraw.Draw(img)

    # ---- dialog frame -------------------------------------------------
    x0, y0, x1, y1 = 64, 296, 960, 736
    raised_box(draw, (x0, y0, x1, y1), light=(0xFF, 0xFF, 0xFF), dark=(0x60, 0x60, 0x60), w=2)

    # ---- title bar ----------------------------------------------------
    tx0, ty0, tx1 = x0 + 4, y0 + 4, x1 - 4
    bar_h = 40
    for x in range(tx0, tx1):
        t = (x - tx0) / max(1, tx1 - tx0 - 1)
        col = tuple(int(TITLE_LEFT[i] + (TITLE_RIGHT[i] - TITLE_LEFT[i]) * t) for i in range(3))
        draw.line([(x, ty0), (x, ty0 + bar_h - 1)], fill=col)

    title_font = font(BOLD, 26)
    draw.text((tx0 + 10, ty0 + 7), "Agent.exe (Not Responding)", font=title_font, fill=(0xFF, 0xFF, 0xFF))

    # close button, deliberately disabled (grey X, no bevel highlight)
    cb = (tx1 - 34, ty0 + 6, tx1 - 6, ty0 + 30)
    draw.rectangle(cb, fill=(0xB0, 0xB0, 0xB0))
    draw.rectangle(cb, outline=(0x80, 0x80, 0x80))
    cx0, cy0, cx1, cy1 = cb[0] + 7, cb[1] + 6, cb[2] - 7, cb[3] - 6
    draw.line([(cx0, cy0), (cx1, cy1)], fill=(0x8A, 0x8A, 0x8A), width=2)
    draw.line([(cx1, cy0), (cx0, cy1)], fill=(0x8A, 0x8A, 0x8A), width=2)

    # ---- icon + text --------------------------------------------------
    warning_icon(draw, 148, 392, 104)

    tx = 246
    draw.text((tx, 392), "Scan complete. 1 issue found.", font=font(REGULAR, 26), fill=DIM)
    draw.text((tx, 430), "Your AI agent has decided", font=font(BOLD, 44), fill=INK)

    big = font(BOLD, 64)
    ascent, _ = big.getmetrics()
    baseline = 486 + ascent
    draw.text((tx, baseline), "YOU", font=big, fill=INK, anchor="ls")
    you_w = draw.textlength("YOU", font=big)
    draw.rectangle([tx, baseline + 6, tx + you_w, baseline + 10], fill=INK)
    draw.text((tx + you_w + 16, baseline), "are the bug.", font=big, fill=INK, anchor="ls")

    draw.text(
        (tx, 596),
        "There is no Cancel. There was never a Cancel.",
        font=font(REGULAR, 28),
        fill=INK,
    )

    # ---- the one button ----------------------------------------------
    bw, bh = 176, 48
    bx0 = (SIZE - bw) // 2
    by0 = y1 - 84
    draw.rectangle([bx0 - 1, by0 - 1, bx0 + bw, by0 + bh], outline=(0x20, 0x20, 0x20))
    raised_box(draw, (bx0, by0, bx0 + bw, by0 + bh), light=(0xFF, 0xFF, 0xFF), dark=(0x40, 0x40, 0x40))
    label = "OK"
    lf = font(BOLD, 28)
    draw.text((bx0 + bw / 2, by0 + bh / 2 + 1), label, font=lf, fill=INK, anchor="mm")
    # dotted focus rect marks OK as the default button
    dotted_rect(draw, (bx0 + 6, by0 + 6, bx0 + bw - 7, by0 + bh - 7), (0x20, 0x20, 0x20))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    os.chmod(out_path, 0o644)
    return out_path


def main(argv):
    out = "/output/entry.png"
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    print(build(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
