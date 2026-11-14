# Woordkracht 1000

**A separate, vocabulary-only Dutch-learning project** — independent of `Orgo4ever/Dutchlearner`.

Woordkracht is a mobile-friendly, offline-capable web app designed to help build a **usable** 1,000-item Dutch vocabulary in roughly a month. Instead of accumulating passive recognition, it emphasizes **English → Dutch typed recall**: the skill needed when you want to say something and cannot find the word.

## What's included

- Exactly **1,000 original, hand-selected Dutch vocabulary entries** in `words.json`. Words are grouped by practical use, not claimed to be a scientific top-1,000 frequency ranking. The bank includes a few short, reusable word combinations alongside headwords.
- **Function-first sequence**: pronouns, connectors, prepositions, useful mini-phrases, everyday verbs, time/location words, descriptions, numbers, people, home, shopping, transport, work and everyday life.
- **Daily new-word goal**, default 35 (adjustable from 1–100).
- **Type to recall** Dutch words (including the noun article `de`/`het` where present); reveal and correct feedback.
- **Spaced review** based on self-rated difficulty, with increasing intervals after success.
- **Conservative mastery score**: a word becomes **verified** only when you correctly type it on **two different calendar days**. Merely revealing it or marking it “already know” never counts as verified.
- **Quick familiarity check:** mark known words 40 at a time without using your daily new-word allowance. Familiar items are staggered over the next 28 days for later confirmation.
- **Already know** on individual cards for fast baseline triage, which still appear for confirmation later.
- **My missing words**: add your own word/phrase when a real-life sentence gets stuck. Personal gap words move to the front of the *new-word* queue.
- **Search and browse** by Dutch, English, topic, and learning status.
- Browser-based Dutch pronunciation (depends on your device's installed voices).
- **Offline PWA** after initial load; no login, backend, paid APIs, or recurring service costs required for local use.
- **JSON progress backup and restore** across devices.

### Important data caveat

All progress lives in **localStorage in the browser where you study**. Clearing browser data, using a different browser/device, or a browser privacy mode can lose access to it. **Download a backup at least weekly** in Settings and restore the JSON on another device as needed. There is deliberately *no* cloud sync in v1.

### How learning is counted

- `Introduced`: you studied an item once, tried it or marked it familiar. This is not proof of mastery.
- `Verified recall`: you typed the correct Dutch headword (including an article if shown) on at least two separate days.
- `Due for review`: the item's next scheduled recall date is today or earlier.
- A mistake marked **Again** returns to your queue (same day). **Got it** or **Easy** only appears for a correctly typed response, not after revealing the answer.

## Run locally

1. Download and unzip the project directory.
2. Open a terminal inside the directory and run:

   ```sh
   python -m http.server 8000
   ```

3. Open `http://localhost:8000` in your browser. (Do **not** double-click `index.html`: browsers generally block loading `words.json` from `file://`.)
4. On a phone, use a deployed HTTPS site and optionally choose “Add to Home Screen.”

Only a recent browser is needed. Python is only used for the optional local web server; no Python packages are required for the app.

## Publishing the app

You can create a **new GitHub repository** (e.g., `woordkracht-1000`) and upload the contents of this folder to the root of its default branch. Enable **GitHub Pages** under repository Settings → Pages, choosing deployment from the branch and the root folder. GitHub Pages serves static assets and can make the app installable on your phone over HTTPS. The repository content should contain **only these source files, not a downloaded progress backup**. Check GitHub Pages availability for your repository's visibility/plan; public repositories are the simplest path.

Alternative: deploy the static folder to any static HTTPS host.

## Files

| File | Purpose |
| --- | --- |
| `index.html` | App layout and navigation |
| `styles.css` | Mobile-first design |
| `app.js` | Learning/review logic and progress storage |
| `words.json` | 1,000 core vocabulary entries |
| `words.csv` | Readable/editable CSV export of the entire vocabulary bank |
| `anki_import.tsv` | Optional English → Dutch import file for Anki, including tags |
| `seed_words.py` | Regenerates JSON and Anki exports from the editable `words.csv` source |
| `manifest.webmanifest`, `icon.svg`, `sw.js` | Installable/offline web app |
| `PLAN.md` | 30-day study program and goals |
| `test_vocab.py`, `test_logic.js` | Dataset and scheduling checks |

To regenerate the JSON and Anki exports after editing `words.csv`:

```sh
python seed_words.py
python test_vocab.py
node test_logic.js
```

## Source notes and evidence

The word bank was manually authored and organized for this project. **It does not reproduce** someone else's complete proprietary or open-source word list. It is *not* a validated corpus-frequency list or an officially certified CEFR dataset. A few English glosses simplify polysemous Dutch words; use an authoritative dictionary for full nuance. Since this is a learner project, improve and correct individual entries as needed.

Helpful background sources used for study-method decisions, **not copied into the dataset**:

- [NT2Lex CEFR-graded Dutch lexical research](https://cental.uclouvain.be/cefrlex/nt2lex/) — frequency and CEFR can inform later ranking (noncommercial dataset has its own license).
- [Meta-analysis: spaced practice in second language learning](https://onlinelibrary.wiley.com/doi/full/10.1111/lang.12479)
- [Meta-analysis: intentional vocabulary-learning activities](https://onlinelibrary.wiley.com/doi/10.1111/modl.12671)

## Next improvements worth prioritizing

1. **Richer placement testing**: make the existing familiarity check more diagnostic with short recall tests.
2. **Word families / conjugation cues**: e.g. `gaan → ga, gaat, ging`, because active sentences also require forms.
3. **Better example phrases** on more cards, especially confusing high-frequency function words.
4. **Flexible accepted answers and manual corrections** for common synonyms without creating false positives.
5. Optional private sync for studying on both desktop and mobile (requires an authentication/storage design before enabling).

### Privacy

The app makes no accounts and sends no vocabulary progress to any server. The only network requests it makes are for its own static files when first installed or refreshed. Dutch pronunciation uses the speech synthesis feature of the browser/device, where available.