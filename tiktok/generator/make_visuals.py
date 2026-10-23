#!/usr/bin/env python3
"""Generate 1080x1920 Quran nature verse visuals (TikTok photo format)."""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, S = 1080, 1920, 2
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_AR = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
RAQM = ImageFont.Layout.RAQM


# ---------------------------------------------------------------- helpers
def grad(stops):
    ys = np.arange(H * S) / S
    arr = np.zeros((H * S, 3))
    for c in range(3):
        arr[:, c] = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
    img = np.repeat(arr[:, None, :], W * S, axis=1).astype("uint8")
    return Image.fromarray(img).convert("RGBA")


def layer():
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def sc(pts):
    return [(x * S, y * S) for x, y in pts]


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def ellipse(d, cx, cy, rx, ry, fill):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=fill)


def blur(im, r):
    return im.filter(ImageFilter.GaussianBlur(r * S))


def glow_disc(base, cx, cy, r, color, rings=((2.6, 14), (1.9, 26), (1.4, 48))):
    lay, d = layer()
    for mult, a in rings:
        ellipse(d, cx, cy, r * mult, r * mult, rgba(color, a))
    base.alpha_composite(lay)


def stars(base, n, ymax, seed, color=(255, 255, 255), amin=90, amax=230, rmax=2.2, avoid=None):
    rnd = random.Random(seed)
    lay, d = layer()
    for _ in range(n):
        x, y = rnd.uniform(40, W - 40), rnd.uniform(40, ymax)
        if avoid and avoid(x, y):
            continue
        r = rnd.uniform(0.8, rmax)
        ellipse(d, x, y, r, r, rgba(color, rnd.randint(amin, amax)))
    base.alpha_composite(lay)


def wavy_band(base, y0, amp, freq, phase, color, bottom=H):
    lay, d = layer()
    pts = [(x, y0 + amp * math.sin(x / W * freq * math.pi * 2 + phase)
            + amp * 0.4 * math.sin(x / W * freq * 2.3 * math.pi * 2 + phase * 1.7)) for x in range(-10, W + 12, 6)]
    pts += [(W + 10, bottom), (-10, bottom)]
    d.polygon(sc(pts), fill=color)
    base.alpha_composite(lay)


def crescent_mask(cx, cy, r, off, r2=None):
    m = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(m)
    d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=255)
    r2 = r2 or r
    d2 = ImageDraw.Draw(m)
    d2.ellipse([(cx - r2 + off[0]) * S, (cy - r2 + off[1]) * S, (cx + r2 + off[0]) * S, (cy + r2 + off[1]) * S], fill=0)
    return m


def phase_disc(base, cx, cy, r, p, lit, unlit):
    """Draw a moon disc with waxing phase p in [0,1] (0 new .. 1 full)."""
    n = int(2 * r * S) + 4
    ys, xs = np.mgrid[0:n, 0:n]
    x = (xs - n / 2) / (r * S)
    y = (ys - n / 2) / (r * S)
    inside = x * x + y * y <= 1.0
    half = np.sqrt(np.clip(1 - y * y, 0, 1))
    term = (1 - 2 * p) * half
    litmask = inside & (x >= term) & (x <= half)
    img = np.zeros((n, n, 4), dtype="uint8")
    img[inside] = unlit
    img[litmask] = lit
    tile = Image.fromarray(img, "RGBA")
    base.alpha_composite(tile, (int(cx * S - n / 2), int(cy * S - n / 2)))


def frame(base, accent, a_outer=150, a_inner=90):
    lay, d = layer()
    d.rectangle([26 * S, 26 * S, (W - 26) * S, (H - 26) * S], outline=rgba(accent, a_outer), width=3 * S)
    d.rectangle([34 * S, 34 * S, (W - 34) * S, (H - 34) * S], outline=rgba(accent, a_inner), width=1 * S)
    for (x, y) in [(143, 143), (937, 143), (143, 1777), (937, 1777)]:
        d.polygon(sc([(x, y - 8), (x + 8, y), (x, y + 8), (x - 8, y)]), fill=rgba(accent, 170))
    # corner arcs
    for i, r in enumerate((26, 50, 74, 96)):
        a = 120 - i * 18
        for (cx, cy, s, e) in [(40, 1882, 270, 360), (1040, 1882, 180, 270), (40, 40, 0, 90), (1040, 40, 90, 180)]:
            d.arc([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], s, e, fill=rgba(accent, a), width=2 * S)
    base.alpha_composite(lay)


