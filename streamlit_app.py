"""Woordkracht 1000 • Streamlit flashcards and active vocabulary practice.

Deploy this file directly from the existing Woordkracht-1000 GitHub repository.
Vocabulary and legacy GitHub Pages progress backups remain compatible.
"""
from __future__ import annotations

from datetime import date, timedelta
from html import escape
import json
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from browser_progress import browser_storage, decode_browser_value

from vocab_core import (
    add_custom_word, all_words, counts, due_words, fresh_progress, json_backup,
    load_bank, load_progress, mark_familiar_batch, mark_known, new_words,
    next_word, normalize, plus_days, rate, session, skip, status,
    today, verified, visible_words,
)

st.set_page_config(page_title="Woordkracht 1000 | Dutch vocabulary", page_icon="🇳🇱", layout="centered", initial_sidebar_state="collapsed")

ROOT = Path(__file__).resolve().parent

st.markdown('''
<style>
  :root { --forest:#163d2d; --muted:#5f7266; --mint:#def0e3; --cream:#f7f7f1; }
  .block-container{ max-width:900px; padding-top:1.4rem; padding-bottom:5rem; }
  h1,h2,h3 {letter-spacing:-.035em;}
  .brand-panel{background:#173b2c; border-radius:24px; padding:25px 27px; margin:0 0 18px; color:white}
  .brand-panel .eyebrow{color:#bbdfbf; font-size:12px; font-weight:800; letter-spacing:.16em}
  .brand-panel h1{font-size:2.1rem; margin:.38rem 0 .45rem; color:white}
  .brand-panel p{color:#deeadf; margin:0}
  .study-face{border:2px solid #dae8d9; background:linear-gradient(145deg,#fbfaf4,#f3f8f1); min-height:210px; border-radius:23px; padding:30px 19px; text-align:center; margin:14px 0 12px; display:flex; flex-direction:column; justify-content:center;}
  .study-face .prompt{font-size:11px; font-weight:800; letter-spacing:.15em; color:#5b7a69; text-transform:uppercase}
  .study-face .word{font-size:clamp(30px, 5vw, 48px); font-weight:850; letter-spacing:-.055em; margin:12px 0; color:#183a2b; line-height:1.18}
  .study-face .sub{font-size:14px; color:#617469}
  .study-face .example{font-size:16px; color:#2c5944; margin-top:12px}
  .study-face .translation{font-size:13px; color:#62746b; margin-top:5px}
  .pill{display:inline-block; border:1px solid #c9ddce; border-radius:25px; color:#365a45; background:#edf6ee; font-weight:700; padding:5px 11px; font-size:12px; margin-right:6px;}
  .tiny{color:#607367;font-size:13px;}
  div.stButton>button {border-radius:12px; min-height:45px;}
  div[data-testid='stMetric'] {border:1px solid #dfe9df; border-radius:15px; padding:13px; background:#fff;}
  div[data-testid='stHorizontalBlock'] {gap:.55rem;}
  @media (max-width:640px) {.block-container{padding-left:1rem;padding-right:1rem}.brand-panel h1{font-size:1.65rem}.study-face{min-height:185px;padding:20px 12px} }
</style>
''', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def cached_bank() -> tuple[list[dict], set[str]]:
    return load_bank(ROOT)


WORDS, A1 = cached_bank()


def push_update() -> None:
    """Mark in-session changes for a durable browser write before next card."""
    st.session_state.save_revision = f"{st.session_state.profile_session}:{st.session_state.get('save_count', 0) + 1}"
    st.session_state.save_count = st.session_state.get("save_count", 0) + 1
    st.rerun()


def init_progress() -> None:
    """Restore first; never replace a pending browser read with a blank profile."""
    st.session_state.setdefault("profile_session", uuid4().hex)
    if "progress" in st.session_state:
        if st.session_state.get("storage_unavailable"):
            browser_storage(action="idle")
            return
        pending = st.session_state.get("save_revision")
        if pending is None:
            browser_storage(action="idle")
            return
        result = browser_storage(action="write", value=json_backup(st.session_state.progress), revision=pending)
        ack = getattr(result, "ack", None)
        if ack == f"ok:{pending}":
            st.session_state.saved_revision = pending
            st.session_state.save_revision = None
            return
        if isinstance(ack, str) and ack.startswith(f"error:{pending}:"):
            st.error("This browser blocked saving your study history. Your current session is still available.")
            st.download_button("Download an emergency JSON backup", json_backup(st.session_state.progress),
                               file_name=f"woordkracht-backup-{today()}.json", mime="application/json")
            if st.button("Continue without autosave (not recommended)"):
                st.session_state.save_revision = None
                st.session_state.storage_unavailable = True
                st.rerun()
        else:
            st.info("Saving your progress to this browser…")
        st.stop()

    result = browser_storage(action="read")
    response = getattr(result, "loaded", None)
    if not isinstance(response, str):
        st.info("Restoring your vocabulary progress from this browser…")
        st.stop()
    try:
        data = json.loads(response)
    except (ValueError, TypeError):
        data = {"ok": False, "error": "The browser returned an unreadable storage response."}

    if data.get("ok") and data.get("present"):
        try:
            st.session_state.progress = decode_browser_value(data["raw"])
            st.session_state.loaded_from_browser = True
            st.rerun()
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            st.error(f"Existing study data was found but could not be restored: {exc}")
            st.warning("Do not start a new profile until you have recovered or backed up your data.")
            st.download_button("Download the raw stored data for recovery", data["raw"],
                               file_name="woordkracht-raw-recovery.txt", mime="text/plain")
    elif not data.get("ok"):
        st.error(f"Browser storage is unavailable: {data.get('error', 'unknown error')}")
        st.warning("Your history will not survive closing the page without a downloaded backup.")
    else:
        st.info("No previous Woordkracht Streamlit profile was found in this browser. You can create one or import a backup.")

    st.markdown('<div class="brand-panel"><div class="eyebrow">WOORDKRACHT · STREAMLIT</div><h1>Continue learning Dutch.</h1><p>Your learning progress belongs to your browser, not a temporary Streamlit session.</p></div>', unsafe_allow_html=True)
    if data.get("ok") and not data.get("present"):
        if st.button("Start a new profile", type="primary", use_container_width=True):
            st.session_state.progress = fresh_progress()
            st.session_state.loaded_from_browser = False
            push_update()
        if st.button("Try recovering progress from the previous Streamlit version", use_container_width=True):
            st.session_state.try_legacy_recovery = True
            st.rerun()
        if st.session_state.get("try_legacy_recovery"):
            try:
                from streamlit_local_storage import LocalStorage
                old_saved = LocalStorage().getItem("woordkracht-streamlit-v1", key="woordkracht_old_progress_recovery")
                if old_saved is not None:
                    st.session_state.progress = decode_browser_value(old_saved) if isinstance(old_saved, str) else load_progress(old_saved)
                    st.session_state.try_legacy_recovery = False
                    st.success("Recovered a profile from the old Streamlit storage component!")
                    push_update()
                st.info("Checking the old storage location. If nothing appears, use your JSON backup instead.")
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                st.warning(f"The older saved profile could not be decoded: {exc}")
            except Exception as exc:
                st.warning(f"The old storage component was unavailable: {exc}")
    st.link_button("Open original GitHub Pages app", "https://orgo4ever.github.io/Woordkracht-1000/", use_container_width=True)
    uploaded = st.file_uploader("Restore a previously downloaded Woordkracht progress backup (.json)", type=["json"], key="initial_backup")
    if uploaded and st.button("Import this backup", use_container_width=True):
        try:
            st.session_state.progress = load_progress(uploaded.getvalue())
            st.session_state.loaded_from_browser = False
            push_update()
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            st.error(str(exc))
    st.caption("Browser storage is specific to each site, browser and device. Restoring a JSON backup also migrates progress from the original GitHub Pages app.")
    st.stop()


init_progress()
p = st.session_state.progress


def pool() -> list[dict]:
    return visible_words(WORDS, A1, p)


def draw_stats() -> None:
    c = counts(pool(), p)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verified", c["verified"])
    c2.metric("Introduced", c["introduced"])
    c3.metric("Due", c["due"])
    c4.metric("Active words", c["total"])


def tts(dutch: str) -> None:
    """Dutch speech with the browser's installed speech synthesis voice."""
    text = dutch.split(" ", 1)[1] if dutch.startswith(("de ", "het ")) else dutch
    js_str = json.dumps(text, ensure_ascii=False).replace("<", "\\u003c")
    components.html(f'''
    <button id="listen" style="font-family:system-ui,sans-serif;cursor:pointer;padding:9px 17px;background:#e4f1e5;color:#1a4631;border:1px solid #d4e2d7;border-radius:13px;font-weight:750">🔊 Hear Dutch pronunciation</button>
    <script>
    document.getElementById('listen').addEventListener('click', function() {{
      if (!('speechSynthesis' in window)) {{ this.textContent='Speech unavailable in this browser'; return; }}
      speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance({js_str});
      utterance.lang = 'nl-NL'; utterance.rate = 0.86;
      speechSynthesis.speak(utterance);
    }});
    </script>''', height=53)


def face(word: dict, revealed: bool, mode: str) -> None:
    front = escape(word["en"])
    dutch = escape(word["nl"])
    if not revealed:
        st.markdown(f'<div class="study-face"><div class="prompt">TRANSLATE THIS INTO DUTCH</div><div class="word">{front}</div><div class="sub">Think of the Dutch word, then flip.</div></div>', unsafe_allow_html=True)
    else:
        ex_nl = escape(word.get("example_nl", ""))
        ex_en = escape(word.get("example_en", ""))
        example = f'<div class="example">{ex_nl}</div><div class="translation">{ex_en}</div>' if ex_nl else ""
        st.markdown(f'<div class="study-face"><div class="prompt">DUTCH ANSWER</div><div class="word">{dutch}</div><div class="sub">{front}</div>{example}</div>', unsafe_allow_html=True)
        tts(word["nl"])


def clear_card() -> None:
    st.session_state.active_word = None
    st.session_state.revealed = False
    st.session_state.result = None


def pick_active(review_only: bool) -> dict | None:
    selected = st.session_state.get("active_word")
    candidates = {w["id"]: w for w in pool()}
    if selected in candidates:
        return candidates[selected]
    w = next_word(pool(), p, review_only=review_only,
                  avoid=tuple(st.session_state.get("recent_ids", [])))
    st.session_state.active_word = w["id"] if w else None
    st.session_state.revealed = False
    st.session_state.result = None
    return w


def complete(word: dict, rating: str, mode: str, correct: bool = False) -> None:
    rate(p, word["id"], rating, mode=mode, typed_correct=correct)
    recent = st.session_state.get("recent_ids", [])
    recent.append(word["id"])
    st.session_state.recent_ids = recent[-12:]
    clear_card()
    push_update()


def rating_bar(word: dict, mode: str, correct: bool = False) -> None:
    cols = st.columns(4)
    options = [("↻ Again", "again"), ("● Hard", "hard"), ("✓ Good", "good"), ("★ Easy", "easy")]
    for col, (label, value) in zip(cols, options):
        if col.button(label, key=f"rate_{mode}_{value}_{word['id']}", use_container_width=True,
                      disabled=(mode == "typed" and not correct and value != "again")):
            complete(word, value, mode, correct)
    if mode == "flash":
        st.caption("Flashcard ratings schedule future review. Only correct **typed recall on two different days** earns 'Verified' status.")
    else:
        st.caption("Typed answers must be correct to earn verified recall credit. Wrong or revealed answers count as practice, not mastery.")


def study(review_only: bool = False) -> None:
    c = counts(pool(), p)
    st.progress(min(1.0, c["today_new"] / max(1, c["goal"])), text=f"Today: {c['today_new']} / {c['goal']} new words")
    st.caption("Due reviews come first · A1 words excluded by default · Add your own missing words in Library")
    mode = st.radio("Practice mode", ["🃏 Flashcards", "⌨️ Type the answer"], horizontal=True, key="mode")
    mode_id = "flash" if mode.startswith("🃏") else "typed"
    context = ("review" if review_only else "study", mode_id)
    if st.session_state.get("last_study_context") != context:
        st.session_state.last_study_context = context
        clear_card()

    target = st.session_state.pop('_target_word', None)
    if target and target in {w['id'] for w in pool()}:
        st.session_state.active_word = target
        st.session_state.revealed = False
        st.session_state.result = None
    word = pick_active(review_only)
    if word is None:
        st.success("You're caught up on reviews!" if review_only else "No more words for this session.")
        if c["new"] and c["today_new"] >= c["goal"] and not review_only:
            st.info("You've reached today's new-word goal. Increase it in Settings if you'd like to continue.")
        return
    record = p["cards"].get(word["id"])
    st.markdown(f'<span class="pill">{escape(word.get("category", ""))}</span><span class="pill">{"Due for review" if record else "New word"}</span>', unsafe_allow_html=True)

    if mode_id == "flash":
        face(word, bool(st.session_state.get("revealed")), mode_id)
        if not st.session_state.get("revealed"):
            if st.button("Flip card · Show Dutch", type="primary", use_container_width=True):
                st.session_state.revealed = True
                st.rerun()
        else:
            rating_bar(word, "flash")
    else:
        result = st.session_state.get("result")
        if result and result.get("id") == word["id"]:
            face(word, True, "typed")
            if result["correct"]:
                st.success("Correct — you recalled the Dutch word without revealing it.")
            elif result["revealed"]:
                st.info("Answer revealed. Rate Again to schedule another try.")
            else:
                st.warning(f"Your answer: {result['answer']!r}. Take another look and choose Again.")
            rating_bar(word, "typed", result["correct"])
        else:
            face(word, False, "typed")
            with st.form(f"typed_{word['id']}", clear_on_submit=False):
                answer = st.text_input("Type the Dutch word", placeholder="Include de / het when shown", max_chars=120, key=f"text_{word['id']}")
                submitted = st.form_submit_button("Check my answer", type="primary", use_container_width=True)
            if submitted:
                st.session_state.result = {"id": word["id"], "correct": normalize(answer) == normalize(word["nl"]), "revealed": False, "answer": answer}
                st.rerun()
            if st.button("Reveal answer instead", use_container_width=True):
                st.session_state.result = {"id": word["id"], "correct": False, "revealed": True, "answer": ""}
                st.rerun()

    # The skip controls are available in both practice modes.
    c1, c2 = st.columns(2)
    if c1.button("Too easy · remove from study", use_container_width=True):
        skip(p, word["id"])
        clear_card()
        push_update()
    if not record and c2.button("Already know → verify later", use_container_width=True):
        mark_known(p, word["id"])
        clear_card()
        push_update()


def familiarity() -> None:
    st.subheader("Quick familiarity check")
    st.write("Mark the words you already recognize. This doesn't count as typed mastery; they'll be queued for later review.")
    base_pool = [w for w in pool() if w.get("category") != "My missing words"]
    pages = max(1, (len(base_pool) + 39) // 40)
    current = int(p["settings"].get("placementPage", 0)) % pages
    chunk = base_pool[current*40:(current+1)*40]
    st.caption(f"Set {current+1} / {pages} · {len(chunk)} words")
    with st.form(f"familiar_set_{current}"):
        chosen = []
        for w in chunk:
            already = w["id"] in p["cards"]
            if st.checkbox(f"{w['nl']} — {w['en']}", value=already, disabled=already, key=f"known_{current}_{w['id']}") and not already:
                chosen.append(w["id"])
        submitted = st.form_submit_button("Save known words and next set →", type="primary", use_container_width=True)
    if submitted:
        mark_familiar_batch(p, chosen)
        p["settings"]["placementPage"] = (current + 1) % pages
        st.toast(f"Marked {len(chosen)} familiar words for later review")
        push_update()


def library() -> None:
    st.subheader("Find the words you're missing")
    wlist = pool()
    col1, col2 = st.columns(2)
    search = col1.text_input("Search English or Dutch", placeholder="for example: although")
    cat = col2.selectbox("Category", ["All"] + sorted(set(w["category"] for w in wlist)))
    filt = st.selectbox("Learning status", ["All", "New", "Learning", "Due", "Verified"])
    matches = [w for w in wlist if (cat == "All" or w["category"] == cat)
               and (filt == "All" or status(w, p) == filt)
               and (not search or normalize(search) in normalize(f"{w['nl']} {w['en']}"))]
    st.caption(f"{len(matches)} results")
    if matches:
        page_size = 20
        num_pages = (len(matches) + page_size - 1) // page_size
        offset = st.number_input("Result page", min_value=1, max_value=max(1, num_pages), value=1)
        for w in matches[(offset-1)*page_size:offset*page_size]:
            a, b = st.columns([4, 1])
            a.markdown(f"**{w['nl']}** · {w['en']}  \n:gray[{w['category']} · {status(w, p)}]")
            if b.button("Study", key=f"browse_{w['id']}", use_container_width=True):
                st.session_state._target_word = w["id"]
                st.session_state._navigate_to = "Study"
                push_update()
    else:
        st.info("No matching vocabulary entries.")
    st.divider()
    st.subheader("Add a word from real life")
    st.caption("When you can't finish a sentence, write down the missing word. Your words go to the front of the new-word queue.")
    with st.form("add_custom", clear_on_submit=True):
        english = st.text_input("English meaning", max_chars=120)
        dutch = st.text_input("Dutch word or phrase", max_chars=120)
        example = st.text_input("Dutch example (optional)", max_chars=180)
        submitted = st.form_submit_button("+ Add to my word bank", type="primary")
    if submitted:
        try:
            word = add_custom_word(p, WORDS, english, dutch, example)
            st.toast(f"Added {word['nl']}!")
            push_update()
        except ValueError as exc:
            st.error(str(exc))


def dashboard() -> None:
    st.subheader("Your progress")
    draw_stats()
    active = pool()
    c = counts(active, p)
    st.progress(c["verified"] / max(1, c["total"]), text=f"{c['verified']} verified out of {c['total']} active words")
    st.caption("'Verified' requires successful typed Dutch recall on at least two separate dates. Flashcards build familiarity and schedule review, but self-rating isn't counted as verified mastery.")
    last_week = [(date.today() - timedelta(days=6-i)).isoformat() for i in range(7)]
    history = pd.DataFrame([{"Day": d[5:], "Flashcards": p["sessions"].get(d, {}).get("flash", 0),
                             "Typed attempts": p["sessions"].get(d, {}).get("typed", 0)} for d in last_week]).set_index("Day")
    st.subheader("Practice over the last 7 days")
    st.bar_chart(history, stack=False)
    st.subheader("Progress by topic")
    category_rows = []
    for category in sorted({w["category"] for w in active}):
        group = [w for w in active if w["category"] == category]
        known = sum(verified(p["cards"].get(w["id"])) for w in group)
        category_rows.append({"Topic": category, "Active": len(group), "Introduced": sum(w["id"] in p["cards"] for w in group), "Verified": known})
    st.dataframe(pd.DataFrame(category_rows), use_container_width=True, hide_index=True)
    if c["total"] < 1000:
        st.info(f"Your A2+ filter currently leaves {c['total']} active words in the original 1,000-item bank. We can later expand this to 1,000 genuinely intermediate entries.")


def settings() -> None:
    st.subheader("Settings & backups")
    goal = st.slider("New words per day", min_value=1, max_value=100, value=p["settings"].get("dailyGoal", 35))
    if goal != p["settings"]["dailyGoal"]:
        p["settings"]["dailyGoal"] = goal
        push_update()
    allow_a1 = st.toggle("Include basic A1 vocabulary", value=p["settings"].get("includeA1", False), help="A1 classifications are curated estimates, not official CEFR exam grades.")
    if allow_a1 != p["settings"]["includeA1"]:
        p["settings"]["includeA1"] = allow_a1
        clear_card()
        push_update()
    st.caption(f"{len(A1)} manually estimated beginner items are hidden when A1 is switched off.")
    skipped = p["settings"].get("skippedIds", [])
    if skipped:
        st.caption(f"You've personally skipped {len(skipped)} words.")
        if st.button("Restore all personally skipped words"):
            p["settings"]["skippedIds"] = []
            push_update()
    st.divider()
    st.markdown("#### Save your progress")
    st.info("Flashcard changes are written to this browser before your next card is shown. This saves continuation on the same browser/device; another phone or computer needs a JSON backup and import. Keep a backup in case browser data is cleared.")
    st.download_button("↓ Download JSON backup", json_backup(p), file_name=f"woordkracht-backup-{today()}.json", mime="application/json", use_container_width=True)
    restored = st.file_uploader("Restore a Woordkracht v1 backup (.json)", type=["json"], key="restore_backup")
    if restored is not None:
        st.caption("Restoring replaces this Streamlit profile. Your downloaded backup stays unchanged.")
        if st.button("Replace progress with uploaded backup", type="primary"):
            try:
                st.session_state.progress = load_progress(restored.getvalue())
                clear_card()
                push_update()
            except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
                st.error(str(exc))
    st.markdown("#### Moving from the original GitHub Pages app")
    st.markdown("1. Open [the original Woordkracht app](https://orgo4ever.github.io/Woordkracht-1000/).  \n2. Use **Settings → Download progress backup**.  \n3. Come back here and import that JSON file.  \n4. Keep regular backups, since the two sites do not automatically share browser progress.")


st.markdown('<div class="brand-panel"><div class="eyebrow">WOORDKRACHT · THE VOCABULARY PROJECT</div><h1>Words that come to mind.</h1><p>Flashcards, typed recall, and intelligent spaced review — with A1 words out of your way.</p></div>', unsafe_allow_html=True)

PAGES = ["Study", "Review", "Library", "Progress", "Settings"]
if st.session_state.get("_navigate_to") in PAGES:
    st.session_state.page = st.session_state.pop("_navigate_to")
if "page" not in st.session_state:
    st.session_state.page = "Study"
page = st.segmented_control("Navigation", PAGES, key="page", label_visibility="collapsed", default="Study")
if page is None:
    page = "Study"

if page in ("Study", "Review"):
    draw_stats()
    study(review_only=page == "Review")
    if page == "Study":
        with st.expander("Already know many of these? Quick familiarity check"):
            familiarity()
elif page == "Library":
    library()
elif page == "Progress":
    dashboard()
else:
    settings()

if st.session_state.get("storage_unavailable"):
    st.warning("Autosave is disabled in this browser. Use Settings → Download JSON backup before leaving.")
else:
    st.caption("Progress is saved in this browser after each rated card. For another device, export/import a JSON backup.")
