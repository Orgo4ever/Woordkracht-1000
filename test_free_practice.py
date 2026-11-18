"""Unit tests for repeatable Free Practice decks (no Streamlit required)."""
import unittest
from copy import deepcopy
from pathlib import Path
from random import Random

from free_practice import make_deck, practice_candidates, shuffle_deck
from vocab_core import fresh_progress, load_bank, rate, visible_words, add_custom_word, skip


class TestFreePractice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.words, cls.a1 = load_bank(Path(__file__).parent)

    def setUp(self):
        self.progress = fresh_progress("2026-11-18")
        self.pool = visible_words(self.words, self.a1, self.progress)

    def test_all_eligible_respects_existing_a1_and_skip_filters(self):
        self.assertEqual(len(practice_candidates(self.pool, self.progress, "All eligible words")), 448)
        skip(self.progress, self.pool[0]["id"])
        filtered = visible_words(self.words, self.a1, self.progress)
        self.assertNotIn(self.pool[0]["id"], [w["id"] for w in practice_candidates(filtered, self.progress, "All eligible words")])

    def test_previously_encountered_includes_words_not_due(self):
        word = self.pool[0]
        rate(self.progress, word["id"], "easy", mode="flash", day="2026-11-18")
        seen = practice_candidates(self.pool, self.progress, "Previously encountered")
        self.assertEqual([w["id"] for w in seen], [word["id"]])
        self.assertEqual(self.progress["cards"][word["id"]]["due"], "2026-11-21")

    def test_difficult_uses_latest_again_or_hard(self):
        rate(self.progress, self.pool[0]["id"], "hard", mode="flash", day="2026-11-18")
        rate(self.progress, self.pool[1]["id"], "again", mode="flash", day="2026-11-18")
        rate(self.progress, self.pool[2]["id"], "easy", mode="flash", day="2026-11-18")
        difficult = practice_candidates(self.pool, self.progress, "Difficult words")
        self.assertEqual({w["id"] for w in difficult}, {self.pool[0]["id"], self.pool[1]["id"]})

    def test_deck_size_no_duplicates_no_mutated_progress(self):
        before = deepcopy(self.progress)
        deck = make_deck(self.pool, 20, Random(4))
        self.assertEqual(len(deck), 20)
        self.assertEqual(len(set(deck)), 20)
        self.assertEqual(self.progress, before)
        self.assertTrue(set(deck).issubset({w["id"] for w in self.pool}))
        for invalid in (0, len(self.pool) + 1, -1):
            with self.assertRaises(ValueError):
                make_deck(self.pool, invalid)
        with self.assertRaises(ValueError):
            make_deck([], 1)

    def test_shuffle_preserves_exact_deck_and_changes_order(self):
        deck = make_deck(self.pool, 20, Random(8))
        shuffled = shuffle_deck(deck, Random(5))
        self.assertNotEqual(shuffled, deck)
        self.assertEqual(set(shuffled), set(deck))
        self.assertEqual(deck, make_deck(self.pool, 20, Random(8)))
        # A deterministic shuffle that keeps the same order still gets rotated.
        unchanged_order = shuffle_deck(["only"], Random(1))
        self.assertEqual(unchanged_order, ["only"])

    def test_custom_words_are_available_and_unknown_source_rejected(self):
        extra = add_custom_word(self.progress, self.words, "to reconsider", "heroverwegen")
        candidates = practice_candidates(visible_words(self.words, self.a1, self.progress),
                                         self.progress, "All eligible words")
        self.assertIn(extra["id"], [w["id"] for w in candidates])
        with self.assertRaises(ValueError):
            practice_candidates(self.pool, self.progress, "Unknown")


if __name__ == "__main__":
    unittest.main()