def star4(d, cx, cy, r, fill):
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.38
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(sc(pts), fill=fill)


# ---------------------------------------------------------------- text card
def wrap(draw, text, font, maxw, rtl):
    words = text.split(" ")
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        kw = dict(direction="rtl", language="ar") if rtl else {}
        if draw.textlength(trial, font=font, **kw) <= maxw * S or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def balanced(draw, text, font, maxw, rtl):
    """Wrap, then shrink the width as far as possible without adding a line (avoids orphan words)."""
    lines = wrap(draw, text, font, maxw, rtl)
    n = len(lines)
    if n == 1:
        return lines
    lo, hi = 200, maxw
    while hi - lo > 4:
        mid = (lo + hi) / 2
        if len(wrap(draw, text, font, mid, rtl)) <= n:
            hi = mid
        else:
            lo = mid
    return wrap(draw, text, font, hi, rtl)


def french_typo(t):
    # French typography: no-break space before ? ! : ;
    out = t
    for ch in ["?", "!", ":", ";"]:
        out = out.replace(" " + ch, " " + ch if ch in "?!;:" else ch)
        out = out.replace(ch, ch)  # no-op, keeps order explicit
    out = out.replace("?", " ?").replace(";", " ;").replace("  ", " ")
    return out


def render_card(base, arabic, french, ref, pal):
    fa = ImageFont.truetype(FONT_AR, 46 * S, layout_engine=RAQM)
    ff = ImageFont.truetype(FONT_FR, 30 * S, layout_engine=RAQM)
    fr_ = ImageFont.truetype(FONT_FR, 22 * S, layout_engine=RAQM)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    a_lines = balanced(tmp, arabic, fa, 905, True)
    f_lines = balanced(tmp, french_typo(french), ff, 880, False)
    a_lh, f_lh = 64, 38
    top = 900
    y_ar = top + 26
    y_div = y_ar + len(a_lines) * a_lh + 18
    y_fr = y_div + 24
    y_ref = y_fr + len(f_lines) * f_lh + 40
    bottom = y_ref + 46
    left, right = 50, W - 50

    lay, d = layer()
    d.rectangle([left * S, top * S, right * S, bottom * S], fill=rgba(pal["card"], 255),
                outline=rgba(pal["accent"], 235), width=3 * S)
    d.rectangle([(left + 8) * S, (top + 8) * S, (right - 8) * S, (bottom - 8) * S],
                outline=rgba(pal["accent"], 120), width=1 * S)
    # corner ticks
    t = 20
    for (x, y, dx, dy) in [(left + 20, top + 24, 1, 1), (right - 20, top + 24, -1, 1),
                           (left + 20, bottom - 24, 1, -1), (right - 20, bottom - 24, -1, -1)]:
        d.line(sc([(x, y + dy * t), (x, y), (x + dx * t, y)]), fill=rgba(pal["accent"], 190), width=2 * S)
    star4(d, W / 2, top - 6, 13, rgba((255, 255, 255), 255))
    # arabic
    cx = W * S / 2
    for i, ln in enumerate(a_lines):
        wl = d.textlength(ln, font=fa, direction="rtl", language="ar")
        d.text((cx - wl / 2, (y_ar + i * a_lh) * S), ln, font=fa, fill=(255, 255, 255, 255),
               direction="rtl", language="ar")
    d.line(sc([(113, y_div), (W - 113, y_div)]), fill=rgba(pal["divider"], 255), width=2 * S)
    for i, ln in enumerate(f_lines):
        wl = d.textlength(ln, font=ff)
        d.text((cx - wl / 2, (y_fr + i * f_lh) * S), ln, font=ff, fill=rgba(pal["fr"], 255))
    wl = d.textlength(ref, font=fr_)
    d.text((cx - wl / 2, y_ref * S), ref, font=fr_, fill=rgba(pal["ref"], 255))
    base.alpha_composite(lay)
    return dict(top=top, bottom=bottom, a_lines=a_lines, f_lines=f_lines, y_ar=y_ar, y_div=y_div, y_fr=y_fr, y_ref=y_ref,
                left=left, right=right)


