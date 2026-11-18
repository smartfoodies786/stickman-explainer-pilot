"""Voice: edge-tts first (free, no key), then gTTS (free, no key),
then offline flite via ffmpeg (robotic but real, no network),
then a silent WAV sized to the text at ~150 wpm so the video still
assembles with correct timing. Returns (audio_path, source_name).
"""
import math
import os
import subprocess
import wave


def estimate_seconds(text: str) -> float:
    words = max(1, len(text.split()))
    return max(2.0, words / 150.0 * 60.0)


def _silent_wav(path: str, seconds: float) -> str:
    rate = 22050
    n = int(rate * seconds)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n)
    return path


def make_voice(text: str, base_path: str, voice: str = "en-US-GuyNeural"):
    """base_path without extension; returns (path, source)."""
    seconds = estimate_seconds(text)

    # 1) edge-tts (Microsoft free TTS, no key)
    mp3 = base_path + ".mp3"
    try:
        import edge_tts
        import asyncio

        async def _run():
            await edge_tts.Communicate(text, voice).save(mp3)

        asyncio.run(_run())
        if os.path.getsize(mp3) > 1000:
            return mp3, "edge-tts"
    except Exception as e:
        print(f"[voice] edge-tts failed: {e}")

    # 2) gTTS (Google free TTS, no key)
    try:
        from gtts import gTTS

        gTTS(text=text, lang="en").save(mp3)
        if os.path.getsize(mp3) > 1000:
            return mp3, "gtts"
    except Exception as e:
        print(f"[voice] gTTS failed: {e}")

    # 3) flite via ffmpeg (offline, no key, no network — robotic voice,
    #    but a real voice; works wherever ffmpeg is installed)
    wav = base_path + ".wav"
    try:
        safe = text.replace("\\", " ").replace("'", "\u2019") \
            .replace(":", " ").replace(";", " ").replace("%", " percent")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
             "-i", f"flite=text='{safe}':voice=slt", wav],
            check=True, timeout=120)
        if os.path.getsize(wav) > 1000:
            return wav, "flite-offline"
    except Exception as e:
        print(f"[voice] flite failed: {e}")

    # 4) Silent fallback — honest timing, no fake voice.
    print("[voice] all TTS failed — using silent audio "
          f"({seconds:.1f}s estimated). Video will have no voice.")
    return _silent_wav(wav, seconds), "silent-fallback"
