"""Stickman Explainer pilot — one prompt -> script -> voice -> stickman video.

Pipeline: script.py (Groq, or built-in fallback) -> voice.py (edge-tts,
fallback gTTS, fallback silent) -> draw.py (Pillow stickman frames) ->
render.py (ffmpeg assembly, 720x1280 vertical).

No API key is needed for the demo: without GROQ_API_KEY the built-in
script is used, and voice falls back gracefully. No key ever goes in
the repo or in chat.
"""
import argparse
import json
import os
import shutil
import sys

from draw import draw_scene
from render import assemble, probe_duration
from script import get_script
from voice import make_voice


def main() -> int:
    ap = argparse.ArgumentParser(description="Stickman Explainer pilot")
    ap.add_argument("question", help="The one question, e.g. "
                    "'What did ancient humans actually do all day?'")
    ap.add_argument("--out", default="out/video.mp4",
                    help="Output mp4 path (default out/video.mp4)")
    ap.add_argument("--workdir", default="out/work",
                    help="Working dir for frames/audio (default out/work)")
    ap.add_argument("--voice", default="en-US-GuyNeural",
                    help="edge-tts voice (default en-US-GuyNeural)")
    args = ap.parse_args()

    os.makedirs(args.workdir, exist_ok=True)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)

    script, script_source = get_script(args.question)
    print(f"[script] source={script_source} scenes={len(script['scenes'])}")
    script_path = os.path.join(args.workdir, "script.json")
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2, ensure_ascii=False)

    segments = []
    total = 0.0
    for i, scene in enumerate(script["scenes"], 1):
        frame = os.path.join(args.workdir, f"scene{i}.png")
        draw_scene(scene, frame, i, len(script["scenes"]))
        audio, voice_source = make_voice(
            scene["narration"], os.path.join(args.workdir, f"scene{i}"),
            voice=args.voice)
        dur = probe_duration(audio)
        total += dur
        print(f"[scene {i}] action={scene.get('action')} voice={voice_source} "
              f"dur={dur:.1f}s frame={frame} audio={audio}")
        segments.append((frame, audio, dur))

    print(f"[render] total ~{total:.1f}s -> {args.out}")
    assemble(segments, args.out)
    print(f"[done] {args.out}  ({total:.1f}s, {len(segments)} scenes, "
          f"script={script_source})")
    print("Script JSON:", script_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
