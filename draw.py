"""Draw one 720x1280 whiteboard-style stickman frame with Pillow.

No copied images: every figure/prop is drawn from lines, circles and
polygons. Poses are parametric — head, body, arms and legs are placed
from an angle table per action, so each scene looks different.
"""
import math
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H = 720, 1280
BG = (253, 248, 238)      # off-white whiteboard
INK = (30, 30, 30)        # stickman black
ACCENT = (220, 90, 40)    # fire / sun orange
BLUE = (60, 120, 180)
GREEN = (70, 140, 70)
LW = 7                    # line width

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, size)
    except OSError:
        return ImageFont.load_default()


def _pt(cx, cy, angle_deg, length):
    a = math.radians(angle_deg)
    return (cx + length * math.sin(a), cy - length * math.cos(a))


def _dpt(cx, cy, angle_deg, length):
    """Point at angle_deg from straight DOWN (0=down, +ve=to the right)."""
    a = math.radians(angle_deg)
    return (cx + length * math.sin(a), cy + length * math.cos(a))


def stickman(d, cx, cy, pose, scale=1.0):
    """cx,cy = head centre. pose = dict of joint angles in degrees
    (0 = straight up/down, + = forward/right)."""
    head_r = 52 * scale
    d.ellipse([cx - head_r, cy - head_r, cx + head_r, cy + head_r],
              outline=INK, width=LW)
    # smile
    d.arc([cx - 22 * scale, cy - 5 * scale, cx + 22 * scale, cy + 28 * scale],
          start=20, end=160, fill=INK, width=4)
    # eyes
    for ex in (-18, 18):
        d.ellipse([cx + ex * scale - 4, cy - 18 * scale - 4,
                   cx + ex * scale + 4, cy - 18 * scale + 4], fill=INK)
    neck = (cx, cy + head_r)
    hip = (cx, cy + head_r + 150 * scale)
    d.line([neck, hip], fill=INK, width=LW)
    # arms from shoulder (angles measured from straight down;
    # ~180 = raised up, ~0 = hanging down)
    sh = (cx, cy + head_r + 35 * scale)
    for ang, ln in pose["arms"]:
        d.line([sh, _dpt(sh[0], sh[1], ang, ln * scale)], fill=INK, width=LW)
    # legs from hip (angles measured from straight down)
    for ang, ln in pose["legs"]:
        d.line([hip, _dpt(hip[0], hip[1], ang, ln * scale)], fill=INK, width=LW)
    return neck, hip


def _ground(d):
    d.line([(60, 980), (660, 980)], fill=INK, width=5)


def _sun(d, x=580, y=150):
    d.ellipse([x - 55, y - 55, x + 55, y + 55], outline=ACCENT, width=6)
    for a in range(0, 360, 45):
        p1 = _pt(x, y, a, 70)
        p2 = _pt(x, y, a, 95)
        d.line([p1, p2], fill=ACCENT, width=5)


def _moon(d, x=580, y=150):
    d.ellipse([x - 50, y - 50, x + 50, y + 50], outline=BLUE, width=6)
    d.ellipse([x - 20, y - 35, x + 35, y + 20], fill=BG, outline=BG)


def _fire(d, x=520, y=980):
    for pts, col in (
            ([(x - 70, y), (x, y - 130), (x + 70, y)], (255, 140, 40)),
            ([(x - 40, y), (x, y - 80), (x + 40, y)], (255, 200, 60))):
        d.polygon(pts, fill=col, outline=ACCENT)
    d.line([(x - 90, y), (x + 90, y)], fill=INK, width=5)


def _spear(d, hand):
    d.line([(hand[0] - 30, hand[1] + 90), (hand[0] + 30, hand[1] - 110)],
           fill=INK, width=6)
    d.polygon([(hand[0] + 30, hand[1] - 110), (hand[0] + 12, hand[1] - 78),
               (hand[0] + 48, hand[1] - 78)], fill=INK)


