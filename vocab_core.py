"""Pure study engine shared by Woordkracht's Streamlit experience.

This module deliberately preserves the v1 JSON backup schema used by the
GitHub Pages app. No user-specific progress is stored in this repository.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
import json
import re
import unicodedata
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
PROGRESS_VERSION = 1
MAX_DAILY_GOAL = 100


def today() -> str:
    return date.today().isoformat()


def plus_days(day: str, n: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=n)).isoformat()


def normalize(text: str) -> str:
    txt = unicodedata.normalize("NFD", str(text or "").lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    txt = re.sub(r"[.!?,'’]", "", txt)
    return " ".join(txt.split())


def load_bank(folder: Path = ROOT) -> tuple[list[dict], set[str]]:
    words = json.loads((folder / "words.json").read_text(encoding="utf-8"))
    excluded = json.loads((folder / "a1-words.json").read_text(encoding="utf-8"))["excluded"]
    if len(words) != 1000 or len({w["id"] for w in words}) != 1000:
        raise ValueError("Vocabulary bank must contain 1,000 uniquely identified entries")
    if len(set(excluded)) != len(excluded):
        raise ValueError("Duplicate A1 exclusions")
    unknown = set(excluded) - {w["nl"] for w in words}
    if unknown:
        raise ValueError(f"Unrecognized exclusions: {sorted(unknown)[:5]}")
    return words, set(excluded)


def fresh_progress(day: str | None = None) -> dict:
    return {
        "version": PROGRESS_VERSION, "created": day or today(),
        "settings": {"dailyGoal": 35, "includeA1": False, "skippedIds": [], "placementPage": 0},
        "cards": {}, "customWords": [], "sessions": {},
    }


def load_progress(data: str | bytes | dict) -> dict:
    """Import Pages or Streamlit backup; reject malformed/unsupported payloads."""
    if isinstance(data, bytes):
        if len(data) > 2_000_000:
            raise ValueError("Backup exceeds 2 MB")
        data = data.decode("utf-8")
    if isinstance(data, str):
        if len(data) > 2_000_000:
            raise ValueError("Backup exceeds 2 MB")
        data = json.loads(data)
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Not a Woordkracht v1 backup")
    if not isinstance(data.get("cards"), dict) or not isinstance(data.get("sessions"), dict) or not isinstance(data.get("customWords"), list):
        raise ValueError("Backup is missing cards, sessions, or customWords")
    if len(data["cards"]) > 20_000 or len(data["customWords"]) > 5_000:
        raise ValueError("Unexpectedly large backup")
    p = deepcopy(data)
    p.setdefault("created", today())
    p["settings"] = p.get("settings") if isinstance(p.get("settings"), dict) else {}
    s = p["settings"]
    try:
        s["dailyGoal"] = max(1, min(MAX_DAILY_GOAL, int(s.get("dailyGoal", 35))))
    except (ValueError, TypeError):
        s["dailyGoal"] = 35
    s["includeA1"] = s.get("includeA1", False) is True
    s["skippedIds"] = list(dict.fromkeys(str(x) for x in s.get("skippedIds", []) if isinstance(x, str))) if isinstance(s.get("skippedIds", []), list) else []
    try:
        s["placementPage"] = max(0, int(s.get("placementPage", 0)))
    except (ValueError, TypeError):
        s["placementPage"] = 0
    return p


def json_backup(progress: dict) -> str:
    return json.dumps(progress, indent=2, ensure_ascii=False)


def all_words(words: list[dict], progress: dict) -> list[dict]:
    return words + progress["customWords"]


def visible_words(words: list[dict], a1: set[str], progress: dict) -> list[dict]:
    skipped = set(progress["settings"].get("skippedIds", []))
    include = progress["settings"].get("includeA1", False)
    return [w for w in all_words(words, progress)
            if w["id"] not in skipped and (include or w.get("category") == "My missing words" or w["nl"] not in a1)]


def verified(record: dict | None) -> bool:
    if not record:
        return False
    return len(set(record.get("successDates", []))) >= 2 and record.get("successfulAttempts", 0) >= 2


def status(word: dict, progress: dict, day: str | None = None) -> str:
    r = progress["cards"].get(word["id"])
    if not r:
        return "New"
    if verified(r):
        return "Verified"
    if r.get("due", day or today()) <= (day or today()):
        return "Due"
    return "Learning"


def due_words(pool: list[dict], progress: dict, day: str | None = None) -> list[dict]:
    day = day or today()
    cards = progress["cards"]
    return sorted((w for w in pool if w["id"] in cards and cards[w["id"]].get("due", day) <= day),
                  key=lambda w: (cards[w["id"]].get("due", day), w.get("rank", 9999)))


def new_words(pool: list[dict], progress: dict) -> list[dict]:
    cards = progress["cards"]
    return sorted((w for w in pool if w["id"] not in cards),
                  key=lambda w: (w.get("category") != "My missing words", w.get("rank", 9999)))


def session(progress: dict, day: str | None = None) -> dict:
    day = day or today()
    return progress["sessions"].setdefault(day, {"new": 0, "reviews": 0, "correct": 0, "wrong": 0, "known": 0, "flash": 0, "typed": 0})


def counts(pool: list[dict], progress: dict, day: str | None = None) -> dict:
    day = day or today()
    cards = progress["cards"]
    ss = progress["sessions"].get(day, {})
    introduced = sum(w["id"] in cards for w in pool)
    return {"total": len(pool), "introduced": introduced,
            "verified": sum(verified(cards.get(w["id"])) for w in pool),
            "due": len(due_words(pool, progress, day)),
            "new": len(pool) - introduced,
            "today_new": int(ss.get("new", 0)),
            "goal": int(progress["settings"].get("dailyGoal", 35))}


def next_word(pool: list[dict], progress: dict, *, review_only: bool = False,
              avoid: tuple[str, ...] = (), day: str | None = None) -> dict | None:
    day = day or today()
    due = due_words(pool, progress, day)
    unseen = new_words(pool, progress)
    if due:
        return next((w for w in due if w["id"] not in avoid[-3:]), due[0])
    if not review_only and int(progress["sessions"].get(day, {}).get("new", 0)) < int(progress["settings"].get("dailyGoal", 35)):
        return unseen[0] if unseen else None
    return None


def new_record(day: str) -> dict:
    return {"firstSeen": day, "due": day, "interval": 0,
            "successfulAttempts": 0, "successDates": [], "attempts": 0}


def rate(progress: dict, word_id: str, rating: str, *, mode: str,
         typed_correct: bool = False, day: str | None = None) -> None:
    """Flashcard self-ratings schedule review, but don't grant verified typed recall."""
    if rating not in {"again", "hard", "good", "easy"} or mode not in {"flash", "typed"}:
        raise ValueError("Unknown rating or mode")
    if mode == "typed" and rating != "again" and not typed_correct:
        raise ValueError("A mistyped or revealed answer cannot earn recall credit")
    day = day or today()
    record = progress["cards"].get(word_id)
    is_new = record is None
    if record is None:
        record = new_record(day)
    record["attempts"] = int(record.get("attempts", 0)) + 1
    old_interval = max(0, int(record.get("interval", 0)))
    if rating == "again":
        interval = 0
    elif rating == "hard":
        interval = max(1, round(old_interval * 1.2))
    elif rating == "good":
        interval = 1 if not old_interval else max(1, round(old_interval * 2))
    else:
        interval = 3 if not old_interval else max(3, round(old_interval * 3))
    record["interval"] = interval
    record["due"] = plus_days(day, interval)
    record["lastRating"] = rating
    record["lastSeen"] = day
    if mode == "flash":
        record["flashAttempts"] = int(record.get("flashAttempts", 0)) + 1
        if rating in {"good", "easy"}:
            record["flashGood"] = int(record.get("flashGood", 0)) + 1
    elif typed_correct and rating != "again":
        record["successfulAttempts"] = int(record.get("successfulAttempts", 0)) + 1
        dates = record.setdefault("successDates", [])
        if day not in dates:
            dates.append(day)
    progress["cards"][word_id] = record
    ss = session(progress, day)
    ss["new" if is_new else "reviews"] += 1
    if mode == "flash":
        ss["flash"] = ss.get("flash", 0) + 1
    else:
        ss["typed"] = ss.get("typed", 0) + 1
        ss["correct" if typed_correct and rating != "again" else "wrong"] += 1


