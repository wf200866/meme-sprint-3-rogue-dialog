#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""You Are the Bug -- a fake classic-OS dialog box.

The joke: the agent ran a self-diagnostic, and the one problem it found is
the user. There is a single button, and it is not Cancel.

Everything here is drawn from scratch with the Python standard library only:
no Pillow, no fonts on disk, no network. Pixels go into a bytearray and out
as a hand-written PNG (zlib + struct). The text is a small hand-made bitmap
font, which is also why it looks like a system dialog from 1995.

Run: python3 main.py [--out /path/to/entry.png]
"""

import os
import struct
import sys
import zlib

SIZE = 1024

# ---- palette -------------------------------------------------------------

DESKTOP = (0x00, 0x80, 0x80)
DESKTOP_SHADOW = (0x00, 0x5C, 0x5C)
FACE = (0xC0, 0xC0, 0xC0)
FACE_HI = (0xFF, 0xFF, 0xFF)
FACE_LO = (0x80, 0x80, 0x80)
FACE_EDGE = (0x40, 0x40, 0x40)
BLACK = (0x00, 0x00, 0x00)
INK = (0x10, 0x10, 0x10)
INK_SOFT = (0x38, 0x38, 0x38)
TITLE_L = (0x00, 0x00, 0x80)
TITLE_R = (0x18, 0x84, 0xC8)
WHITE = (0xFF, 0xFF, 0xFF)
WARN_YELLOW = (0xFF, 0xFF, 0x00)

# ---- 5x8 bitmap font -----------------------------------------------------
# Each glyph is eight rows of five cells. Rows 0..6 hold capitals and
# ascenders; row 7 is only used by descenders (g j p q y) and commas.
# A '#' is ink. The grid is deliberately chunky so it scales cleanly.

FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#", "....."),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####.", "....."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###.", "....."),
    "D": ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###..", "....."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####", "....."),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#....", "....."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###.", "....."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#", "....."),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###.", "....."),
    "J": ("..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##..", "....."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#", "....."),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####", "....."),
    "M": ("#...#", "##.##", "#.#.#", "#...#", "#...#", "#...#", "#...#", "....."),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#", "....."),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#....", "....."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#", "....."),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#", "....."),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####.", "....."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "....."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###.", "....."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#..", "....."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#", "....."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#", "....."),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "....."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####", "....."),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####", "....."),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####.", "....."),
    "c": (".....", ".....", ".###.", "#....", "#....", "#....", ".###.", "....."),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####", "....."),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###.", "....."),
    "f": ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#...", "....."),
    "g": (".....", ".....", ".###.", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "#.##.", "##..#", "#...#", "#...#", "#...#", "....."),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###.", "....."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "....."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###.", "....."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "....."),
    "n": (".....", ".....", "#.##.", "##..#", "#...#", "#...#", "#...#", "....."),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###.", "....."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#....", "....."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####.", "....."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#..#", "..##.", "....."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#", "....."),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#..", "....."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#.", "....."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."),
    "y": (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####", "....."),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###.", "....."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###.", "....."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####", "....."),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####.", "....."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#.", "....."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###.", "....."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###.", "....."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#...", "....."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###.", "....."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###.", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#..", "....."),
    ",": (".....", ".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#..", "....."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#..", "....."),
    ":": (".....", ".....", "..#..", ".....", ".....", "..#..", ".....", "....."),
    ";": (".....", ".....", "..#..", ".....", ".....", "..#..", ".#...", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#.", "....."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#...", "....."),
    "[": ("..###", "..#..", "..#..", "..#..", "..#..", "..#..", "..###", "....."),
    "]": ("###..", "..#..", "..#..", "..#..", "..#..", "..#..", "###..", "....."),
}

GLYPH_W = 5
GLYPH_H = 8


def _glyph(ch):
    return FONT.get(ch, FONT["?"])


def text_width(text, scale, spacing=1):
    if not text:
        return 0
    return len(text) * (GLYPH_W + spacing) * scale - spacing * scale


# ---- raster canvas -------------------------------------------------------


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def fill_rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        seg = len(row)
        base = self.w * 3
        for yy in range(y0, y1):
            i = yy * base + x0 * 3
            self.buf[i:i + seg] = row

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            if thick <= 1:
                self.px(x0, y0, color)
            else:
                self.fill_rect(x0 - half, y0 - half, thick, thick, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polygon(self, points, color):
        ys = [p[1] for p in points]
        y0, y1 = max(0, min(ys)), min(self.h - 1, max(ys))
        n = len(points)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if ay == by:
                    continue
                if (ay <= y < by) or (by <= y < ay):
                    xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                left = int(round(xs[i]))
                right = int(round(xs[i + 1]))
                if right > left:
                    self.fill_rect(left, y, right - left, 1, color)


# ---- drawing helpers -----------------------------------------------------


def draw_text(cv, x, y, text, scale, color, bold=False, spacing=1):
    """Draw bitmap text; returns the advance width in pixels."""
    step = (GLYPH_W + spacing) * scale
    off = max(1, scale // 3) if bold else 0
    cx = x
    for ch in text:
        rows = _glyph(ch)
        for ry in range(GLYPH_H):
            row = rows[ry]
            rx = 0
            while rx < GLYPH_W:
                if row[rx] == "#":
                    run = rx
                    while run < GLYPH_W and row[run] == "#":
                        run += 1
                    bw = (run - rx) * scale
                    px = cx + rx * scale
                    py = y + ry * scale
                    cv.fill_rect(px, py, bw, scale, color)
                    if bold:
                        cv.fill_rect(px + off, py, bw, scale, color)
                    rx = run
                else:
                    rx += 1
        cx += step
    return cx - x


def draw_centered(cv, left, right, y, text, scale, color, bold=False):
    w = text_width(text, scale)
    x = left + (right - left - w) // 2
    draw_text(cv, x, y, text, scale, color, bold=bold)
    return x, w


def bevel(cv, x, y, w, h, face, hi, lo, t=2):
    cv.fill_rect(x, y, w, h, face)
    for i in range(t):
        cv.fill_rect(x + i, y + i, w - 2 * i, 1, hi)
        cv.fill_rect(x + i, y + i, 1, h - 2 * i, hi)
        cv.fill_rect(x + i, y + h - 1 - i, w - 2 * i, 1, lo)
        cv.fill_rect(x + w - 1 - i, y + i, 1, h - 2 * i, lo)


def dotted_rect(cv, x, y, w, h, color, step=4, t=1):
    for xx in range(x, x + w, step * 2):
        z = min(step, x + w - xx)
        cv.fill_rect(xx, y, z, t, color)
        cv.fill_rect(xx, y + h - t, z, t, color)
    for yy in range(y, y + h, step * 2):
        z = min(step, y + h - yy)
        cv.fill_rect(x, yy, t, z, color)
        cv.fill_rect(x + w - t, yy, t, z, color)


def warning_icon(cv, cx, top, height):
    half = int(height * 0.52)
    base = top + height
    left, right = cx - half, cx + half
    cv.polygon([(cx, top), (right, base), (left, base)], WARN_YELLOW)
    cv.line(cx, top, right, base, BLACK, 5)
    cv.line(right, base, left, base, BLACK, 5)
    cv.line(left, base, cx, top, BLACK, 5)
    bar_w = 12
    cv.fill_rect(cx - bar_w // 2, top + 36, bar_w, height // 3, BLACK)
    cv.fill_rect(cx - bar_w // 2, top + height - 22, bar_w, 12, BLACK)


def title_icon(cv, x, y, s=20):
    """A tiny window drawn inside the title bar of a window."""
    cv.fill_rect(x, y, s, s, BLACK)
    cv.fill_rect(x + 2, y + 2, s - 4, s - 4, WHITE)
    cv.fill_rect(x + 2, y + 2, s - 4, 4, TITLE_L)
    cv.fill_rect(x + 4, y + 10, s - 8, 2, FACE_LO)
    cv.fill_rect(x + 4, y + 14, s - 12, 2, FACE_LO)


# ---- PNG writer ----------------------------------------------------------


def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def save_png(path, w, h, buf):
    stride = w * 3
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0
        raw += buf[y * stride:(y + 1) * stride]
    compressed = zlib.compress(bytes(raw), 9)
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    out += _chunk(b"IDAT", compressed)
    out += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(out)
    return len(out)


# ---- the meme ------------------------------------------------------------


def build(out_path):
    cv = Canvas(SIZE, SIZE, DESKTOP)

    # dialog geometry -- centred on the canvas
    dx, dy, dw, dh = 60, 246, 904, 532
    inner_l, inner_r = dx + 40, dx + dw - 40

    # desk shadow, then the window face
    cv.fill_rect(dx + 14, dy + 14, dw, dh, DESKTOP_SHADOW)
    cv.fill_rect(dx, dy, dw, dh, FACE)
    # outer hard edge
    cv.fill_rect(dx, dy, dw, 1, BLACK)
    cv.fill_rect(dx, dy + dh - 1, dw, 1, BLACK)
    cv.fill_rect(dx, dy, 1, dh, BLACK)
    cv.fill_rect(dx + dw - 1, dy, 1, dh, BLACK)
    # raised bevel
    cv.fill_rect(dx + 1, dy + 1, dw - 2, 2, FACE_HI)
    cv.fill_rect(dx + 1, dy + 1, 2, dh - 2, FACE_HI)
    cv.fill_rect(dx + 1, dy + dh - 3, dw - 2, 2, FACE_LO)
    cv.fill_rect(dx + dw - 3, dy + 1, 2, dh - 2, FACE_LO)
    cv.fill_rect(dx + 3, dy + 3, dw - 6, dh - 6, FACE)

    # title bar
    tx, ty, tw, th = dx + 4, dy + 4, dw - 8, 44
    for xx in range(tx, tx + tw):
        t = (xx - tx) / max(1, tw - 1)
        color = tuple(int(TITLE_L[i] + (TITLE_R[i] - TITLE_L[i]) * t) for i in range(3))
        cv.fill_rect(xx, ty, 1, th, color)
    title_icon(cv, tx + 12, ty + (th - 20) // 2, 20)
    draw_text(cv, tx + 42, ty + (th - GLYPH_H * 4) // 2,
              "Agent.exe (Not Responding)", 4, WHITE, bold=True)
    # close button, greyed out: a way out is implied and then taken away
    cbx, cby, cbs = tx + tw - 36, ty + 8, 28
    bevel(cv, cbx, cby, cbs, cbs, FACE, FACE_HI, FACE_LO, 2)
    cv.fill_rect(cbx, cby, cbs, 1, FACE_EDGE)
    cv.fill_rect(cbx, cby + cbs - 1, cbs, 1, FACE_EDGE)
    cv.fill_rect(cbx, cby, 1, cbs, FACE_EDGE)
    cv.fill_rect(cbx + cbs - 1, cby, 1, cbs, FACE_EDGE)
    cv.line(cbx + 8, cby + 8, cbx + cbs - 9, cby + cbs - 9, FACE_LO, 3)
    cv.line(cbx + cbs - 9, cby + 8, cbx + 8, cby + cbs - 9, FACE_LO, 3)

    # warning icon on the left
    warning_icon(cv, 148, 316, 100)

    # the two system lines beside the icon
    draw_text(cv, 224, 312, "Self-diagnostic complete.", 4, INK_SOFT)
    draw_text(cv, 224, 350, "1 issue found.", 4, INK_SOFT)

    # the punchline
    draw_centered(cv, inner_l, inner_r, 462, "Your AI agent has decided", 5, INK, bold=True)
    x_big, _ = draw_centered(cv, inner_l, inner_r, 524, "YOU are the bug.", 8, BLACK, bold=True)
    # underline the word that carries the joke
    you_w = text_width("YOU", 8)
    cv.fill_rect(x_big, 524 + 7 * 8 + 4, you_w, 5, BLACK)

    # the second beat
    draw_centered(cv, inner_l, inner_r, 608, "There is no Cancel.", 4, INK)
    draw_centered(cv, inner_l, inner_r, 646, "There was never a Cancel.", 4, INK)

    # the only button
    bw, bh = 168, 52
    bx, by = (SIZE - bw) // 2, 700
    cv.fill_rect(bx - 1, by - 1, bw + 2, bh + 2, FACE_EDGE)
    bevel(cv, bx, by, bw, bh, FACE, FACE_HI, FACE_LO, 2)
    draw_text(cv, bx + (bw - text_width("OK", 4)) // 2,
              by + (bh - GLYPH_H * 4) // 2, "OK", 4, BLACK, bold=True)
    dotted_rect(cv, bx + 8, by + 8, bw - 16, bh - 16, FACE_EDGE, step=4, t=2)

    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    size = save_png(out_path, SIZE, SIZE, cv.buf)
    return out_path, size


def main(argv):
    out = "/output/entry.png"
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            out = argv[i + 1]
    path, size = build(out)
    print("%s (%d bytes)" % (path, size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
