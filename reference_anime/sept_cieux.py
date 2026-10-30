"""Visuel animé « Les sept cieux » — Al-Mulk (67), verset 3, récitation al-Afasy.
Direction artistique : nuit indigo-violette, or pâle, sept anneaux célestes concentriques
qui tournent en sens alternés, lune en halo, rayons lents, montagnes en couches et brume,
poussière d'or, carte en verre dépoli. Rend un MP4 1080x1920 30 i/s avec la récitation."""
import math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = "/tmp/claude-0/-home-claude/9e2e559f-e783-52d4-b4d6-856569bb8743/scratchpad"
AUDIO = f"{S}/rec/067003.mp3"
OUT = sys.argv[1] if len(sys.argv) > 1 else "sept_cieux.mp4"
PREVIEW = [float(x) for x in sys.argv[2:]]          # si des temps sont donnés : images fixes seulement
W, H, FPS = 1080, 1920, 30
LEAD, TAIL = 1.0, 1.5
AUD = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", AUDIO]).decode())
DUR = round(LEAD + AUD + TAIL, 2)
N = int(DUR * FPS)
random.seed(3); np.random.seed(3)

AMIRI_B = f"{S}/fonts/Amiri-1.003/Amiri-Bold.ttf"
CORM = f"{S}/gf/ofl/cormorantgaramond/CormorantGaramond[wght].ttf"
CORM_I = f"{S}/gf/ofl/cormorantgaramond/CormorantGaramond-Italic[wght].ttf"
CINZEL = f"{S}/gf/ofl/cinzel/Cinzel[wght].ttf"

def vfont(path, size, wght):
    f = ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    try: f.set_variation_by_axes([wght])
    except Exception: pass
    return f

F_AR = ImageFont.truetype(AMIRI_B, 66, layout_engine=ImageFont.Layout.RAQM)
F_FR = vfont(CORM_I, 40, 500)
F_REF = vfont(CINZEL, 25, 600)
F_BRAND = vfont(CINZEL, 30, 700)
F_KICK = vfont(CINZEL, 22, 500)

# Palette « Sept cieux »
TOP = np.array([10, 9, 34]); MID = np.array([40, 24, 82]); LOW = np.array([118, 62, 112])
GOLD = (236, 200, 128); GOLD_SOFT = (246, 224, 176); MOON = (255, 247, 228)
MX, MY = 540, 360                                      # centre de la lune et des anneaux

def ease(t): t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)
def ease_out(t): t = min(1.0, max(0.0, t)); return 1 - (1 - t) ** 3

# ---------------- couches fixes ----------------
yy = np.linspace(0, 1, H)[:, None]
g = np.where(yy < 0.45, TOP + (MID - TOP) * (yy / 0.45), MID + (LOW - MID) * ((yy - 0.45) / 0.55))
bg = np.repeat(g[:, None, :], W, axis=1).reshape(H, W, 3)
# lueur radiale autour de la lune
xs = np.arange(W)[None, :]; ys = np.arange(H)[:, None]
dist = np.sqrt((xs - MX) ** 2 + ((ys - MY) * 0.9) ** 2)
glow = np.exp(-(dist / 420) ** 2)[..., None]
bg = bg + glow * np.array([70, 48, 92]) * 0.9
BG = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert("RGBA")

# lune + halo (flou)
moon_l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(moon_l)
for r, a in [(260, 26), (190, 40), (140, 60)]:
    d.ellipse([MX - r, MY - r, MX + r, MY + r], fill=MOON + (a,))
moon_l = moon_l.filter(ImageFilter.GaussianBlur(40))
disc = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0)); dd = ImageDraw.Draw(disc)
dd.ellipse([2 * MX - 176, 2 * MY - 176, 2 * MX + 176, 2 * MY + 176], fill=MOON + (255,))
mares = Image.new("RGBA", disc.size, (0, 0, 0, 0)); dm = ImageDraw.Draw(mares)
for (ox, oy, rr, a) in [(-50, -30, 46, 30), (40, 36, 34, 24), (10, -70, 22, 22), (-20, 70, 26, 20)]:
    dm.ellipse([2 * (MX + ox) - rr, 2 * (MY + oy) - rr, 2 * (MX + ox) + rr, 2 * (MY + oy) + rr], fill=(214, 198, 184, a))
