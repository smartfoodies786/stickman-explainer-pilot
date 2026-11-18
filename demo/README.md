# Demo — Scene 1, animated (the hook)

One scene only, answering the pilot's main complaint: the pilot was a
slideshow (one still per scene). This scene is drawn **frame by frame**
at 24 fps, 7 seconds, 720×1280.

## What moves

- **0.0–1.2s** — stickman walks in from the left (legs + arms swing, head bob)
- **1.2–2.6s** — stops, big stretch (arms up, sleepy eyes)
- **2.6–4.0s** — confused shrug, wide eyes, "O" mouth, big "?" pops in
- **4.0–7.0s** — points up-right at the question; the question pops in
  word by word; slow camera zoom-in (1.00 → 1.08) runs the whole scene
- Voice: "What did ancient humans actually do all day?" — delayed to
  land on the pointing gesture

## Run it

```bash
cd demo
../.venv/bin/python animate_scene.py   # or: python animate_scene.py
# output: demo/animated-scene-1.mp4
```

Needs Python 3.10+ and ffmpeg. Voice uses the same fallbacks as the
pilot (edge-tts → gTTS → offline flite); the log says which one ran.

## Verified run (2026-11-18, this repo's author machine)

- Output: `animated-scene-1.mp4` — **7.0 s, 720×1280, H.264 + AAC, 523 KB**
- Audio: real voice, mean volume **−18.1 dB** (not silent)
- Voice path used: **flite-offline** — edge-tts blocked by that
  machine's network proxy (SSL error), gTTS answered 429. On a normal
  PC/laptop edge-tts usually works first and sounds much more human.
- Render: 168 frames in 13.2 s, 24 fps (total run ~23 s incl. ffmpeg)
- Frames checked visually at t=0.5 / 3.2 / 6.0 s: walking pose (left,
  legs mid-stride) → shrug + "?" (centre, wide eyes) → pointing
  up-right at the full question (arm clear of the head, text readable,
  no sun collision). Two bugs found in the first render and fixed:
  the pointing arm went straight up *through* the head (now 145°,
  diagonal) and the question text overlapped the sun (sun moved below
  the text).

## Honest limits

- Still a code-drawn stickman — no realistic video, no Veo, no GPU.
- Voice in this VM is the robotic flite fallback (see above).
- This is one scene, not the full v2 video. If this feels engaging
  enough, the same animation engine gets applied to all 5 scenes.
