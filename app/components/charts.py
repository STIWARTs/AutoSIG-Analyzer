from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Instrument-panel token system (see docs/design.md): hairline gridlines,
# steel-cyan data points, IBM Plex Sans titles with IBM Plex Mono numeric
# readouts. Shared by every Plotly chart so styling stays identical. Colors are
# resolved per active theme so charts match light/dark instead of pinning dark.
ACCENT = "#3E92CC"
SANS = "IBM Plex Sans"
MONO = "IBM Plex Mono"

_PALETTE = {
    "dark": {"bg": "#0B0F14", "line": "#232A33", "text": "#E6EDF3", "template": "plotly_dark"},
    "light": {"bg": "#F7F9FB", "line": "#D5DCE4", "text": "#1B2733", "template": "plotly_white"},
}


def palette() -> dict[str, str]:
    """Active chart palette; pages use it for series/text colors too."""
    return _PALETTE.get(st.context.theme.type, _PALETTE["dark"])


def dark_layout(fig: go.Figure, height: int = 300) -> go.Figure:
    p = palette()
    fig.update_layout(template=p["template"], paper_bgcolor=p["bg"], plot_bgcolor=p["bg"],
                      height=height, font=dict(family=SANS, color=p["text"]),
                      margin=dict(l=45, r=20, t=40, b=40), showlegend=False)
    fig.update_xaxes(gridcolor=p["line"], zerolinecolor=p["line"])
    fig.update_yaxes(gridcolor=p["line"], zerolinecolor=p["line"])
    return fig


def _symmetric_limit(samples: np.ndarray, percentile: float = 99.0, margin: float = 1.15) -> float:
    """Half-width for a square I/Q frame: a high percentile of the symbol radius
    (so a handful of outlier symbols cannot stretch the frame) plus a small fixed
    margin. Falls back to the true max, then to 1.0, for degenerate/empty input."""
    if samples.size == 0:
        return 1.0
    radius = np.abs(samples)
    hi = float(np.percentile(radius, percentile))
    if not np.isfinite(hi) or hi <= 0:
        hi = float(radius.max())
    return hi * margin if hi > 0 else 1.0


def constellation_figure(samples: np.ndarray, title: str, size: int = 300) -> go.Figure:
    """Scatter of complex I/Q samples as accent-colored markers on the plot surface.

    The figure is square and uses symmetric margins, so the drawing area is
    square; both axes are then forced to the SAME symmetric range [-limit, +limit]
    (no scaleanchor, which lets Plotly silently override one axis). A square
    drawing area + equal numeric ranges guarantees identical px/unit on I and Q,
    so the constellation sits in a true square frame that outliers cannot skew.
    """
    view = np.asarray(samples)
    fig = go.Figure(go.Scattergl(x=view.real, y=view.imag, mode="markers",
                                 marker=dict(size=4, color=ACCENT, opacity=.55)))
    limit = _symmetric_limit(view)
    edge = 55  # symmetric margins -> square drawing area of (size - 2*edge) per side
    fig = dark_layout(fig, size)
    fig.update_layout(width=size, height=size, margin=dict(l=edge, r=edge, t=edge, b=edge),
                      title=dict(text=title, font=dict(family=SANS), x=0.5, xanchor="center"),
                      xaxis_title="I", yaxis_title="Q",
                      xaxis=dict(range=[-limit, limit], tickfont=dict(family=MONO)),
                      yaxis=dict(range=[-limit, limit], tickfont=dict(family=MONO)))
    return fig