disc.alpha_composite(mares.filter(ImageFilter.GaussianBlur(6)))
disc = disc.resize((W, H), Image.LANCZOS)
moon_l.alpha_composite(disc)

# rayons (demi-résolution, tournent lentement)
RAYS = Image.new("L", (900, 900), 0); dr = ImageDraw.Draw(RAYS)
for k in range(18):
    a0 = k * 20 + random.uniform(-4, 4); w = random.uniform(2.5, 5.5)
    dr.pieslice([0, 0, 900, 900], a0, a0 + w, fill=random.randint(18, 42))
RAYS = RAYS.filter(ImageFilter.GaussianBlur(10))
rmask = Image.new("L", (900, 900), 0); ImageDraw.Draw(rmask).ellipse([0, 0, 900, 900], fill=255)
rmask = rmask.filter(ImageFilter.GaussianBlur(120))
RAYS = ImageChops.multiply(RAYS, rmask)

# montagnes en couches (2x puis réduit), plus larges pour le parallaxe
def ridge(n, base, amp, rough, seed):
    rng = np.random.default_rng(seed); pts = np.zeros(n)
    step = n - 1; pts[0] = rng.uniform(-1, 1); pts[-1] = rng.uniform(-1, 1); scale = 1.0
    while step > 1:
        half = step // 2
        for i in range(half, n - 1, step):
            pts[i] = (pts[i - half] + pts[i + half]) / 2 + rng.uniform(-1, 1) * scale
        scale *= rough; step = half
    return base - pts * amp

