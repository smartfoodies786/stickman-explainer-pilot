# Stickman Explainer — Pilot

One prompt in, one vertical explainer video out. Inspired by the
Eliro-style stickman Shorts (stick figure + voice + one question),
rebuilt as a free, local, no-GPU pipeline.

**What it does**

```
python main.py "What did ancient humans actually do all day?" --out out/video.mp4
```

1. **Script** — Groq (`gpt-oss-20b`) writes 5 scenes (narration + action
   + caption). No key? A built-in template is used instead, so the demo
   always works.
2. **Voice** — edge-tts first (free, no key), then gTTS, then offline
   flite via ffmpeg (robotic but real, no network), then silent audio
   sized to the text as a last resort. The log always says which one ran.
3. **Visuals** — Pillow draws every frame from code: whiteboard style,
   720×1280, one stickman pose per action (wake / hunt / gather / fire /
   sleep …). No copied images.
4. **Edit** — ffmpeg stitches one still + its voice per scene into a
   720×1280 H.264 + AAC mp4, ~30 seconds.

## Setup (3 steps)

```bash
git clone https://github.com/smartfoodies786/stickman-explainer-pilot.git
cd stickman-explainer-pilot
pip install -r requirements.txt   # needs Python 3.10+ and ffmpeg on PATH
```

Roman-Urdu: pehle repo clone karo, phir `pip install -r requirements.txt`,
phir neeche wala command chalao. `ffmpeg` pehle se installed hona chahiye
(`ffmpeg -version` se check karo).

## Run

```bash
# Demo (no key needed — built-in script + best available free voice)
python main.py "What did ancient humans actually do all day?" --out out/video.mp4

# With your own script (free Groq key — never paste it in chat or in a file)
export GROQ_API_KEY="your-key-here"
python main.py "Why is the sky blue?" --out out/video.mp4

# Different voice (edge-tts voice name)
python main.py "What did ancient humans actually do all day?" --voice en-US-AriaNeural
```

The script JSON for each run is saved at `out/work/script.json`.
A rendered sample is in `out/sample.mp4` and its script in
`examples/sample-script.json`.

## Verified pilot run (2026-11-18, this repo's author machine)

- Question: "What did ancient humans actually do all day?"
- Output: `out/sample.mp4` — **28.5 s, 720×1280, H.264 + AAC, 445 KB**
- Audio: real voice, mean volume −16.2 dB (not silent)
- Script path used: **fallback template** (no `GROQ_API_KEY` was set)
- Voice path used: **flite-offline** — edge-tts was blocked by that
  machine's network proxy (SSL error) and gTTS answered 429, so the
  offline flite voice ran instead. On a normal PC / laptop, edge-tts
  usually works first and sounds much more human.

## Honest limits

- **Stickman only.** No realistic video, no Veo, no GPU — that is the
  point: it is cheap and free, but it will never look like a filmed scene.
- **Voice is TTS, not a human.** edge-tts sounds decent; the offline
  flite fallback sounds robotic. Pick the voice with `--voice`.
- **Script quality = Groq free tier.** Without a key you only get the
  built-in ancient-humans script (other questions reuse its 5 beats
  with your question in scene 1). With a key, Groq writes a fresh
  script per question, within its free-tier rate limits.
- **No viral guarantee.** The Eliro channel this copies has 21 videos,
  171K subscribers and one 18M-view video — the tool can copy the
  *format*, not the views. Views depend on the question, the script
  and distribution.
- **Still images per scene.** Each scene is one drawn frame held for
  the narration — no frame-by-frame animation yet. That is the next
  step if the pilot is worth continuing (simple arm/head movement,
  then a web UI).
- No key, token or password is ever stored in this repo. `GROQ_API_KEY`
  comes from the environment only.
