"""Adds a title block and non-overlapping leader-line callouts to the raw V3 renders (Pillow)."""

import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "renders_V3")
TITLES = {
    "V3_1_Assembly_Isometric": ("SPD V3.0 — Submerged Pulsed Micro-Slit Diffuser, full assembly",
                                "Printed parts 01-10 + purchased references (duckbill, O-rings, 1.40 m loop, ballast)"),
    "V3_2_Section_AA_Downcomers": ("SECTION A-A  (Y = -92 mm, through the downcomers)",
                                   "Oscillator outputs -> downcomers -> closed plenum ducts -> pockets -> 1.0 mm slits"),
    "V3_3_Section_BB_Supply_Stack": ("SECTION B-B  (X = 0, supply stack)",
                                     "Inlet -> accumulator -> standpipe -> duckbill -> supply plenum -> nozzle"),
    "V3_4_Section_CC_Oscillator_Plan": ("SECTION C-C  (Z = 193 mm, oscillator cavity plan)",
                                        "Loop-type bistable Coanda oscillator, b = 6 mm, h = 16 mm, splitter at 6 b"),
}


def font(size, bold=False):
    for f in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        p = os.path.join("C:\\Windows\\Fonts", f)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def place(labels, side, top, bottom, h):
    """Distribute callouts on one side, keeping order of their anchors and a minimum pitch."""
    labels = sorted(labels, key=lambda l: l["y"])
    pitch = max(h + 10, min(64, (bottom - top) / max(1, len(labels))))
    ys, cur = [], top
    for lab in labels:
        cur = max(cur, min(lab["y"] - h / 2, bottom - h))
        ys.append(cur)
        cur += pitch
    over = (ys[-1] + h) - bottom if ys else 0
    if over > 0:
        ys = [max(top, y - over) for y in ys]
    return list(zip(labels, ys))


def main():
    with open(os.path.join(OUT, "labels.json"), encoding="utf-8") as f:
        all_labels = json.load(f)
    for name, labels in all_labels.items():
        raw = os.path.join(OUT, name + "_raw.png")
        img = Image.open(raw).convert("RGB")
        w, h = img.size
        head = 96
        canvas = Image.new("RGB", (w, h + head), (14, 22, 34))
        canvas.paste(img, (0, head))
        d = ImageDraw.Draw(canvas)
        t1, t2 = TITLES[name]
        d.text((28, 16), t1, font=font(30, True), fill=(235, 242, 250))
        d.text((28, 58), t2, font=font(20), fill=(150, 190, 230))
        d.text((w - 330, 22), "SPD V3.0  |  2026-09-28", font=font(20, True), fill=(255, 196, 90))
        d.text((w - 330, 54), "verified: verify_spd_v3.py", font=font(18), fill=(150, 190, 230))
        f = font(21, True)
        box_h = 34
        left = [l for l in labels if l["x"] < w / 2]
        right = [l for l in labels if l["x"] >= w / 2]
        for side, group in (("L", left), ("R", right)):
            for lab, y in place(group, side, head + 20, head + h - 20, box_h):
                ax, ay = lab["x"], lab["y"] + head
                tw = d.textlength(lab["text"], font=f)
                bx = 18 if side == "L" else w - tw - 42
                by = y
                if bx - 12 <= ax <= bx + tw + 36 and by - 12 <= ay <= by + box_h + 12:   # box would hide its anchor
                    by = by + box_h + 26 if by + 2 * box_h + 26 < head + h else by - box_h - 26
                d.rounded_rectangle([bx, by, bx + tw + 24, by + box_h], radius=8, fill=(14, 22, 34),
                                    outline=(255, 170, 60), width=2)
                d.text((bx + 12, by + 4), lab["text"], font=f, fill=(245, 245, 245))
                sx = bx + tw + 24 if side == "L" else bx
                d.line([(sx, by + box_h / 2), (ax, ay)], fill=(255, 170, 60), width=3)
                d.ellipse([ax - 6, ay - 6, ax + 6, ay + 6], fill=(255, 170, 60), outline=(20, 20, 20))
        canvas.save(os.path.join(OUT, name + ".png"), optimize=True)
        print("annotated", name)


if __name__ == "__main__":
    main()
