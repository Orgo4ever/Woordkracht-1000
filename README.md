# Woordkracht 1000

**A separate, vocabulary-only Dutch-learning project** — independent of `Orgo4ever/Dutchlearner`.

Woordkracht is a mobile-friendly, offline-capable web app designed to help build a **usable** 1,000-item Dutch vocabulary in roughly a month. Instead of accumulating passive recognition, it emphasizes **English → Dutch typed recall**: the skill needed when you want to say something and cannot find the word.

## A2+ focus (default)

**Beginner vocabulary is hidden by default.** The manually reviewed `a1-words.json` currently excludes 552 introductory items from learning, review, familiarity checks and progress calculations. The original 1,000-entry bank remains intact and the default active pool is 448 A2+ candidates. These labels are practical **estimates**, not official CEFR certifications; a word's difficulty depends on its meaning and use. You can include A1 again in Settings and skip additional words via **Too easy · skip**. Skipping does not delete saved progress; restore skipped entries from Settings. Custom missing words are always included by default.

**The target remains 1,000 useful words beyond A1**, but the current bank needs additional A2/B1 entries to reach that target. Do not interpret the 448 active entries as 1,000 advanced words.

## New: Streamlit flashcard application (November 2026)

The repository offers **two independent interfaces** that use the same word bank:

- **Existing GitHub Pages**: `index.html` and `app.js` (still live, offline capable, unchanged).
- **Streamlit flashcards**: `streamlit_app.py`, `vocab_core.py`, and `requirements.txt` (an online Python-powered app; deploy separately on Streamlit Community Cloud).

### Flashcard-first features

- **Flip cards**: English → Dutch, reveal, browser pronunciation, bilingual example when available, then rate **Again / Hard / Good / Easy**.
- **Typed recall**: type the Dutch word (with `de` or `het` where applicable), check without revealing, and receive stricter mastery credit.
- **Review queue**: due words first, with intervals based on ratings; daily new-word target defaults to 35.
- **Free Practice / Vrij oefenen**: create a repeatable deck of any size from previously encountered, difficult (last rated Again/Hard), or all eligible words; move backward/forward, flip cards, restart, and shuffle. Next wraps to the beginning instead of ending.
- **A1 filter**: excludes the same 552 estimated A1 entries by default, leaving 448 active A2+ candidates. You can turn them on in Settings.
- **Placement / library**: familiar-word checklist, search and filter, skip easy words, and add words you needed in conversation.
- **Dashboard**: seven-day study activity, topic coverage, introduced and verified counts.
- **Progress import/export**: reads the exact same version-1 JSON backup format as GitHub Pages. Use Pages → Settings → Download progress backup, then import in the Streamlit app.

**Mastery distinction:** rating a flashcard Good/Easy schedules spaced review but does *not* claim verified production. A word becomes **Verified** only after two correct **typed** English→Dutch recalls on different dates. This rule is shared with the original app.

### Free Practice (independent of spaced repetition)

Open the **Practice** tab in Streamlit. Choose a vocabulary source and deck size, then click **Build a new practice deck**. The deck can be repeated indefinitely; **Next** wraps after the last card, **Previous** revisits earlier cards, **Shuffle deck** rearranges the *same* selected words, and **Restart deck** starts from the first card in the current order.

- **Previously encountered** includes any active word already recorded in your progress, even if its next review is days away.
- **Difficult words** includes words last rated Again or Hard in the regular Study/Review sessions.
- **All eligible words** includes the entire currently visible vocabulary pool, respecting your A1 setting and personally skipped words. Custom words are included when eligible.
- Free Practice is intentionally **ungraded** and **does not change** your next due dates, daily word allowance, mastery status, progress records, or saved backup format.
- The selected deck survives tab changes in the active Streamlit session, but it is not included in the browser progress backup and can reset on a full app reload. Build a fresh deck whenever needed.

