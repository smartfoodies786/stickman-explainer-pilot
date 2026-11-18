"""ONE animated scene demo — the hook.
"What did ancient humans actually do all day?"

NOT a slideshow: every frame (24fps, 7s = 168 frames) is drawn
from scratch in Pillow with a parametric stickman whose pose
interpolates through phases:

  0.0-1.2s  walk in from the left (legs + arms swing, head bob)
  1.2-2.6s  stop + big stretch (arms up, body rises, sleepy eyes)
  2.6-4.0s  confused (head tilt, shrug, wide eyes, "?" pops)
  4.0-7.0s  point up at the question (arm rotates up, text pops
            word-by-word, slow camera zoom-in throughout)

Camera: continuous zoom 1.00 -> 1.08 (centre crop + resize).
Voice: same fallbacks as the pilot (edge-tts -> gTTS -> flite),
delayed ~3.8s so it lands on the pointing gesture.
"""
import math, os, sys, subprocess, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from voice import make_voice  # noqa: E402
from render import probe_duration  # noqa: E402

W, H = 720, 1280
FPS = 24
DUR = 7.0
BG = (253, 248, 238)
INK = (30, 30, 30)
ACCENT = (220, 90, 40)
BLUE = (60, 120, 180)
LW = 7
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
QUESTION = "What did ancient humans actually do all day?"
NARRATION = QUESTION


def _font(size, bold=False):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT, max(8, int(size)))
    except OSError:
        return ImageFont.load_default()


def _dpt(cx, cy, angle_deg, length):
    """Point at angle from straight DOWN (0=down, 180=up)."""
    a = math.radians(angle_deg)
    return (cx + length * math.sin(a), cy + length * math.cos(a))


def _lerp(a, b, t):
    return a + (b - a) * t


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _word_layout():
    """Pre-compute (word, x, y) for the question, wrapped to 620px."""
    font = _font(54, True)
    words, lines, cur, y = QUESTION.split(), [], [], 115
    for w in words:
        trial = (cur + [w])
        width = sum(ImageDraw.Draw(Image.new("RGB", (10, 10))).textlength(x + " ", font=font) for x in trial)
        if width > 620 and cur:
            lines.append((cur, y)); y += 72; cur = [w]
        else:
            cur = trial
    if cur:
        lines.append((cur, y))
    out = []
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for line_words, ly in lines:
        x = 50
        for w in line_words:
            out.append((w, x, ly))
            x += tmp.textlength(w + " ", font=font)
    return out


WORDS = _word_layout()