# ---------------------------------------------------------------- scenes
def scene_orbits():
    pal = dict(accent=(150, 215, 215), card=(20, 22, 38), divider=(160, 220, 220), fr=(240, 232, 222), ref=(205, 198, 190))
    base = grad([(0, (22, 36, 82)), (380, (74, 80, 140)), (640, (214, 140, 120)), (840, (246, 176, 120)), (1920, (246, 176, 120))])
    stars(base, 90, 520, 11)
    # orbit rings
    lay, d = layer()
    for rx, ry, a in [(400, 310, 150), (330, 250, 90)]:
        N = 140
        for i in range(N):
            if i % 2:
                continue
            a0, a1 = 2 * math.pi * i / N, 2 * math.pi * (i + 1) / N
            p0 = (540 + rx * math.cos(a0), 440 + ry * math.sin(a0))
            p1 = (540 + rx * math.cos(a1), 440 + ry * math.sin(a1))
            d.line(sc([p0, p1]), fill=rgba((255, 238, 210), a), width=3 * S)
    base.alpha_composite(lay)
    # sun (top-left of orbit) and moon (bottom-right)
    sx, sy = 540 + 400 * math.cos(math.radians(205)), 440 + 310 * math.sin(math.radians(205))
    glow_disc(base, sx, sy, 56, (255, 214, 140))
    lay, d = layer()
    ellipse(d, sx, sy, 56, 56, (255, 243, 205, 255))
    base.alpha_composite(lay)
    mx, my = 540 + 400 * math.cos(math.radians(25)), 440 + 310 * math.sin(math.radians(25))
    glow_disc(base, mx, my, 50, (200, 214, 255), rings=((2.4, 10), (1.7, 20), (1.3, 36)))
    m = crescent_mask(mx, my, 50, (22, -12), 44)
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    lay.paste(Image.new("RGBA", (W * S, H * S), (240, 244, 255, 255)), (0, 0), m)
    base.alpha_composite(lay)
    # horizon hills
    wavy_band(base, 790, 14, 1.2, 0.5, (96, 72, 100, 255))
    wavy_band(base, 830, 10, 1.6, 2.1, (70, 54, 86, 255))
    return base, pal


def scene_phases():
    pal = dict(accent=(190, 200, 235), card=(14, 16, 34), divider=(190, 200, 235), fr=(238, 232, 224), ref=(200, 196, 192))
    base = grad([(0, (10, 14, 40)), (500, (28, 36, 84)), (860, (62, 66, 120)), (1920, (62, 66, 120))])
    stars(base, 140, 700, 7, avoid=lambda x, y: False)
    # row of phases along an arc
    phases = [0.06, 0.16, 0.30, 0.50, 0.70, 0.86, 1.0]
    for i, p in enumerate(phases):
        t = i / (len(phases) - 1)
        cx = 150 + t * 780
        cy = 690 - 230 * math.sin(math.pi * t)
        if p >= 1.0:
            glow_disc(base, cx, cy, 46, (230, 236, 255), rings=((2.4, 12), (1.7, 24), (1.3, 40)))
        phase_disc(base, cx, cy, 46, p, (244, 244, 232, 255), (44, 52, 100, 255))
    # old palm frond silhouette curve (the aged date-stalk) as thin curved crescent
    m = crescent_mask(540, 230, 72, (28, -12), 64)
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    lay.paste(Image.new("RGBA", (W * S, H * S), (250, 240, 210, 255)), (0, 0), m)
    base.alpha_composite(lay)
    # dunes
    wavy_band(base, 760, 18, 1.0, 0.8, (52, 54, 104, 255))
    wavy_band(base, 815, 12, 1.5, 2.6, (40, 42, 86, 255))
    return base, pal


