"""Session-only practice decks, independent of Woordkracht's scheduled reviews.

These helpers never mutate the progress profile or mark words as studied.
"""
from __future__ import annotations

from random import Random


SOURCES = ("Previously encountered", "Difficult words", "All eligible words")


def practice_candidates(words: list[dict], progress: dict, source: str) -> list[dict]:
    """Filter the already-visible word pool for an optional practice session."""
    if source not in SOURCES:
        raise ValueError(f"Unknown practice source: {source}")
    if source == "All eligible words":
        return list(words)

    records = progress["cards"]
    if source == "Previously encountered":
        return [word for word in words if word["id"] in records]

    # This is deliberately simple and transparent: no hidden mastery changes.
    return [word for word in words
            if records.get(word["id"], {}).get("lastRating") in {"again", "hard"}]


def make_deck(words: list[dict], count: int, rng: Random | None = None) -> list[str]:
    """Return a random sample of word IDs, without duplicates or side effects."""
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= len(words):
        raise ValueError("Deck size must be between 1 and the available word count")
    ids = [word["id"] for word in words]
    if len(ids) != len(set(ids)):
        raise ValueError("Practice candidate IDs must be unique")
    return (rng if rng is not None else Random()).sample(ids, count)


def shuffle_deck(ids: list[str], rng: Random | None = None) -> list[str]:
    """Shuffle the same deck, guaranteeing a changed order for 2+ cards."""
    shuffled = list(ids)
    (rng if rng is not None else Random()).shuffle(shuffled)
    if len(shuffled) > 1 and shuffled == ids:
        shuffled = shuffled[1:] + shuffled[:1]
    return shuffled
