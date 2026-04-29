from pathlib import Path

from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.fonts import load_embedded_fonts
from app.core.models import WatermarkOptions
from app.core.watermark import WatermarkRenderer

PRESET_COLORS = [
    ("白色", "#FFFFFF"),
    ("黑色", "#000000"),
    ("红色", "#E53935"),
    ("蓝色", "#1E88E5"),
    ("绿色", "#43A047"),
    ("黄色", "#FDD835"),
    ("橙色", "#FB8C00"),
    ("灰色", "#757575"),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Image Watermark Tool")
        self.resize(1280, 760)
        self.input_file: Path | None = None
        self.input_dir: Path | None = None
        self.output_dir: Path | None = None
        self.preview_mode_original = False
        self.fonts = load_embedded_fonts()
        self.renderer = WatermarkRenderer(Path(__file__).resolve().parents[2] / "assets" / "fonts")
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(300)
        self.preview_timer.timeout.connect(self.refresh_preview)
        self._init_ui()
        self.setStyleSheet(
            "QMainWindow { background: #eef2f7; }"
            "QGroupBox { background: white; border: 1px solid #d6dde8; border-radius: 10px; margin-top: 8px; font-weight: 600; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }"
            "QPushButton { background: #2563eb; color: white; border: none; border-radius: 6px; padding: 8px 12px; }"
            "QPushButton:disabled { background: #9aa7bf; }"
            "QLineEdit, QComboBox, QSpinBox { padding: 5px 6px; border: 1px solid #cfd7e3; border-radius: 5px; }"
        )

    def _init_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setSpacing(12)

        # Left panel: source and actions
        left = QGroupBox("输入源")
        l = QVBoxLayout(left)
        self.file_label = QLabel("单张图片：未选择")
        self.dir_label = QLabel("批量目录：未选择")
        btn_pick_file = QPushButton("选择单张图片")
        btn_pick_file.clicked.connect(self.pick_file)
        btn_pick_folder = QPushButton("选择批量目录")
        btn_pick_folder.clicked.connect(self.pick_input_dir)
        btn_pick_output = QPushButton("选择输出目录")
        btn_pick_output.clicked.connect(self.pick_output_dir)
        self.export_one_btn = QPushButton("导出单张")
        self.export_one_btn.clicked.connect(self.export_single)
        self.export_batch_btn = QPushButton("批量导出")
        self.export_batch_btn.clicked.connect(self.export_batch)
        l.addWidget(self.file_label)
        l.addWidget(btn_pick_file)
        l.addSpacing(8)
        l.addWidget(self.dir_label)
        l.addWidget(btn_pick_folder)
        l.addWidget(btn_pick_output)
        l.addSpacing(8)
        l.addWidget(self.export_one_btn)
        l.addWidget(self.export_batch_btn)
        l.addStretch()

        # Center panel: preview
        center = QGroupBox("预览")
        c = QVBoxLayout(center)
        toggle_row = QHBoxLayout()
        self.toggle_btn = QPushButton("查看原图")
        self.toggle_btn.clicked.connect(self.toggle_preview_mode)
        toggle_row.addWidget(self.toggle_btn)
        toggle_row.addStretch()
        self.preview_label = QLabel("请选择一张图片进行预览")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(640, 640)
        self.preview_label.setStyleSheet("background:#f5f7fa;border:1px solid #d0d7de;border-radius:8px;")
        c.addLayout(toggle_row)
        c.addWidget(self.preview_label, 1)
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        c.addWidget(self.progress)

        # Right panel: options
        right = QGroupBox("水印设置")
        r = QGridLayout(right)
        self.text_edit = QLineEdit("CONFIDENTIAL")
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.fonts)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 180)
        self.size_spin.setValue(36)
        self.color_combo = QComboBox()
        for label, color in PRESET_COLORS:
            self.color_combo.addItem(f"{label} ({color})", userData=color)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(80)
        self.rotation_spin = QSpinBox()
        self.rotation_spin.setRange(-180, 180)
        self.rotation_spin.setValue(-30)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["tiled", "nine-grid"])
        self.position_combo = QComboBox()
        self.position_combo.addItems(
            [
                "top-left",
                "top-center",
                "top-right",
                "center-left",
                "center",
                "center-right",
                "bottom-left",
                "bottom-center",
                "bottom-right",
            ]
        )
        self.spacing_x = QSpinBox()
        self.spacing_x.setRange(40, 600)
        self.spacing_x.setValue(180)
        self.spacing_y = QSpinBox()
        self.spacing_y.setRange(40, 600)
        self.spacing_y.setValue(140)
        self.density_slider = QSlider(Qt.Horizontal)
        self.density_slider.setRange(0, 100)
        self.density_slider.setValue(50)

        controls = [
            ("文本", self.text_edit),
            ("字体", self.font_combo),
            ("字号", self.size_spin),
            ("颜色", self.color_combo),
            ("透明度", self.opacity_slider),
            ("旋转角度", self.rotation_spin),
            ("模式", self.mode_combo),
            ("位置", self.position_combo),
            ("水平间距", self.spacing_x),
            ("垂直间距", self.spacing_y),
            ("水印密度", self.density_slider),
        ]
        for row, (title, widget) in enumerate(controls):
            r.addWidget(QLabel(title), row, 0)
            r.addWidget(widget, row, 1)

        for w in [
            self.text_edit,
            self.font_combo,
            self.size_spin,
            self.color_combo,
            self.opacity_slider,
            self.rotation_spin,
            self.mode_combo,
            self.position_combo,
            self.spacing_x,
            self.spacing_y,
            self.density_slider,
        ]:
            self._connect_for_refresh(w)

        layout.addWidget(left, 0)
        layout.addWidget(center, 1)
        layout.addWidget(right, 0)

    def _connect_for_refresh(self, widget) -> None:
        signal = getattr(widget, "textChanged", None) or getattr(widget, "valueChanged", None) or getattr(
            widget, "currentTextChanged", None
        )
        if signal:
            signal.connect(self.schedule_preview_refresh)

    def pick_file(self) -> None:
        file, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not file:
            return
        self.input_file = Path(file)
        self.file_label.setText(f"单张图片：{self.input_file.name}")
        self.schedule_preview_refresh()

    def pick_input_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择批量目录")
        if folder:
            self.input_dir = Path(folder)
            self.dir_label.setText(f"批量目录：{self.input_dir.name}")

    def pick_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self.output_dir = Path(folder)

    def schedule_preview_refresh(self) -> None:
        self.preview_timer.start()

    def _options(self) -> WatermarkOptions:
        return WatermarkOptions(
            text=self.text_edit.text() or "CONFIDENTIAL",
            font_name=self.font_combo.currentText(),
            font_size=self.size_spin.value(),
            color_hex=self.color_combo.currentData() or "#FFFFFF",
            opacity=self.opacity_slider.value(),
            rotation=self.rotation_spin.value(),
            mode=self.mode_combo.currentText(),
            position=self.position_combo.currentText(),
            spacing_x=self.spacing_x.value(),
            spacing_y=self.spacing_y.value(),
            density=self.density_slider.value(),
        )

    def refresh_preview(self) -> None:
        if not self.input_file:
            return
        try:
            if self.preview_mode_original:
                from PIL import Image

                image = Image.open(self.input_file).convert("RGB")
            else:
                image = self.renderer.render(self.input_file, self._options())
            image.thumbnail((900, 900))
            qt_img = QImage(ImageQt(image))
            pix = QPixmap.fromImage(qt_img)
            self.preview_label.setPixmap(pix)
        except Exception as ex:
            self.preview_label.setText(f"预览失败: {ex}")

    def toggle_preview_mode(self) -> None:
        self.preview_mode_original = not self.preview_mode_original
        self.toggle_btn.setText("查看水印图" if self.preview_mode_original else "查看原图")
        self.refresh_preview()

    def export_single(self) -> None:
        if not self.input_file:
            QMessageBox.warning(self, "提示", "请先选择单张图片。")
            return
        output, _ = QFileDialog.getSaveFileName(
            self, "导出单张", f"{self.input_file.stem}_wm{self.input_file.suffix}", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not output:
            return
        try:
            self.renderer.export_single(self.input_file, Path(output), self._options())
            QMessageBox.information(self, "完成", "单张导出成功。")
        except Exception as ex:
            QMessageBox.critical(self, "错误", f"导出失败: {ex}")

    def export_batch(self) -> None:
        if not self.input_dir:
            QMessageBox.warning(self, "提示", "请先选择批量目录。")
            return
        if not self.output_dir:
            QMessageBox.warning(self, "提示", "请先选择输出目录。")
            return
        self.export_batch_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)

        def on_progress(current: int, total: int) -> None:
            self.progress.setMaximum(max(1, total))
            self.progress.setValue(current)

        ok_count, failed = self.renderer.export_batch(self.input_dir, self.output_dir, self._options(), on_progress)
        self.export_batch_btn.setEnabled(True)
        self.progress.setVisible(False)
        if failed:
            QMessageBox.warning(
                self, "部分成功", f"成功 {ok_count} 张，失败 {len(failed)} 张。\n失败文件：{', '.join(failed[:8])}"
            )
        else:
            QMessageBox.information(self, "完成", f"批量导出成功，共 {ok_count} 张。")