def _berries(d, x=520, y=920):
    d.ellipse([x - 45, y - 20, x + 45, y + 20], outline=GREEN, width=5)
    for bx in (-25, 0, 25):
        d.ellipse([x + bx - 10, y - 32, x + bx + 10, y - 12], fill=ACCENT)

# angle tables: arms/legs as (angle_deg, length_px)
POSES = {
    "wake":  {"arms": [(-155, 95), (155, 95)], "legs": [(-12, 130), (12, 130)]},
    "hunt":  {"arms": [(55, 110), (85, 100)], "legs": [(35, 130), (-25, 130)]},
    "gather":{"arms": [(-35, 100), (35, 100)], "legs": [(-10, 130), (10, 130)]},
    "fire":  {"arms": [(-25, 95), (25, 95)], "legs": [(-35, 90), (35, 90)]},
    "sleep": {"arms": [(-80, 80), (-60, 80)], "legs": [(80, 120), (95, 120)]},
    "walk":  {"arms": [(-40, 95), (40, 95)], "legs": [(30, 130), (-30, 130)]},
    "talk":  {"arms": [(-150, 90), (30, 100)], "legs": [(-12, 130), (12, 130)]},
    "cook":  {"arms": [(30, 100), (60, 95)], "legs": [(-12, 130), (12, 130)]},
    "build": {"arms": [(15, 100), (70, 100)], "legs": [(-20, 130), (20, 130)]},
    "think": {"arms": [(-60, 70), (20, 90)], "legs": [(-12, 130), (12, 130)]},
}


def draw_scene(scene, out_path, index, total):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    action = scene.get("action", "walk")
    pose = POSES.get(action, POSES["walk"])

    # header: question number + caption
    d.text((50, 55), f"SCENE {index} / {total}", font=_font(34, True), fill=BLUE)
    _y = 105
    for _line in textwrap.wrap(scene.get("caption", ""), width=30)[:2]:
        d.text((50, _y), _line, font=_font(36, True), fill=INK)
        _y += 46
    d.line([(50, 205), (670, 205)], fill=(200, 200, 200), width=3)

    _ground(d)
    cx, cy = 300, 540
    if action == "wake":
        _sun(d, 610, 285)
        stickman(d, cx, cy, pose)
    elif action == "hunt":
        _sun(d, 130, 285)
        neck, hip = stickman(d, cx, cy, pose)
        hand = _dpt(cx, cy + 52 + 35, 55, 110)
        _spear(d, hand)
    elif action == "gather":
        _sun(d, 610, 285)
        stickman(d, cx, cy, pose)
        _berries(d, 540, 900)
    elif action == "fire":
        _moon(d, 610, 285)
        stickman(d, cx, cy + 60, pose)
        _fire(d, 520, 980)
    elif action == "sleep":
        _moon(d, 610, 285)
        # lying down, horizontal figure on the ground line
        d.ellipse([150, 830, 250, 930], outline=INK, width=LW)
        d.line([(250, 880), (480, 880)], fill=INK, width=LW)
        d.line([(480, 880), (560, 840)], fill=INK, width=LW)
        d.line([(480, 880), (560, 920)], fill=INK, width=LW)
        d.line([(250, 880), (300, 840)], fill=INK, width=LW)
        d.text((480, 740), "z z z", font=_font(52, True), fill=BLUE)
    else:
        _sun(d, 610, 285)
        stickman(d, cx, cy, pose)

    # narration text, wrapped, bottom box
    box_top = 1030
    d.rectangle([40, box_top, 680, 1210], fill=(255, 255, 255),
                outline=(210, 210, 210), width=3)
    lines = textwrap.wrap(scene.get("narration", ""), width=34)
    y = box_top + 18
    for line in lines[:4]:
        d.text((65, y), line, font=_font(32), fill=INK)
        y += 42

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.save(out_path)
    return out_path
