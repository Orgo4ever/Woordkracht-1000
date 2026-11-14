"""Regenerate words.json and anki_import.tsv from editable words.csv.
Usage: python seed_words.py
The hand-curated vocabulary source is words.csv. Python standard library only.
"""
import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parent
source = root / 'words.csv'
with source.open('r', encoding='utf-8-sig', newline='') as f:
    words = list(csv.DictReader(f))
assert len(words) == 1000, f"Expected 1000 core entries, got {len(words)}"
assert len({row['id'] for row in words}) == 1000, "Duplicate IDs"
assert len({row['nl'].casefold() for row in words}) == 1000, "Duplicate Dutch terms"
payload = [
    {
        'id': row['id'],
        'nl': row['nl'],
        'en': row['en'],
        'category': row['category'],
        'rank': int(row['rank']),
        'example_nl': row['example_nl'],
        'example_en': row['example_en'],
    }
    for row in words
]
(root / 'words.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
with (root / 'anki_import.tsv').open('w', encoding='utf-8', newline='') as f:
    f.write('#separator:Tab\n#html:false\n#columns:Front\tBack\tTags\n')
    for w in payload:
        tag = w['category'].lower().replace(' ', '_')
        f.write(f"{w['en']}\t{w['nl']}\t{tag}\n")
print(f"Regenerated {len(payload)} vocabulary items from words.csv")
