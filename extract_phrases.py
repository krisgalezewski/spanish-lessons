#!/usr/bin/env python3
"""
extract_phrases.py — scans the site's HTML files and builds phrases.json
automatically, so you never have to hand-maintain the phrase list.

It looks for every Spanish string the pages can actually speak:
  - data-text="..." attributes on <button class="say"> elements
  - {es: '...'} / {es: "..."} fields inside the pages' embedded vocab,
    dialogue, and exercise data

Run this again any time you add content to the pages, then run
generate_audio.py — it only generates files that don't exist yet, so
re-running is always safe and cheap.

USAGE:
    python extract_phrases.py
"""

import json
import re
import unicodedata
from pathlib import Path

HTML_FILES = ["spanish_kids.html", "spanish_adult.html"]
OUTPUT_FILE = "phrases.json"


def slugify(text: str) -> str:
    """Must produce the exact same result as slugify() in the HTML/JS."""
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[¿¡?!.,;:\"'()]", "", text)
    text = text.strip()
    text = re.sub(r"[\s/]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


DATA_TEXT_RE = re.compile(r'data-text="([^"]*)"')
ES_FIELD_RE = re.compile(r"""es\s*:\s*(['"])((?:(?!\1).)*)\1""")


def extract_from_file(path: Path):
    content = path.read_text(encoding="utf-8")
    found = set()
    for m in DATA_TEXT_RE.finditer(content):
        text = m.group(1).strip()
        # skip dynamic JS template-literal expressions like ${item.es} —
        # those are computed at runtime and can't be pre-generated
        if text and "${" not in text:
            found.add(text)
    for m in ES_FIELD_RE.finditer(content):
        text = m.group(2).strip()
        if text and "${" not in text:
            found.add(text)
    return found


def main():
    all_phrases = set()
    for filename in HTML_FILES:
        path = Path(filename)
        if not path.exists():
            print(f"(skipping {filename} — not found in this folder)")
            continue
        found = extract_from_file(path)
        print(f"{filename}: {len(found)} phrases")
        all_phrases |= found

    items = []
    seen_ids = {}
    for text in sorted(all_phrases):
        file_id = slugify(text)
        if not file_id:
            continue
        if file_id in seen_ids and seen_ids[file_id] != text:
            # Two different strings slugified to the same id (rare, e.g. differ
            # only by punctuation) — keep the first, keep both texts noted.
            print(f"WARNING: '{text}' collides with '{seen_ids[file_id]}' -> {file_id}")
            continue
        seen_ids[file_id] = text
        items.append({"file": file_id, "es": text})

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"\nWrote {len(items)} unique phrases to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
