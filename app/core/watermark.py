from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from app.core.models import WatermarkOptions


class WatermarkRenderer:
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    def __init__(self, fonts_dir: Path) -> None:
        self.fonts_dir = fonts_dir

    def render(self, source_path: Path, options: WatermarkOptions) -> Image.Image:
        base = Image.open(source_path).convert("RGBA")
        overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        color = ImageColor.getrgb(options.color_hex)
        fill = (color[0], color[1], color[2], int(options.opacity * 255 / 100))
        font = self._load_font(options.font_name, options.font_size)

        if options.mode == "tiled":
            self._draw_tiled(overlay, options, fill, font)
        else:
            self._draw_nine_grid(overlay, options, fill, font)

        result = Image.alpha_composite(base, overlay).convert("RGB")
        return result

    def export_single(self, source_path: Path, output_path: Path, options: WatermarkOptions) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        rendered = self.render(source_path, options)
        rendered.save(output_path)

    def export_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        options: WatermarkOptions,
        progress_callback=None,
    ) -> tuple[int, list[str]]:
        files = [p for p in input_dir.iterdir() if p.suffix.lower() in self.SUPPORTED_EXTENSIONS]
        total = len(files)
        failed: list[str] = []
        output_dir.mkdir(parents=True, exist_ok=True)
        for idx, image_path in enumerate(files, start=1):
            out_path = output_dir / f"{image_path.stem}_wm{image_path.suffix.lower()}"
            try:
                self.export_single(image_path, out_path, options)
            except Exception:
                failed.append(image_path.name)
            if progress_callback:
                progress_callback(idx, total)
        return total - len(failed), failed

    def _load_font(self, font_name: str, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        bundled_font = self._find_bundled_font(font_name)
        if bundled_font:
            return ImageFont.truetype(str(bundled_font), font_size)

        system_font = self._find_windows_font(font_name)
        if system_font:
            return ImageFont.truetype(str(system_font), font_size)

        # Last-resort Chinese-safe fallback order on Windows.
        for fallback_name in ("msyh.ttc", "simhei.ttf", "simsun.ttc", "arial.ttf"):
            fallback = self._find_windows_font(fallback_name)
            if fallback:
                return ImageFont.truetype(str(fallback), font_size)

        return ImageFont.load_default()

    def _find_bundled_font(self, font_name: str) -> Path | None:
        candidates = [
            self.fonts_dir / f"{font_name}.ttf",
            self.fonts_dir / f"{font_name}.TTF",
            self.fonts_dir / f"{font_name}.ttc",
            self.fonts_dir / f"{font_name}.TTC",
        ]
        lowered = font_name.lower()
        for path in self.fonts_dir.glob("*"):
            if path.suffix.lower() in {".ttf", ".ttc", ".otf"} and lowered in path.stem.lower():
                candidates.append(path)
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _find_windows_font(self, font_name: str) -> Path | None:
        windows_fonts = Path("C:/Windows/Fonts")
        if not windows_fonts.exists():
            return None

        name = font_name.lower().strip()
        direct = windows_fonts / font_name
        if direct.exists():
            return direct

        aliases = {
            "microsoft yahei": ["msyh.ttc", "msyhbd.ttc"],
            "simhei": ["simhei.ttf"],
            "simsun": ["simsun.ttc"],
            "arial": ["arial.ttf", "arialbd.ttf"],
            "times new roman": ["times.ttf", "timesbd.ttf"],
            "consolas": ["consola.ttf", "consolab.ttf"],
        }
        for file_name in aliases.get(name, []):
            candidate = windows_fonts / file_name
            if candidate.exists():
                return candidate

        for path in windows_fonts.glob("*"):
            if path.suffix.lower() in {".ttf", ".ttc", ".otf"} and name in path.stem.lower():
                return path
        return None

    def _draw_tiled(self, canvas: Image.Image, opt: WatermarkOptions, fill, font) -> None:
        draw = ImageDraw.Draw(canvas)
        size = canvas.size
        text_bbox = draw.textbbox((0, 0), opt.text, font=font)
        text_w = max(10, text_bbox[2] - text_bbox[0])
        text_h = max(10, text_bbox[3] - text_bbox[1])
        # Density mapping: 50 is neutral; higher density means smaller spacing.
        density_factor = max(0.35, min(2.0, (110 - opt.density) / 60))
        spaced_x = int(opt.spacing_x * density_factor)
        spaced_y = int(opt.spacing_y * density_factor)
        step_x = max(text_w + 20, spaced_x)
        step_y = max(text_h + 20, spaced_y)
        for y in range(-size[1], size[1] * 2, step_y):
            for x in range(-size[0], size[0] * 2, step_x):
                self._draw_text_with_rotation(canvas, (x, y), opt.text, fill, font, opt.rotation)

    def _draw_nine_grid(self, canvas: Image.Image, opt: WatermarkOptions, fill, font) -> None:
        draw = ImageDraw.Draw(canvas)
        size = canvas.size
        text_bbox = draw.textbbox((0, 0), opt.text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        margin = 24
        positions = {
            "top-left": (margin, margin),
            "top-center": ((size[0] - text_w) // 2, margin),
            "top-right": (size[0] - text_w - margin, margin),
            "center-left": (margin, (size[1] - text_h) // 2),
            "center": ((size[0] - text_w) // 2, (size[1] - text_h) // 2),
            "center-right": (size[0] - text_w - margin, (size[1] - text_h) // 2),
            "bottom-left": (margin, size[1] - text_h - margin),
            "bottom-center": ((size[0] - text_w) // 2, size[1] - text_h - margin),
            "bottom-right": (size[0] - text_w - margin, size[1] - text_h - margin),
        }
        xy = positions.get(opt.position, positions["bottom-right"])
        self._draw_text_with_rotation(canvas, xy, opt.text, fill, font, opt.rotation)

    def _draw_text_with_rotation(self, canvas: Image.Image, xy, text: str, fill, font, angle: int) -> None:
        if angle == 0:
            ImageDraw.Draw(canvas).text(xy, text, fill=fill, font=font)
            return
        dummy = ImageDraw.Draw(canvas)
        bbox = dummy.textbbox((0, 0), text, font=font)
        text_w = max(1, bbox[2] - bbox[0])
        text_h = max(1, bbox[3] - bbox[1])
        text_layer = Image.new("RGBA", (text_w + 8, text_h + 8), (0, 0, 0, 0))
        ImageDraw.Draw(text_layer).text((4, 4), text, fill=fill, font=font)
        rotated = text_layer.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        canvas.alpha_composite(rotated, dest=(int(xy[0]), int(xy[1])))
