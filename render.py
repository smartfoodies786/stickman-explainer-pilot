"""Render: one still image + its audio per scene -> segment mp4s,
then concat to the final 720x1280 H.264/AAC mp4 with ffmpeg.
"""
import json
import os
import subprocess


def _run(cmd):
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def probe_duration(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", path], capture_output=True, text=True, check=True)
    return float(json.loads(out.stdout)["format"]["duration"])


def assemble(segments, out_path: str):
    workdir = os.path.dirname(os.path.abspath(segments[0][0]))
    seg_files = []
    for i, (frame, audio, dur) in enumerate(segments, 1):
        seg = os.path.join(workdir, f"seg{i}.mp4")
        # -loop 1 still image for exactly the audio duration; pad a
        # fraction so the last frame is not cut short.
        _run(["ffmpeg", "-y", "-v", "error",
              "-loop", "1", "-i", frame, "-i", audio,
              "-t", f"{dur + 0.15:.2f}",
              "-vf", "scale=720:1280,format=yuv420p",
              "-c:v", "libx264", "-r", "30", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "128k", "-shortest", seg])
        seg_files.append(seg)

    lst = os.path.join(workdir, "concat.txt")
    with open(lst, "w") as f:
        for s in seg_files:
            f.write(f"file '{s}'\n")
    _run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
          "-i", lst, "-c", "copy", out_path])
    return out_path
