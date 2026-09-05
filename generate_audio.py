#!/usr/bin/env python3
"""
generate_audio.py — generates MP3 files from Google Cloud Text-to-Speech
for the Spanish site, using the same pattern as the Rozmówki Przedszkolne
project (standard library only, no pip install needed).

USAGE:
    python generate_audio.py YOUR_API_KEY
    (or set the GOOGLE_TTS_API_KEY environment variable instead)

Reads phrases.json (built by extract_phrases.py) in this same folder, e.g.:
[
  {"file": "hola", "es": "Hola"},
  {"file": "buenos-dias", "es": "Buenos días"}
]

Writes audio/es/<file>.mp3 for each entry, skipping any file that already
exists — so re-running after adding new content only fills in the gaps.
Put the resulting "audio" folder next to index.html, spanish_kids.html and
spanish_adult.html in your GitHub Pages repo; every 🔊 button on both pages
will then play the real recording automatically, falling back to the phone's
own voice only if a file is ever missing.
"""

import json
import os
import sys
import time
import base64
import urllib.request
import urllib.error

API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

# Full voice list: https://cloud.google.com/text-to-speech/docs/voices
# es-ES-Neural2-* voices sound noticeably more natural than the Wavenet ones
# if your Cloud project has Neural2 enabled — try swapping the name below.
VOICES = {
    "es": {"languageCode": "es-ES", "name": "es-ES-Wavenet-C"},  # female, European Spanish
}

SPEAKING_RATE = 0.92
PITCH = 1.0
OUTPUT_DIR = "audio"
MANIFEST_FILE = "phrases.json"
LANG = "es"


def synthesize(api_key, text):
    voice = VOICES[LANG]
    payload = {
        "input": {"text": text},
        "voice": voice,
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": SPEAKING_RATE, "pitch": PITCH},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}?key={api_key}", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return base64.b64decode(body["audioContent"])


def main():
    api_key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GOOGLE_TTS_API_KEY")
    if not api_key:
        print("ERROR: pass your API key as an argument, or set GOOGLE_TTS_API_KEY.")
        sys.exit(1)
    if not os.path.exists(MANIFEST_FILE):
        print(f"ERROR: {MANIFEST_FILE} not found — run extract_phrases.py first.")
        sys.exit(1)

    with open(MANIFEST_FILE, encoding="utf-8") as f:
        items = json.load(f)

    out_dir = os.path.join(OUTPUT_DIR, LANG)
    os.makedirs(out_dir, exist_ok=True)

    total = len(items)
    done, failed, skipped = 0, [], 0

    for item in items:
        out_path = os.path.join(out_dir, f"{item['file']}.mp3")
        done += 1
        if os.path.exists(out_path):
            skipped += 1
            continue
        try:
            audio_bytes = synthesize(api_key, item["es"])
            with open(out_path, "wb") as f:
                f.write(audio_bytes)
            print(f"[{done}/{total}] OK   {item['file']}.mp3")
        except Exception as e:
            print(f"[{done}/{total}] FAIL {item['file']}: {e}")
            failed.append(item["file"])
        time.sleep(0.05)

    print("\n---- SUMMARY ----")
    print(f"Generated: {total - len(failed) - skipped} new, {skipped} already existed, {len(failed)} failed")
    if failed:
        print(f"Failed: {', '.join(failed)} — run the script again to retry just these.")
    else:
        print("All audio generated successfully! 🎉")


if __name__ == "__main__":
    main()
