from __future__ import annotations

import streamlit as st


@st.cache_resource
def is_light() -> bool:
    """Single source of truth for light/dark styling, shared by the CSS design
    tokens (widgets.py) and the chart palettes (charts.py).

    Deliberately NOT st.context.theme.type: that value is inferred in the
    browser and is known-wrong on the first script run of a session with a
    custom theme (streamlit/streamlit#11920), and it also differs per visitor
    because the Light/Dark toggle in the settings menu is stored in each
    browser's localStorage. That mismatch is what made the deployed app render
    dark native widgets with light-theme CSS (unreadable sidebar labels).
    Instead we resolve the theme deterministically server-side from the actual
    effective config (theme.backgroundColor in .streamlit/config.toml), so CSS
    and native widgets always agree on every machine.
    """
    background = st.get_option("theme.backgroundColor") or ""
    try:
        rgb = background.strip().lstrip("#")
        if len(rgb) == 3:  # expand #abc shorthand
            rgb = "".join(c * 2 for c in rgb)
        channels = [int(rgb[i:i + 2], 16) for i in (0, 2, 4)]
    except (ValueError, IndexError):
        return False  # unparseable config falls back to the dark token set
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue > 128