MW = 1240
def mountain(seed, base, amp, col_top, col_bot, rim, rough=0.55):
    w2, h2 = MW * 2, H * 2
    r = ridge(1025, base * 2, amp * 2, rough, seed)
    xs2 = np.linspace(0, w2, len(r))
    lay = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
    poly = [(0, h2)] + list(zip(xs2, r)) + [(w2, h2)]
    m = Image.new("L", (w2, h2), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
    top = int(r.min()); grad = np.zeros((h2, w2, 4), np.uint8)
    t = np.clip((np.arange(h2) - top) / (h2 * 0.35), 0, 1)[:, None]
    c = np.array(col_top) + (np.array(col_bot) - np.array(col_top)) * t
    grad[..., :3] = np.repeat(c[:, None, :], w2, axis=1).reshape(h2, w2, 3)
    grad[..., 3] = np.array(m)
    lay = Image.fromarray(grad)
    if rim:   # liseré de lumière lunaire sur les crêtes
        rl = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
        ImageDraw.Draw(rl).line(list(zip(xs2, r + 2)), fill=rim, width=5)
        lay.alpha_composite(rl)
    return lay.resize((MW, H), Image.LANCZOS)

M_FAR = mountain(11, 720, 150, (66, 46, 108), (92, 62, 120), (200, 170, 220, 110), 0.6)
M_MID = mountain(5, 810, 120, (38, 26, 72), (60, 38, 92), (226, 196, 150, 150), 0.55)
M_NEAR = mountain(23, 910, 90, (18, 13, 40), (26, 18, 52), (236, 200, 128, 120), 0.5)

# brume : bruit flou qui défile
def mist_tex(seed, w, h, alpha):
    rng = np.random.default_rng(seed)
    n = rng.random((h // 8, w // 8))
    im = Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(28))
    a = np.array(im).astype(float) / 255.0
    yv = np.linspace(0, 1, h)[:, None]; band = np.exp(-((yv - 0.5) / 0.28) ** 2)
    a = np.clip((a - 0.35) * 2.2, 0, 1) * band * alpha
    out = np.zeros((h, w, 4), np.uint8); out[..., :3] = (210, 190, 230); out[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(out)
MIST1 = mist_tex(1, 2400, 260, 0.55)
MIST2 = mist_tex(2, 2400, 220, 0.45)

# étoiles (3 profondeurs), poussière d'or
stars = []
for depth, n, rr in [(0.2, 160, (0.6, 1.4)), (0.5, 70, (1.2, 2.2)), (1.0, 22, (2.0, 3.4))]:
    for _ in range(n):
        stars.append([random.uniform(0, W), random.uniform(0, 1000), random.uniform(*rr), depth,
                      random.uniform(0, 6.28), random.uniform(0.8, 2.6)])
dust = [[random.uniform(60, W - 60), random.uniform(600, 1900), random.uniform(1.2, 3.0),
         random.uniform(14, 34), random.uniform(0, 6.28)] for _ in range(46)]

# vignette + grain
vx = (xs - W / 2) / (W / 2); vy = (ys - H / 2) / (H / 2)
vig = np.clip((np.sqrt(vx ** 2 * 0.9 + vy ** 2 * 0.6) - 0.55) * 1.2, 0, 1) ** 1.6
VIG = np.zeros((H, W, 4), np.uint8); VIG[..., 3] = (vig * 170).astype(np.uint8); VIG[..., :3] = (6, 4, 18)
VIG = Image.fromarray(VIG)
GRAIN = [np.random.normal(0, 5.5, (H, W, 1)).astype(np.int16) for _ in range(6)]

# ---------------- textes rendus par Chromium ----------------
import json
AR = "الَّذِي خَلَقَ سَبْعَ سَمَاوَاتٍ طِبَاقًاۖ مَا تَرَىٰ فِي خَلْقِ الرَّحْمَٰنِ مِنْ تَفَاوُتٍۖ فَارْجِعِ الْبَصَرَ هَلْ تَرَىٰ مِنْ فُطُورٍ"
FR = ("Celui qui a créé sept cieux superposés sans que tu voies de disproportion en la création "
      "du Tout Miséricordieux. Ramène [sur elle] le regard. Y vois-tu une brèche quelconque ?")
TXT = "txt"; os.makedirs(TXT, exist_ok=True)
gold_css = "rgb(%d,%d,%d)" % GOLD
spec = {"fonts": {"AmiriB": AMIRI_B, "CormI": CORM_I, "Cinzel": CINZEL},
  "blocks": [
    {"id": "kick", "text": "ALLAH LE TRÈS-HAUT A DIT", "font": "Cinzel", "size": 22, "lh": 1.2, "color": gold_css, "weight": 500, "ls": 5, "width": 860},
    {"id": "ar", "text": AR, "font": "AmiriB", "size": 56, "lh": 1.8, "color": "#fffcf4", "dir": "rtl", "lang": "ar", "width": 860,
     "shadow": "0 3px 10px rgba(0,0,0,.55)"},
    {"id": "fr", "text": FR, "font": "CormI", "size": 36, "lh": 1.32, "color": "#f2e8de", "weight": 500, "width": 880,
     "shadow": "0 2px 8px rgba(0,0,0,.5)"},
    {"id": "ref", "text": "AL-MULK &nbsp;·&nbsp; SOURATE 67 &nbsp;·&nbsp; VERSET 3", "font": "Cinzel", "size": 24, "lh": 1.2, "color": gold_css, "weight": 600, "ls": 3, "width": 860},
    {"id": "brand", "text": "DHIKRÂ &nbsp;<span style=\"font-family:AmiriB;font-size:40px\">ذِكْرَى</span>", "font": "Cinzel", "size": 30, "lh": 1.2, "color": gold_css, "weight": 700, "ls": 4, "width": 500},
  ]}
json.dump(spec, open(f"{TXT}/spec.json", "w"), ensure_ascii=False)
subprocess.run(["node", "render_text.js", f"{TXT}/spec.json", TXT], check=True)
T = {k: Image.open(f"{TXT}/{k}.png").convert("RGBA") for k in ["kick", "ar", "fr", "ref", "brand"]}

CX0, CX1, RAD = 64, W - 64, 28
CY0 = 880
y = CY0 + 40
P = {}
P["kick"] = y - 14; y += T["kick"].height - 30
P["ar"] = y - 10; y += T["ar"].height - 26
SEP_Y = y + 10; y += 30
P["fr"] = y - 16; y += T["fr"].height - 26
P["ref"] = y - 16; y += T["ref"].height - 30
CY1 = y + 34
P["brand"] = CY1 + 46
print("bas de carte", CY1, "| durée", DUR)

cmask = Image.new("L", (W, H), 0)
ImageDraw.Draw(cmask).rounded_rectangle([CX0, CY0, CX1, CY1], RAD, fill=255)
deco = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0)); dc = ImageDraw.Draw(deco)
dc.rounded_rectangle([2 * CX0, 2 * CY0, 2 * CX1, 2 * CY1], 2 * RAD, outline=GOLD + (220,), width=3)
dc.rounded_rectangle([2 * CX0 + 22, 2 * CY0 + 22, 2 * CX1 - 22, 2 * CY1 - 22], 2 * RAD - 16, outline=GOLD + (90,), width=2)
def star8(dc, cx, cy, r, fill):
    pts = []
    for k in range(16):
        ang = math.pi / 8 * k - math.pi / 2
        rr = r if k % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    dc.polygon(pts, fill=fill)
dc.ellipse([W - 44, 2 * CY0 - 44, W + 44, 2 * CY0 + 44], fill=(26, 18, 52, 255), outline=GOLD + (230,), width=3)
star8(dc, W, 2 * CY0, 30, GOLD + (255,))
for (x, y_, sx, sy) in [(CX0, CY0, 1, 1), (CX1, CY0, -1, 1), (CX0, CY1, 1, -1), (CX1, CY1, -1, -1)]:
    X, Y = 2 * x + sx * 54, 2 * y_ + sy * 54
    dc.polygon([(X, Y - 12), (X + 12, Y), (X, Y + 12), (X - 12, Y)], fill=GOLD + (230,))
    dc.line([(X + sx * 22, Y), (X + sx * 90, Y)], fill=GOLD + (150,), width=2)
    dc.line([(X, Y + sy * 22), (X, Y + sy * 90)], fill=GOLD + (150,), width=2)
DECO = deco.resize((W, H), Image.LANCZOS)

frame = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0)); df = ImageDraw.Draw(frame)
df.rectangle([56, 56, 2 * W - 56, 2 * H - 56], outline=GOLD_SOFT + (70,), width=2)
df.rectangle([72, 72, 2 * W - 72, 2 * H - 72], outline=GOLD_SOFT + (40,), width=2)
for r in range(70, 240, 34):
    df.arc([80 - r, 2 * H - 80 - r, 80 + r, 2 * H - 80 + r], 270, 360, fill=GOLD_SOFT + (60,), width=2)
    df.arc([2 * W - 80 - r, 80 - r, 2 * W - 80 + r, 80 + r], 90, 180, fill=GOLD_SOFT + (60,), width=2)