def lightning(base, pts, width=12):
    glow, gd = layer()
    gd.line(sc(pts), fill=(255, 240, 160, 230), width=int(width * 2.8 * S), joint="curve")
    glow = blur(glow, 16)
    base.alpha_composite(glow)
    lay, d = layer()
    d.line(sc(pts), fill=(255, 252, 230, 255), width=int(width * S), joint="curve")
    base.alpha_composite(lay)


def scene_lightning():
    pal = dict(accent=(170, 200, 230), card=(18, 20, 32), divider=(170, 200, 230), fr=(238, 234, 228), ref=(198, 196, 196))
    base = grad([(0, (26, 30, 52)), (400, (50, 58, 92)), (800, (96, 108, 142)), (1920, (96, 108, 142))])
    # heavy clouds
    rnd = random.Random(5)
    lay, d = layer()
    for (cx, cy, rx, ry, col) in [
        (200, 250, 260, 90, (66, 74, 108)), (520, 200, 300, 110, (58, 66, 100)), (860, 260, 250, 90, (70, 78, 112)),
        (360, 350, 300, 100, (78, 88, 122)), (740, 380, 290, 100, (82, 92, 128)), (540, 330, 340, 110, (90, 100, 136)),
        (150, 430, 220, 70, (92, 102, 138)), (930, 450, 230, 70, (94, 104, 140)),
    ]:
        ellipse(d, cx, cy, rx, ry, rgba(col, 255))
    base.alpha_composite(lay)
    # lightning bolt
    lightning(base, [(560, 430), (500, 520), (548, 540), (456, 650), (506, 668), (404, 800)], 11)
    lightning(base, [(700, 440), (668, 500), (694, 510), (650, 580)], 6)
    # rain
    lay, d = layer()
    for _ in range(170):
        x, y = rnd.uniform(40, W - 40), rnd.uniform(470, 800)
        d.line(sc([(x, y), (x - 10, y + 34)]), fill=(205, 222, 245, rnd.randint(60, 150)), width=2 * S)
    base.alpha_composite(lay)
    # hills
    wavy_band(base, 780, 14, 1.2, 0.2, (46, 56, 80, 255))
    wavy_band(base, 830, 10, 1.7, 1.9, (34, 42, 64, 255))
    return base, pal


def scene_earth():
    pal = dict(accent=(235, 205, 170), card=(32, 22, 26), divider=(235, 205, 170), fr=(244, 236, 226), ref=(212, 200, 190))
    base = grad([(0, (96, 80, 130)), (300, (214, 150, 150)), (520, (250, 198, 140)), (580, (250, 198, 140)), (1920, (250, 198, 140))])
    # sun
    glow_disc(base, 810, 300, 62, (255, 224, 160))
    lay, d = layer()
    ellipse(d, 810, 300, 62, 62, (255, 246, 214, 255))
    base.alpha_composite(lay)
    # mountains (pegs) above ground
    lay, d = layer()
    d.polygon(sc([(110, 580), (300, 250), (490, 580)]), fill=(122, 92, 112, 255))
    d.polygon(sc([(400, 580), (590, 200), (780, 580)]), fill=(96, 72, 98, 255))
    d.polygon(sc([(700, 580), (850, 330), (1000, 580)]), fill=(134, 104, 120, 255))
    base.alpha_composite(lay)
    # ground slab (earth as a spread bed), with cutaway roots anchoring mountains
    earth = grad([(0, (188, 138, 96)), (840, (176, 128, 92)), (1920, (96, 68, 60))])
    lay, d = layer()
    d.rectangle([0, 580 * S, W * S, H * S], fill=(255, 255, 255, 255))
    lay_mask = lay.getchannel("A")
    base.paste(earth, (0, 0), lay_mask)
    lay, d = layer()
    d.rectangle([0, 580 * S, W * S, 604 * S], fill=(120, 150, 96, 255))
    d.polygon(sc([(180, 604), (300, 800), (420, 604)]), fill=(138, 98, 72, 255))
    d.polygon(sc([(470, 604), (590, 836), (710, 604)]), fill=(112, 78, 60, 255))
    d.polygon(sc([(770, 604), (850, 770), (930, 604)]), fill=(146, 106, 78, 255))
    base.alpha_composite(lay)
    return base, pal


