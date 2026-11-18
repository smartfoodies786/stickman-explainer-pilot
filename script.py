"""Script generation: Groq (gpt-oss-20b) when GROQ_API_KEY is set, else a
built-in template so the demo works offline with no key at all.

A script is: {"question": str, "scenes": [{"narration": str,
"action": str, "caption": str}, ...]} — 5 scenes, ~25-35s total.
"""
import json
import os

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "gpt-oss-20b"

# Built-in fallback, written for the demo question. For any other
# question the template is adapted: the same 5 beats, question in scene 1.
FALLBACK_SCENES = [
    {"narration": "What did ancient humans actually do all day? "
                  "No phones, no jobs, no alarms. Just survival.",
     "action": "wake", "caption": "No phones. No jobs. Just survival."},
    {"narration": "First, they hunted. A small group, wooden spears, "
                  "hours of walking just to find one meal.",
     "action": "hunt", "caption": "Hunting took hours — for one meal."},
    {"narration": "Then they gathered. Berries, roots, and nuts — "
                  "food the whole family could share.",
     "action": "gather", "caption": "Gathering fed the whole family."},
    {"narration": "At night, fire was everything. Warmth, light, "
                  "protection — and the first stories ever told.",
     "action": "fire", "caption": "Fire was warmth, light, and stories."},
    {"narration": "Then they slept, early, under the stars. And the "
                  "next morning, it all started again.",
     "action": "sleep", "caption": "Sleep early. Repeat tomorrow."},
]

SYSTEM_PROMPT = (
    "You write 30-second stickman explainer videos. Return ONLY valid JSON, "
    "no markdown, no extra text: "
    '{"scenes": [{"narration": "...", "action": "...", "caption": "..."}]} '
    "Exactly 5 scenes. Each narration is 1-2 short sentences, 12-20 words. "
    "Each caption is under 8 words. Action is one word from: "
    "wake, hunt, gather, fire, sleep, walk, talk, cook, build, think."
)


def _groq_script(question: str):
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return None, "no GROQ_API_KEY set"
    try:
        r = requests.post(GROQ_URL, timeout=60, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"},
            json={"model": MODEL, "temperature": 0.7, "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}"}]})
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        text = text.strip("`").removeprefix("json").strip()
        data = json.loads(text)
        scenes = data["scenes"]
        assert isinstance(scenes, list) and len(scenes) == 5
        for s in scenes:
            assert s["narration"] and s["caption"] and s["action"]
        return {"question": question, "scenes": scenes}, "groq"
    except Exception as e:  # network, bad key, bad JSON -> fallback
        return None, f"groq failed ({type(e).__name__}: {e})"


def get_script(question: str):
    """Return (script, source). Source is 'groq' or 'fallback-template'."""
    script, why = _groq_script(question)
    if script:
        return script, "groq"
    print(f"[script] Groq unavailable: {why} — using built-in template.")
    scenes = [dict(s) for s in FALLBACK_SCENES]
    if "ancient human" not in question.lower():
        scenes[0]["narration"] = (
            f"{question} Let's find out — the simple way, in 30 seconds.")
        scenes[0]["caption"] = question
    return {"question": question, "scenes": scenes}, "fallback-template"
