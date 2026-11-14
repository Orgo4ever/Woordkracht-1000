"""Small Streamlit v2 browser-storage bridge for Woordkracht.

The component runs on the app origin and reads before any profile can be
created. A write is acknowledged only after localStorage.setItem succeeds.
It does not provide cross-browser or cross-device synchronization.
"""
from __future__ import annotations

import json

import streamlit as st

STORAGE_KEY = "woordkracht-streamlit-v1"  # Keep the old key for migration.

JS = r"""
export default function({data, setStateValue}) {
  const {action, key, value, revision} = data || {};
  if (action === 'read') {
    try {
      const raw = window.localStorage.getItem(key);
      setStateValue('loaded', JSON.stringify({ok: true, present: raw !== null, raw}));
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
        data={"action": action, "key": STORAGE_KEY, "value": value, "revision": revision},
        default={"loaded": None, "ack": None},
        on_loaded_change=lambda: None,
        on_ack_change=lambda: None,
        height=0,
    )


def decode_browser_value(raw: str) -> dict:
    """Read both raw JSON and older double-JSON-encoded component data."""
    from vocab_core import load_progress

    candidate = raw
    for _ in range(5):
        if isinstance(candidate, dict):
            if "version" in candidate:
                return load_progress(candidate)
            if "value" in candidate:
                candidate = candidate["value"]
                continue
            break
        if isinstance(candidate, str):
            candidate = json.loads(candidate)
            continue
        break
    raise ValueError("Stored profile is not a valid Woordkracht backup")
