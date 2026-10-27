"""Small, consistent line icons for the Streamlit interface."""

from __future__ import annotations

from html import escape
import re


_PATHS = {
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "settings": '<path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06-2 2-.06-.06A1.7 1.7 0 0 0 15.87 18a1.7 1.7 0 0 0-1.2 1.57V20h-2.8v-.09A1.7 1.7 0 0 0 10.7 18.3a1.7 1.7 0 0 0-1.87.34l-.06.06-2-2 .06-.06A1.7 1.7 0 0 0 7.2 14.8 1.7 1.7 0 0 0 5.6 13.6H5v-2.8h.6A1.7 1.7 0 0 0 7.2 9.6a1.7 1.7 0 0 0-.34-1.87L6.8 7.7l2-2 .06.06A1.7 1.7 0 0 0 10.7 6.1a1.7 1.7 0 0 0 1.2-1.57V4h2.8v.53A1.7 1.7 0 0 0 15.9 6.1a1.7 1.7 0 0 0 1.87-.34l.06-.06 2 2-.06.06A1.7 1.7 0 0 0 19.4 9.6a1.7 1.7 0 0 0 1.6 1.2h.5v2.8H21a1.7 1.7 0 0 0-1.6 1.4Z"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z"/>',
    "chart": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="M8 16v-4"/><path d="M12 16V8"/><path d="M16 16v-7"/>',
    "flask": '<path d="M9 3h6"/><path d="M10 3v7l-5.6 8.1A2 2 0 0 0 6 21h12a2 2 0 0 0 1.6-2.9L14 10V3"/><path d="M8 16h8"/>',
    "compare": '<rect x="3" y="5" width="7" height="14" rx="1"/><rect x="14" y="5" width="7" height="14" rx="1"/><path d="M6 9h1M17 9h1M6 13h1M17 13h1"/>',
    "lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    "cpu": '<rect x="7" y="7" width="10" height="10" rx="2"/><path d="M10 10h4v4h-4zM10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4"/>',
    "network": '<circle cx="12" cy="4" r="2"/><circle cx="5" cy="18" r="2"/><circle cx="19" cy="18" r="2"/><path d="m11 6-5 10m7-10 5 10M7 18h10"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 16l9 5 9-5"/>',
    "tag": '<path d="M3 12V4a1 1 0 0 1 1-1h8l9 9-9 9-9-9Z"/><circle cx="7.5" cy="7.5" r="1"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h1M3 12h1M3 18h1"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
    "file": '<path d="M6 2h8l4 4v16H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/><path d="M14 2v5h5M8 12h8M8 16h8"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "error": '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6m0-6-6 6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/><path d="M12 1v4M12 19v4M1 12h4M19 12h4"/>',
}


def icon_svg(name: str, *, size: int = 19) -> str:
    """Return a decorative SVG that inherits the text color."""
    if name not in _PATHS:
        raise ValueError(f"Unknown icon: {name}")
    return (
        f'<svg class="fv-icon" width="{size}" height="{size}" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true" focusable="false">{_PATHS[name]}</svg>'
    )


def icon_heading(title: str, name: str, *, level: int = 3) -> str:
    """Return an accessible heading with a decorative icon."""
    if level not in (3, 4, 5):
        raise ValueError("Heading level must be 3, 4, or 5")
    return f'<h{level} class="fv-heading">{icon_svg(name)}<span>{escape(title)}</span></h{level}>'


_DECORATIVE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\ufe0f\u200d]")


def plain_label(value: object) -> object:
    """Remove decorative symbols from legacy result labels for display only."""
    if not isinstance(value, str):
        return value
    return re.sub(r"\s+", " ", _DECORATIVE.sub("", value)).strip()
