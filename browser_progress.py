"""Small Streamlit v2 browser-storage bridge for Woordkracht.

The component runs on the app origin and reads before any profile can be
created. A write is acknowledged only after localStorage.setItem succeeds.
It does not provide cross-browser or cross-device synchronization.
"""
from __future__ import annotations

import json

import streamlit as st

STORAGE_KEY = "woordkracht-streamlit-v2"  # Separate validated profile from old recovery data.
LEGACY_KEY = "woordkracht-streamlit-v1"  # Never overwrite the old storage key.

JS = r"""
export default function({data, setStateValue}) {
  const {action, key, legacyKey, value, revision} = data || {};
  if (action === 'read') {
    try {
      const raw = window.localStorage.getItem(key);
      const legacyRaw = window.localStorage.getItem(legacyKey);
      setStateValue('loaded', JSON.stringify({ok: true, present: raw !== null || legacyRaw !== null, raw, legacyRaw}));
    } catch (err) {
      setStateValue('loaded', JSON.stringify({ok: false, error: String(err)}));
    }
  } else if (action === 'write') {
    try {
      // Never write until Python has restored an existing profile or the
      // learner deliberately created/imported one.
      window.localStorage.setItem(key, value);
      const readBack = window.localStorage.getItem(key);
      if (readBack !== value) throw new Error('Saved data did not match');
      setStateValue('ack', 'ok:' + revision);
    } catch (err) {
      setStateValue('ack', 'error:' + revision + ':' + String(err));
    }
  }
}
"""

_bridge = st.components.v2.component("woordkracht.browser_progress", js=JS)


def browser_storage(*, action: str, value: str | None = None, revision: str = "") -> object:
    """Mount one stable component and return its state on this rerun."""
    if action not in {"read", "write", "idle"}:
        raise ValueError("Invalid browser storage action")
    return _bridge(
        key="woordkracht_browser_storage",
        data={"action": action, "key": STORAGE_KEY, "legacyKey": LEGACY_KEY, "value": value, "revision": revision},
        default={"loaded": None, "ack": None},
        on_loaded_change=lambda: None,
        on_ack_change=lambda: None,
        height=0,
    )


def decode_browser_value(raw: str | dict) -> dict:
    """Read a genuine v1 profile even when embedded in older storage wrappers.

    Malformed or placeholder data is never considered a fresh progress record.
    This function never changes browser storage.
    """
    from vocab_core import load_progress

    if isinstance(raw, str) and len(raw) > 2_000_000:
        raise ValueError("Stored profile exceeds the safe recovery limit")
    pending = [(raw, 0)]
    visited = 0
    wrapper_keys = ("value", "data", "progress", "profile", "payload", "content", "state", "saved", "backup")
    while pending and visited < 128:
        candidate, depth = pending.pop(0)
        visited += 1
        if depth > 12:
            continue
        if isinstance(candidate, dict):
            if candidate.get("version") == 1 and isinstance(candidate.get("cards"), dict):
                return load_progress(candidate)
            keys = [key for key in wrapper_keys if key in candidate]
            keys.extend(key for key in candidate if key not in keys)
            for key in keys[:32]:
                value = candidate.get(key)
                if isinstance(value, (dict, str, list)):
                    pending.append((value, depth + 1))
        elif isinstance(candidate, list):
            for item in candidate[:32]:
                if isinstance(item, (dict, str, list)):
                    pending.append((item, depth + 1))
        elif isinstance(candidate, str):
            try:
                pending.append((json.loads(candidate), depth + 1))
            except (json.JSONDecodeError, ValueError):
                pass
    raise ValueError("No valid Woordkracht profile was found inside the stored data")


def recover_prefer_new(current_raw: str | None, legacy_raw: str | None) -> tuple[dict | None, str | None]:
    """Prefer new valid data; fall back to valid old data without overwriting it."""
    for source, raw in (("current", current_raw), ("legacy", legacy_raw)):
        if raw is None:
            continue
        try:
            return decode_browser_value(raw), source
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
    return None, None
