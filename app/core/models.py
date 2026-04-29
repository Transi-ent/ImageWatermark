from dataclasses import dataclass


@dataclass
class WatermarkOptions:
    text: str = "CONFIDENTIAL"
    font_name: str = "Arial"
    font_size: int = 36
    color_hex: str = "#FFFFFF"
    opacity: int = 80  # 0-100
    rotation: int = -30
    mode: str = "tiled"  # tiled | nine-grid
    position: str = "bottom-right"  # for nine-grid
    spacing_x: int = 180
    spacing_y: int = 140
    density: int = 50  # 0-100, higher means denser for tiled mode
