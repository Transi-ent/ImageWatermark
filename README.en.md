# ImageWatermark

A lightweight Windows desktop tool for adding text watermarks to images, built with `PySide6 + Pillow`.  
It provides a simple GUI workflow with live preview and batch export, suitable for content protection and internal media processing.

## 1. Overview

`ImageWatermark` is a Windows-focused desktop application.  
It lets users complete the full workflow in UI:

`Select images -> Configure watermark -> Export output`

No command-line interaction is required for daily usage.

The project also includes packaging scripts for distributing the app to non-technical users.

## 2. Feature List

- Supports common image formats: `jpg`, `jpeg`, `png`, `bmp`, `webp`
- Single-image watermark export
- Batch folder processing and export
- Custom watermark text
- Adjustable watermark styles:
  - Font family
  - Font size
  - Color (preset common colors)
  - Opacity
  - Rotation angle
- Two layout modes:
  - Nine-grid positioning (for example: bottom-right, center)
  - Tiled mode (with adjustable horizontal/vertical spacing)
- Adjustable watermark density (tiled mode):
  - Higher density: tighter watermark distribution
  - Lower density: sparser watermark distribution
- Live preview with original/watermarked image toggle
- Built-in font loading:
  - Loads bundled `.ttf` fonts from `assets/fonts`
  - Falls back to system fonts, including Chinese-friendly options such as `Microsoft YaHei`, `SimHei`, and `SimSun`
- Windows packaging support:
  - `PyInstaller` for executable generation
  - `Inno Setup` for installer creation

## 3. Getting Started

### 3.1 Prerequisites

- OS: Windows
- Python: `3.10+` recommended

### 3.2 Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 3.3 Run the App

```bash
python app/main.py
```

### 3.4 Basic Workflow

1. Click `Select Single Image` or `Select Batch Folder`
2. Configure watermark options on the right panel (text, font, color, opacity, density, etc.)
3. Check the preview in the center area (toggle original/watermarked view)
4. Click `Export Single` or `Batch Export`

### 3.5 Build Executable and Installer

1. Run the build script:

```powershell
.\build.ps1
```

2. Open and compile the installer script with Inno Setup:

- `installer/InnoSetup.iss`

After compilation, you will get a Windows installer package.