FRAME = frame.resize((W, H), Image.LANCZOS)

def wipe(im, p, rtl):
    """Révélation en balayage doux (droite→gauche pour l'arabe)."""
    if p >= 1: return im
    w_ = im.width; edge = 160
    x = np.arange(w_)
    pos = (w_ - x) if rtl else x
    front = p * (w_ + edge)
    a = np.clip((front - pos) / edge, 0, 1)
    m = (np.array(im.getchannel("A")).astype(float) * a[None, :]).astype(np.uint8)
    c = im.copy(); c.putalpha(Image.fromarray(m)); return c

T_KICK, T_AR, T_FR, T_REF = 2.3, 2.7, 5.4, 7.2
def faded(im, a):
    if a >= 0.999: return im
    c = im.copy(); c.putalpha(c.getchannel("A").point(lambda v: int(v * a))); return c

# ---------------- rendu d'une image ----------------
def render(t):
    img = BG.copy()
    # rayons
    ang = t * 2.2
    rays = RAYS.rotate(ang, resample=Image.BICUBIC).resize((1800, 1800), Image.BILINEAR)
    rl = Image.new("RGBA", rays.size, MOON + (0,)); rl.putalpha(rays)
    img.alpha_composite(rl, (MX - 900, MY - 900))
    # couche dynamique 2x : étoiles + anneaux
    SS = 2; dh = 1150
    dyn = Image.new("RGBA", (W * SS, dh * SS), (0, 0, 0, 0)); dd = ImageDraw.Draw(dyn)
    for s in stars:
        x = (s[0] + t * 6 * s[3]) % W; y_ = s[1] + math.sin(t * 0.3 + s[0]) * 2 * s[3]
        tw = 0.55 + 0.45 * math.sin(t * s[5] + s[4])
        r = s[2] * (0.8 + 0.3 * tw) * SS
        dd.ellipse([x * SS - r, y_ * SS - r, x * SS + r, y_ * SS + r], fill=(240, 236, 255, int(70 + 180 * tw)))
        if s[3] == 1.0 and tw > 0.8:       # scintillement en croix pour les plus proches
            L = r * 4
            dd.line([(x * SS - L, y_ * SS), (x * SS + L, y_ * SS)], fill=(240, 236, 255, 90), width=2)
            dd.line([(x * SS, y_ * SS - L), (x * SS, y_ * SS + L)], fill=(240, 236, 255, 90), width=2)
    # sept anneaux : apparition en balayage puis rotation alternée
    for k in range(7):
        R = (230 + k * 62) * SS
        appear = ease_out((t - 0.2 - 0.28 * k) / 1.4)
        if appear <= 0: continue
        rot = (t * (6 + k * 1.3)) * (1 if k % 2 == 0 else -1)
        a = int((190 - k * 18) * appear)
        box = [MX * SS - R, MY * SS - R, MX * SS + R, MY * SS + R]
        sweep = 360 * appear
        if k % 3 == 0:        # anneau de points
            n = 72 + k * 12
            for j in range(n):
                th = j / n * 360
                if th > sweep: break
                rad = math.radians(th + rot)
                px, py = MX * SS + R * math.cos(rad), MY * SS + R * math.sin(rad)
                pr = 2.2 * SS if j % 6 == 0 else 1.2 * SS
                dd.ellipse([px - pr, py - pr, px + pr, py + pr], fill=GOLD + (a,))
        elif k % 3 == 1:      # anneau en tirets
            n = 36 + k * 4
            for j in range(n):
                th = j / n * 360
                if th > sweep: break
                dd.arc(box, th + rot, th + rot + 360 / n * 0.55, fill=GOLD_SOFT + (a,), width=2 * SS)
        else:                 # anneau continu + 4 losanges
            dd.arc(box, rot, rot + sweep, fill=GOLD + (int(a * 0.7),), width=SS)
            for q in range(4):
                th = q * 90 + rot
                if q * 90 > sweep: continue
                rad = math.radians(th); px, py = MX * SS + R * math.cos(rad), MY * SS + R * math.sin(rad)
                dd.polygon([(px, py - 9 * SS), (px + 6 * SS, py), (px, py + 9 * SS), (px - 6 * SS, py)], fill=GOLD + (a,))
    # étoile filante
    for t0, x0, y0 in [(5.5, 180, 140), (13.2, 980, 230)]:
        p = (t - t0) / 0.9
        if 0 <= p <= 1:
            dirx = 1 if x0 < W / 2 else -1
            hx, hy = x0 + dirx * 420 * p, y0 + 210 * p
            for k in range(12):
                q = k / 12; tx, ty = hx - dirx * 160 * q, hy - 80 * q
                al = int(230 * (1 - q) * math.sin(math.pi * p))
                rr = (2.6 - 2.0 * q) * SS
                dd.ellipse([tx * SS - rr, ty * SS - rr, tx * SS + rr, ty * SS + rr], fill=(255, 245, 225, al))
    dyn = dyn.resize((W, dh), Image.LANCZOS)
    img.alpha_composite(dyn, (0, 0))
    # lune qui respire
    img.alpha_composite(moon_l)
    br = 0.5 + 0.5 * math.sin(t * 1.1)
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rr = 196 + 10 * br
    ImageDraw.Draw(ring).ellipse([MX - rr, MY - rr, MX + rr, MY + rr], outline=MOON + (int(40 + 40 * br),), width=3)
    img.alpha_composite(ring)
    # montagnes + brume en parallaxe
    for lay, amp, sp in [(M_FAR, 18, 0.10), (None, 0, 0), (M_MID, 36, 0.13), (None, 1, 0), (M_NEAR, 60, 0.16)]:
        if lay is None:
            mist = MIST1 if amp == 0 else MIST2
            off = int((t * (22 if amp == 0 else 34)) % 1200)
            yv = 720 if amp == 0 else 830
            img.alpha_composite(mist.crop((off, 0, off + W, mist.height)), (0, yv))
            continue
        ox = int((MW - W) / 2 + amp * math.sin(t * sp))
        img.alpha_composite(lay.crop((ox, 0, ox + W, H)))
    # poussière d'or qui monte
    pl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(pl)
    for p in dust:
        y_ = (p[1] - t * p[3]) % 1400 + 520
        x = p[0] + 18 * math.sin(t * 0.7 + p[4])
        al = int(160 * (0.5 + 0.5 * math.sin(t * 1.7 + p[4])))
        r = p[2]
        dp.ellipse([x - r * 3, y_ - r * 3, x + r * 3, y_ + r * 3], fill=GOLD + (al // 6,))
        dp.ellipse([x - r, y_ - r, x + r, y_ + r], fill=GOLD_SOFT + (al,))
    img.alpha_composite(pl)
    # carte en verre dépoli
    ca = ease((t - 1.6) / 0.9)
    if ca > 0:
        dy = int(26 * (1 - ease_out((t - 1.6) / 0.9)))
        reg = img.crop((0, CY0 - 40, W, CY1 + 40))
        blur = reg.resize((W // 6, reg.height // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3)).resize(reg.size, Image.BICUBIC)
        tint = Image.new("RGBA", reg.size, (16, 10, 36, 196))
        blur.alpha_composite(tint)
        glass = Image.new("RGBA", (W, H), (0, 0, 0, 0)); glass.paste(blur, (0, CY0 - 40))
        m = cmask.point(lambda v: int(v * ca))
        if dy: m = ImageChops.offset(m, 0, dy)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.6)))
        img.alpha_composite(ImageChops.offset(sh, 0, 14))
        glass.putalpha(m); img.alpha_composite(glass)
        img.alpha_composite(faded(ImageChops.offset(DECO, 0, dy), ca))
        sp = ease_out((t - (T_FR - 0.6)) / 0.8)
        if sp > 0:
            sl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sl)
            half = 330 * sp
            ds.line([(W / 2 - half, SEP_Y + dy), (W / 2 + half, SEP_Y + dy)], fill=GOLD + (200,), width=2)
            ds.polygon([(W / 2, SEP_Y - 7 + dy), (W / 2 + 7, SEP_Y + dy), (W / 2, SEP_Y + 7 + dy), (W / 2 - 7, SEP_Y + dy)], fill=GOLD + (255,))
            img.alpha_composite(sl)
        def put(k, im):
            img.alpha_composite(im, ((W - im.width) // 2, P[k] + dy))
        a = ease((t - T_KICK) / 0.7)
        if a > 0: put("kick", faded(T["kick"], a))
        p = (t - T_AR) / 2.4
        if p > 0: put("ar", wipe(T["ar"], ease(p), True))
        p = (t - T_FR) / 1.8
        if p > 0: put("fr", wipe(T["fr"], ease(p), False))
        a = ease((t - T_REF) / 0.8)
        if a > 0: put("ref", faded(T["ref"], a))
    ba = ease((t - 1.0) / 1.2)
    if ba > 0:
        img.alpha_composite(faded(T["brand"], ba), ((W - T["brand"].width) // 2, P["brand"]))
    img.alpha_composite(FRAME)
    img.alpha_composite(VIG)
    # léger mouvement de caméra (zoom lent) + fondu de fin
    z = 1.0 + 0.035 * ease(t / DUR)
    cw, ch = int(W / z), int(H / z)
    img = img.crop(((W - cw) // 2, (H - ch) // 2 - int(10 * t / DUR), (W - cw) // 2 + cw, (H - ch) // 2 - int(10 * t / DUR) + ch)).resize((W, H), Image.BICUBIC)
    arr = np.asarray(img.convert("RGB")).astype(np.int16) + GRAIN[int(t * FPS) % len(GRAIN)]
    fin = ease((DUR - t) / 0.8); start = ease(t / 0.6)
    arr = arr * min(fin, start)
    return np.clip(arr, 0, 255).astype(np.uint8)

if PREVIEW:
    for tt in PREVIEW:
        Image.fromarray(render(tt)).save(f"prev_{tt:05.1f}.png")
    sys.exit(0)

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    "-i", AUDIO,
    "-filter_complex", f"[1:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-1.5,adelay={int(LEAD*1000)}|{int(LEAD*1000)},apad[a]",
    "-map", "0:v", "-map", "[a]", "-t", str(DUR),
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for i in range(N):
    ff.stdin.write(render(i / FPS).tobytes())
    if i % 90 == 0: print("image", i, "/", N, flush=True)
ff.stdin.close(); ff.wait(); print("ok", OUT)