def _draw_stickman(d, cx, cy, scale, arm_l, arm_r, leg_l, leg_r, eye, mouth, tilt=0.0):
    """cx,cy = head centre. arm/leg = (angle_from_down, length).
    Angles are the key animation channel: they change every frame."""
    hr = 52 * scale
    # head (tilt = horizontal offset of features, cheap fake tilt)
    d.ellipse([cx - hr, cy - hr, cx + hr, cy + hr], outline=INK, width=LW)
    # eyes
    if eye == "sleepy":  # closed lines
        for ex in (-18, 18):
            d.line([(cx + (ex - 10) * scale + tilt, cy - 18 * scale),
                    (cx + (ex + 10) * scale + tilt, cy - 18 * scale)], fill=INK, width=4)
    elif eye == "wide":  # big surprised circles
        for ex in (-18, 18):
            d.ellipse([cx + ex * scale - 9 + tilt, cy - 18 * scale - 9,
                       cx + ex * scale + 9 + tilt, cy - 18 * scale + 9],
                      outline=INK, width=4)
        d.ellipse([cx - 18 * scale - 3 + tilt, cy - 18 * scale - 3,
                   cx - 18 * scale + 3 + tilt, cy - 18 * scale + 3], fill=INK)
        d.ellipse([cx + 18 * scale - 3 + tilt, cy - 18 * scale - 3,
                   cx + 18 * scale + 3 + tilt, cy - 18 * scale + 3], fill=INK)
    else:  # normal dots
        for ex in (-18, 18):
            d.ellipse([cx + ex * scale - 4 + tilt, cy - 18 * scale - 4,
                       cx + ex * scale + 4 + tilt, cy - 18 * scale + 4], fill=INK)
    # mouth
    if mouth == "o":
        d.ellipse([cx - 11 * scale + tilt, cy + 14 * scale,
                   cx + 11 * scale + tilt, cy + 34 * scale], outline=INK, width=4)
    elif mouth == "flat":
        d.line([(cx - 16 * scale + tilt, cy + 22 * scale),
                (cx + 16 * scale + tilt, cy + 22 * scale)], fill=INK, width=4)
    else:  # smile
        d.arc([cx - 22 * scale + tilt, cy - 5 * scale, cx + 22 * scale + tilt, cy + 28 * scale],
              start=20, end=160, fill=INK, width=4)
    neck = (cx, cy + hr)
    hip = (cx, cy + hr + 150 * scale)
    d.line([neck, hip], fill=INK, width=LW)
    sh = (cx, cy + hr + 35 * scale)
    for ang, ln in (arm_l, arm_r):
        d.line([sh, _dpt(sh[0], sh[1], ang, ln * scale)], fill=INK, width=LW)
    for ang, ln in (leg_l, leg_r):
        d.line([hip, _dpt(hip[0], hip[1], ang, ln * scale)], fill=INK, width=LW)
    return sh, hip


