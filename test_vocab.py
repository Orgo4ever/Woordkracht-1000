"""Basic lexical data and project integrity tests (standard library only)."""
import json
import re
from pathlib import Path
from collections import Counter

root = Path(__file__).parent
words = json.loads((root / 'words.json').read_text(encoding='utf-8'))
assert len(words) == 1000, f"Expected 1000 entries, got {len(words)}"
assert [w['id'] for w in words] == [f'w{i:04d}' for i in range(1, 1001)]
assert len({w['nl'].casefold() for w in words}) == 1000
for word in words:
    assert all(word.get(field) is not None for field in ['nl','en','category','example_nl','example_en'])
    assert word['nl'].strip() and word['en'].strip()
    assert word['rank'] == int(word['id'][1:])
    assert not re.search(r'\s{2,}', word['nl'])
assert len({w['category'] for w in words}) >= 10
for term in ['omdat','want','als','niet','geen','te','wel','niemand','niets','alles','meer','minder',
             'de','het','een','zijn','hebben','moeten','kunnen','willen','doen','maken','gaan',
             'begrijpen','vragen','antwoorden','eigenlijk','toch','de trein','de gemeente',
             'de supermarkt','de functie','het contract','ik ben','de suiker']:
    assert term in {w['nl'] for w in words}, term
for file in ['index.html','styles.css','app.js','manifest.webmanifest','sw.js','icon.svg','README.md','PLAN.md']:
    assert (root / file).exists(), f'Missing {file}'
print('PASS: 1000 unique and complete Dutch vocabulary entries, critical terms, app assets')
print('Categories:', dict(Counter(w['category'] for w in words)))