def mark_known(progress: dict, word_id: str, day: str | None = None) -> bool:
    if word_id in progress["cards"]:
        return False
    day = day or today()
    r = new_record(day)
    r.update({"due": plus_days(day, 1), "interval": 1, "flag": "preknown"})
    progress["cards"][word_id] = r
    ss = session(progress, day)
    ss["new"] += 1
    ss["known"] += 1
    return True


def mark_familiar_batch(progress: dict, ids: list[str], day: str | None = None) -> int:
    day = day or today()
    added = 0
    for i, word_id in enumerate(ids):
        if word_id in progress["cards"]:
            continue
        r = new_record(day)
        delay = 1 + (i % 28)
        r.update({"due": plus_days(day, delay), "interval": delay, "flag": "preknown"})
        progress["cards"][word_id] = r
        added += 1
    session(progress, day)["known"] += added
    return added


def skip(progress: dict, word_id: str) -> None:
    skipped = progress["settings"].setdefault("skippedIds", [])
    if word_id not in skipped:
        skipped.append(word_id)


def add_custom_word(progress: dict, words: list[dict], english: str, dutch: str, example: str = "") -> dict:
    english, dutch, example = english.strip(), dutch.strip(), example.strip()
    if not english or not dutch or len(english) > 120 or len(dutch) > 120:
        raise ValueError("Enter English and Dutch meanings (up to 120 characters)")
    if any(normalize(w["nl"]) == normalize(dutch) for w in all_words(words, progress)):
        raise ValueError("That Dutch word is already in your vocabulary bank")
    word = {"id": f"custom-{uuid4().hex[:14]}", "nl": dutch,
            "en": english, "category": "My missing words", "rank": 1001 + len(progress["customWords"]),
            "example_nl": example[:180], "example_en": ""}
    progress["customWords"].append(word)
    return word