def draw_frame(t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # sun + ground (static set dressing) — sun sits mid-right, BELOW the
    # question text (top-right collided with the last word before)
    d.ellipse([575, 380, 665, 470], outline=ACCENT, width=6)
    for a in range(0, 360, 45):
        x, y = 620, 425
        p1 = (x + 55 * math.sin(math.radians(a)), y - 55 * math.cos(math.radians(a)))
        p2 = (x + 75 * math.sin(math.radians(a)), y - 75 * math.cos(math.radians(a)))
        d.line([p1, p2], fill=ACCENT, width=5)
    d.line([(60, 980), (660, 980)], fill=INK, width=5)
    d.text((50, 62), "SCENE 1 — THE HOOK", font=_font(30, True), fill=BLUE)

    # ---- pose timeline (all angles in degrees from straight down) ----
    bob = 0.0
    if t < 1.2:  # WALK IN: x 90 -> 360, legs/arms swing, head bob
        k = _smooth(t / 1.2)
        cx = _lerp(90, 360, k)
        step = math.sin(t * 12)  # ~2 steps in 1.2s
        leg_l, leg_r = (32 * step, 130), (-32 * step, 130)
        arm_l, arm_r = (-38 * step, 95), (38 * step, 95)
        eye, mouth, cy = "normal", "smile", 640 - abs(step) * 8
        bob = abs(step) * 8
    elif t < 2.6:  # STRETCH: arms rise up, body lifts, sleepy eyes
        k = _smooth((t - 1.2) / 1.4)
        cx = 360
        arm_l = (_lerp(-10, -155, k), 95)
        arm_r = (_lerp(10, 155, k), 95)
        leg_l, leg_r = (-12, 130), (12, 130)
        eye, mouth = "sleepy", "flat"
        cy = 640 - 22 * math.sin(k * math.pi)  # rise then settle
    elif t < 4.0:  # CONFUSED: shrug (arms out-up), head tilt, wide eyes
        k = _smooth((t - 2.6) / 1.4)
        cx = 360
        arm_r = (_lerp(155, 130, k), 95)
        arm_l = (_lerp(-155, -130, k), 95)
        leg_l, leg_r = (-12, 130), (12, 130)
        eye, mouth = "wide", "o"
        cy = 640
        tilt = 14 * math.sin(k * math.pi)
        # "?" pops above head
        if k > 0.3:
            s = 1.0 + 0.5 * max(0, 1 - (k - 0.3) / 0.2)
            d.text((470, 480), "?", font=_font(int(90 * s), True), fill=ACCENT)
        _draw_stickman(d, cx, cy, 1.0, arm_l, arm_r, leg_l, leg_r, eye, mouth, tilt=tilt)
        _finish(d, t)
        return _zoom(img, t)
    else:  # POINT UP-RIGHT: arm at 145deg, diagonal — 168deg went
        # straight up from the shoulder THROUGH the head (seen in check)
        k = _smooth((t - 4.0) / 1.0)
        cx = 360
        arm_r = (_lerp(130, 145, k), 115)  # sweep up-right to point at text
        arm_l = (_lerp(-130, 15, k), 95)
        leg_l, leg_r = (-12, 130), (12, 130)
        eye, mouth = "wide", "o"
        cy = 640
        # pointing finger dot at hand
        hand = _dpt(cx, cy + 52 + 35, 145, 115)
        d.ellipse([hand[0] - 8, hand[1] - 8, hand[0] + 8, hand[1] + 8], fill=ACCENT)
        _draw_stickman(d, cx, cy, 1.0, arm_l, arm_r, leg_l, leg_r, eye, mouth, tilt=6)
    _draw_stickman(d, cx, cy, 1.0, arm_l, arm_r, leg_l, leg_r, eye, mouth)
    _finish(d, t)
    return _zoom(img, t)


def _finish(d, t):
    """Question text (word-by-word pop from t=4.0) + narration box."""
    # question words pop in, one every 0.25s from t=4.0
    for i, (w, x, y) in enumerate(WORDS):
        appear = 4.0 + i * 0.25
        if t >= appear:
            age = t - appear
            pop = 1.0 + 0.45 * max(0.0, 1.0 - age / 0.18)  # overshoot then settle
            d.text((x, y - 6 * (pop - 1.0)), w, font=_font(int(54 * pop), True),
                   fill=ACCENT if w == "day?" else INK)
    # narration box
    d.rectangle([40, 1030, 680, 1210], fill=(255, 255, 255), outline=(210, 210, 210), width=3)
    d.text((65, 1055), "What did ancient humans", font=_font(32), fill=INK)
    d.text((65, 1100), "actually do all day?", font=_font(32, True), fill=INK)
    d.text((65, 1150), "Let's find out.", font=_font(28), fill=BLUE)


def _zoom(img, t):
    """Slow camera zoom 1.00 -> 1.08 across the scene."""
    z = 1.0 + 0.08 * (t / DUR)
    cw, ch = int(W / z), int(H / z)
    x0, y0 = (W - cw) // 2, (H - ch) // 2
    return img.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    frames = os.path.join(base, "work", "frames")
    os.makedirs(frames, exist_ok=True)
    out = os.path.join(base, "animated-scene-1.mp4")

    t0 = time.time()
    n = int(FPS * DUR)
    for i in range(n):
        draw_frame(i / FPS).save(os.path.join(frames, f"f{i:04d}.png"))
    print(f"[frames] {n} frames in {time.time() - t0:.1f}s")

    audio, src = make_voice(NARRATION, os.path.join(base, "work", "scene1"))
    adur = probe_duration(audio)
    print(f"[voice] source={src} dur={adur:.1f}s file={audio}")
    delay_ms = 3800  # voice lands on the pointing gesture
    subprocess.run([
        "ffmpeg", "-y", "-v", "error",
        "-framerate", str(FPS), "-i", os.path.join(frames, "f%04d.png"),
        "-i", audio,
        "-filter_complex",
        f"[1:a]adelay={delay_ms}|{delay_ms},apad[a]",
        "-map", "0:v", "-map", "[a]",
        "-t", f"{DUR:.1f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "128k", out], check=True)
    print(f"[done] {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
