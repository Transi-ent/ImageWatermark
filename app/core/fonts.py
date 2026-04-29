from pathlib import Path

from PySide6.QtGui import QFontDatabase


DEFAULT_FONT_CANDIDATES = [
    "Microsoft YaHei",
    "SimHei",
    "SimSun",
    "Arial",
    "Times New Roman",
    "Consolas",
]


def load_embedded_fonts() -> list[str]:
    """Load bundled fonts if present and return display names."""
    fonts_dir = Path(__file__).resolve().parents[2] / "assets" / "fonts"
    loaded_families: list[str] = []
    if fonts_dir.exists():
        for font_path in fonts_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_path))
            if font_id >= 0:
                loaded_families.extend(QFontDatabase.applicationFontFamilies(font_id))

    merged = loaded_families.copy()
    for fallback in DEFAULT_FONT_CANDIDATES:
        if fallback not in merged:
            merged.append(fallback)
    return merged
