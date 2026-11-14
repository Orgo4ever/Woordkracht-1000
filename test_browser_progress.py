"""Regression checks for progress restored from browser storage."""
import json
import unittest
from unittest.mock import MagicMock
import sys

mock_streamlit = MagicMock()
mock_streamlit.components.v2.component.return_value = MagicMock()
sys.modules.setdefault("streamlit", mock_streamlit)
from browser_progress import decode_browser_value, JS
from vocab_core import fresh_progress, json_backup


class BrowserStorageTests(unittest.TestCase):
    def test_raw_json_and_legacy_double_encoded(self):
        p = fresh_progress("2026-11-14")
        p["cards"]["w0088"] = {"firstSeen": "2026-11-14", "due": "2026-11-15", "attempts": 1}
        for raw in (json_backup(p), json.dumps(json_backup(p)), json.dumps({"value": json_backup(p)})):
            restored = decode_browser_value(raw)
            self.assertEqual(restored["cards"], p["cards"])

    def test_invalid_never_creates_blank_profile(self):
        with self.assertRaises((ValueError, TypeError, json.JSONDecodeError)):
            decode_browser_value('"not a backup"')

    def test_browser_ack_and_initial_read_are_explicit(self):
        self.assertIn("setStateValue('loaded'", JS)
        self.assertIn("setStateValue('ack'", JS)
        self.assertIn("window.localStorage.setItem", JS)
        self.assertIn("readBack !== value", JS)


if __name__ == "__main__":
    unittest.main()