### Deploy on Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub** (the wording may vary).
3. Set repository to `Orgo4ever/Woordkracht-1000`, branch to `main`, and main-file path to `streamlit_app.py`.
4. Deploy. `requirements.txt` at the repository root installs the dependencies. Do **not** replace or remove the GitHub Pages deployment.

For local development:

```sh
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
python -m unittest discover -v
```

### Continuation fix (November 14, 2026)

The Streamlit app now uses an explicit browser-storage bridge in `browser_progress.py` rather than assuming the older asynchronous storage component has finished loading. It:

- **Reads and validates** any existing saved profile before offering to create a new one.
- **Waits for a confirmed save** after each flashcard rating, word skip, settings update, and backup import before advancing.
- Keeps the `woordkracht-streamlit-v1` storage key and understands raw and double-encoded legacy JSON.
- Offers **Try recovering progress from the previous Streamlit version** when an older browser component may have saved data under a different origin.
- Preserves the existing backup format and keeps the GitHub Pages app unchanged.

**Important limits:** browser storage is specific to a domain, browser, and device. This fix prevents the same browser from restarting a profile, but **does not sync** a phone with a desktop. Use Settings → Download JSON backup and restore it on another device. If browser storage is blocked, an emergency backup option appears. Do not clear site data before confirming your previous progress is safely backed up.

To test: rate a flashcard and wait until the next card is shown, close/reopen the same browser, and confirm **Introduced** and **Due** counts are retained. Repeat after another rating. Run `python test_streamlit_core.py` and `python test_browser_progress.py` for study/recovery regression tests.

### Progress reliability and privacy

The Streamlit app uses a browser-local-storage component where supported, with **JSON backup and restore** as a portable fallback. **Streamlit Session State is not durable**: it is lost on reload/reconnection if browser storage does not restore the profile. Browser storage may be cleared and does not automatically sync across domains, devices, or browsers. Download backups regularly and import your existing Pages backup once. **Do not commit personal backup JSON files to this public repository.** No login or cloud database is configured.

**Testing:** `vocab_core.py` has nine standard-library regression tests that cover flashcard scheduling, typed-only verified mastery, the A1 filter, skipping/adding words, familiar-word placement, and compatibility with the existing Pages backup. The Streamlit UI still needs a browser smoke test after deployment; dependencies couldn't be installed in the build environment used to author this update.

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

All progress lives in **localStorage in the browser where you study**. Updating the app or switching the A1 filter does not intentionally reset progress. Clearing browser data, using a different browser/device, or a browser privacy mode can lose access to it. **Download a backup at least weekly** in Settings and restore the JSON on another device as needed. There is deliberately *no* cloud sync in v1.

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
| `a1-words.json` | Editable estimated A1 exclusions (default A2+ focus) |
| `words.csv` | Readable/editable CSV export of the entire vocabulary bank |
| `anki_import.tsv` | Optional English → Dutch import file for Anki, including tags |
| `seed_words.py` | Editable, independently authored word-bank source and reproducible generator |
| `manifest.webmanifest`, `icon.svg`, `sw.js` | Installable/offline web app |
| `PLAN.md` | 30-day study program and goals |
| `test_vocab.py`, `test_logic.js` | Dataset and scheduling checks |

To regenerate the data file after editing `seed_words.py`:

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

1. **Quick-placement test**: mark familiar items in batches and test them rather than spending days relearning basics.
2. **Word families / conjugation cues**: e.g. `gaan → ga, gaat, ging`, because active sentences also require forms.
3. **Better example phrases** on more cards, especially confusing high-frequency function words.
4. **Flexible accepted answers and manual corrections** for common synonyms without creating false positives.
5. Optional private sync for studying on both desktop and mobile (requires an authentication/storage design before enabling).

### Privacy

The **GitHub Pages** app makes no accounts and stores its progress in local browser storage. The **Streamlit** app sends interaction data to its Streamlit server during normal use and attempts to save progress in browser storage using a third-party component. Neither frontend has a private cloud-sync database. Avoid putting progress backups into the public GitHub repository. Dutch pronunciation uses the browser/device speech-synthesis feature where available.