def scene_seas():
    pal = dict(accent=(206, 236, 236), card=(16, 24, 34), divider=(170, 225, 225), fr=(240, 236, 230), ref=(200, 200, 200))
    base = grad([(0, (232, 132, 108)), (260, (248, 178, 126)), (520, (255, 222, 166)), (840, (236, 200, 150)), (1920, (150, 116, 92))])
    glow_disc(base, 540, 500, 90, (255, 236, 190))
    lay, d = layer()
    ellipse(d, 540, 520, 90, 90, (255, 244, 206, 255))
    base.alpha_composite(lay)
    # two seas
    lay, d = layer()
    d.rectangle([0, 520 * S, 540 * S, 850 * S], fill=(66, 170, 176, 255))
    d.rectangle([540 * S, 520 * S, W * S, 850 * S], fill=(26, 66, 128, 255))
    # clean the sun's lower half sinking into the sea
    base.alpha_composite(lay)
    lay, d = layer()
    rnd = random.Random(9)
    for k in range(34):
        t = k / 33
        y = 530 + 320 * t ** 1.5
        for side in (-1, 1):
            x0 = 540 + side * (30 + 440 * t) * rnd.uniform(0.15, 1.0)
            ln = 40 + 160 * t
            x1 = min(max(x0 + ln * side * 0.5, 6), W - 6)
            d.line(sc([(x0, y), (x1, y)]), fill=(255, 255, 255, int(30 + 60 * t)), width=2 * S)
    base.alpha_composite(lay)
    # shoreline: sand rises over the lower edge of the sea
    wavy_band(base, 846, 9, 1.4, 0.7, (236, 200, 150, 255))
    sand = grad([(0, (236, 200, 150)), (840, (236, 200, 150)), (1920, (150, 116, 92))])
    lay, d = layer()
    d.rectangle([0, 856 * S, W * S, H * S], fill=(255, 255, 255, 255))
    base.paste(sand, (0, 0), lay.getchannel("A"))
    # barrier between the seas (luminous strip, perspective)
    glow, gd = layer()
    gd.polygon(sc([(536, 520), (544, 520), (588, 842), (492, 842)]), fill=(255, 250, 220, 190))
    glow = blur(glow, 8)
    base.alpha_composite(glow)
    lay, d = layer()
    d.polygon(sc([(538, 520), (542, 520), (564, 842), (516, 842)]), fill=(255, 252, 235, 235))
    base.alpha_composite(lay)
    return base, pal


SCENES = {
    "55_orbits": scene_orbits, "56_moon_phases": scene_phases, "57_lightning": scene_lightning,
    "58_earth_mountains": scene_earth, "59_two_seas": scene_seas,
}


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    verses = json.load(open(os.path.join(HERE, "verses.json"), encoding="utf-8"))
    report = {}
    for v in verses:
        base, pal = SCENES[v["id"]]()
        arabic = v["arabic_simple"].replace("ۖ", "").replace("  ", " ").strip()
        info = render_card(base, arabic, v["french"], v["ref_label"], pal)
        frame(base, pal["accent"])
        out = base.convert("RGB").resize((W, H), Image.LANCZOS)
        path = os.path.join(outdir, f"Nature_{v['id']}.png")
        out.save(path, optimize=True)
        report[v["id"]] = dict(path=path, **{k: info[k] for k in ("top", "bottom")}, arabic_lines=info["a_lines"],
                               french_lines=info["f_lines"])
        print("wrote", path, "card", info["top"], "-", info["bottom"], "| ar lines", len(info["a_lines"]), "| fr lines", len(info["f_lines"]))
    json.dump(report, open(os.path.join(outdir, "layout_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main(sys.argv[1])
