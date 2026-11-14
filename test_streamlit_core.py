"""Regression tests for the Streamlit app's study engine and Pages backup format."""
import json
import unittest
from copy import deepcopy
from pathlib import Path

from vocab_core import (load_bank, fresh_progress, load_progress, json_backup,
                        visible_words, due_words, new_words, counts, rate, verified,
                        mark_known, mark_familiar_batch, skip, add_custom_word, next_word,
                        normalize)


class TestStreamlitVocabulary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.words, cls.a1 = load_bank(Path(__file__).parent)

    def setUp(self):
        self.p = fresh_progress('2026-11-14')
        self.pool = visible_words(self.words, self.a1, self.p)

    def test_default_excludes_basic_a1_and_retains_a2(self):
        self.assertEqual(len(self.words), 1000)
        self.assertEqual(len(self.a1), 552)
        self.assertEqual(len(self.pool), 448)
        self.assertNotIn('ik', [w['nl'] for w in self.pool])
        self.p['settings']['includeA1'] = True
        self.assertEqual(len(visible_words(self.words, self.a1, self.p)), 1000)

    def test_flashcards_schedule_but_never_verify(self):
        word = self.pool[0]
        rate(self.p, word['id'], 'easy', mode='flash', day='2026-11-14')
        r = self.p['cards'][word['id']]
        self.assertEqual(r['flashGood'], 1)
        self.assertEqual(r['due'], '2026-11-17')
        self.assertFalse(verified(r))
        self.assertEqual(self.p['sessions']['2026-11-14']['new'], 1)

    def test_two_day_typed_achieves_verified(self):
        word = self.pool[0]
        rate(self.p, word['id'], 'good', mode='typed', typed_correct=True, day='2026-11-14')
        self.assertFalse(verified(self.p['cards'][word['id']]))
        rate(self.p, word['id'], 'good', mode='typed', typed_correct=True, day='2026-11-15')
        self.assertTrue(verified(self.p['cards'][word['id']]))
        self.assertEqual(self.p['cards'][word['id']]['successDates'], ['2026-11-14', '2026-11-15'])

    def test_cannot_cheat_mastery_after_reveal(self):
        word = self.pool[0]
        with self.assertRaises(ValueError):
            rate(self.p, word['id'], 'easy', mode='typed', typed_correct=False)
        rate(self.p, word['id'], 'again', mode='typed', typed_correct=False, day='2026-11-14')
        self.assertFalse(verified(self.p['cards'][word['id']]))
        self.assertEqual(self.p['cards'][word['id']]['due'], '2026-11-14')

    def test_flash_then_typed_preserves_history(self):
        word = self.pool[0]
        rate(self.p, word['id'], 'good', mode='flash', day='2026-11-14')
        rate(self.p, word['id'], 'good', mode='typed', typed_correct=True, day='2026-11-15')
        self.assertEqual(self.p['cards'][word['id']]['flashAttempts'], 1)
        self.assertFalse(verified(self.p['cards'][word['id']]))

    def test_quick_familiarity_uses_no_new_allowance(self):
        ids = [w['id'] for w in self.pool[:40]]
        self.assertEqual(mark_familiar_batch(self.p, ids, day='2026-11-14'), 40)
        self.assertEqual(self.p['sessions']['2026-11-14']['new'], 0)
        self.assertTrue(all(self.p['cards'][x]['flag'] == 'preknown' for x in ids))
        self.assertFalse(verified(self.p['cards'][ids[0]]))

    def test_skip_and_custom_vocabulary(self):
        word = self.pool[0]
        skip(self.p, word['id'])
        self.assertNotIn(word['id'], [w['id'] for w in visible_words(self.words, self.a1, self.p)])
        own = add_custom_word(self.p, self.words, 'notwithstanding', 'desalniettemin')
        self.assertEqual(new_words(visible_words(self.words, self.a1, self.p), self.p)[0]['id'], own['id'])
        with self.assertRaises(ValueError):
            add_custom_word(self.p, self.words, 'duplicate', 'desalniettemin')

    def test_backup_compatibility_and_restore(self):
        word = self.pool[0]
        mark_known(self.p, word['id'], day='2026-11-14')
        original = deepcopy(self.p)
        self.assertEqual(load_progress(json_backup(self.p))['cards'], original['cards'])
        self.assertEqual(load_progress(json_backup(self.p))['sessions'], original['sessions'])
        # Older Pages backups can omit settings added in the Streamlit app.
        self.p['settings'] = {'dailyGoal': 35}
        restored = load_progress(json.dumps(self.p))
        self.assertFalse(restored['settings']['includeA1'])
        self.assertEqual(restored['settings']['skippedIds'], [])

    def test_due_first_and_daily_limit(self):
        word = self.pool[0]
        rate(self.p, word['id'], 'again', mode='flash', day='2026-11-14')
        self.assertEqual(next_word(self.pool, self.p, day='2026-11-14')['id'], word['id'])
        self.assertEqual(next_word(self.pool, self.p, review_only=True, day='2026-11-15')['id'], word['id'])
        self.assertEqual(normalize('  Gevraagd! '), 'gevraagd')


if __name__ == '__main__':
    unittest.main()
