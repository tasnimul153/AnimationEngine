from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSlider, QSpinBox, QStatusBar
)
from PyQt6.QtCore import Qt
from src.ui.editor_widget import InteractivePreview

class FrameEditorDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Frame Editor")
        self.resize(1200, 900)
        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QLabel { color: #ccc; }
            QPushButton { 
                background: #333; color: #fff; border: none; 
                padding: 8px 14px; border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background: #444; }
            QPushButton:checked { background: #2a6; border: 1px solid #3b7; }
            QSlider::groove:horizontal { background: #444; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #888; width: 14px; margin: -4px 0; border-radius: 7px; }
            QSpinBox { background: #333; color: #fff; border: 1px solid #444; padding: 4px; }
            QStatusBar { background: #111; color: #888; }
        """)
        
        self.image_path = image_path
        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 0)
        
        # --- Top Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        
        lbl_tools = QLabel("🛠 Tools:")
        lbl_tools.setStyleSheet("font-weight: bold; color: #aaa;")
        
        self.btn_wand = QPushButton("✨ Wand")
        self.btn_wand.setCheckable(True)
        self.btn_wand.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_WAND))
        
        self.btn_rect = QPushButton("⬜ Rect")
        self.btn_rect.setCheckable(True)
        self.btn_rect.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_RECT))
        
        self.btn_lasso = QPushButton("✏️ Lasso")
        self.btn_lasso.setCheckable(True)
        self.btn_lasso.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_LASSO))
        
        self.btn_eraser = QPushButton("🧽 Eraser")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_ERASER))
        
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("color: #444;")
        
        toolbar.addWidget(lbl_tools)
        toolbar.addWidget(self.btn_wand)
        toolbar.addWidget(self.btn_rect)
        toolbar.addWidget(self.btn_lasso)
        toolbar.addWidget(self.btn_eraser)
        toolbar.addWidget(sep1)
        
        # Tolerance
        lbl_tol = QLabel("Tolerance:")
        self.slider_tol = QSlider(Qt.Orientation.Horizontal)
        self.slider_tol.setRange(1, 100)
        self.slider_tol.setValue(20)
        self.slider_tol.setFixedWidth(90)
        self.slider_tol.valueChanged.connect(self.on_tolerance_changed)
        self.lbl_tol_val = QLabel("20")
        self.lbl_tol_val.setFixedWidth(25)
        
        toolbar.addWidget(lbl_tol)
        toolbar.addWidget(self.slider_tol)
        toolbar.addWidget(self.lbl_tol_val)
        
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("color: #444;")
        toolbar.addWidget(sep2)
        
        # Brush Size
        lbl_brush = QLabel("Brush:")
        self.spin_brush = QSpinBox()
        self.spin_brush.setRange(1, 100)
        self.spin_brush.setValue(15)
        self.spin_brush.setFixedWidth(55)
        self.spin_brush.valueChanged.connect(self.on_brush_changed)
        
        toolbar.addWidget(lbl_brush)
        toolbar.addWidget(self.spin_brush)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # --- Second Toolbar ---
        toolbar2 = QHBoxLayout()
        toolbar2.setSpacing(6)
        
        lbl_zoom = QLabel("🔍 Zoom:")
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedWidth(32)
        self.btn_zoom_out.clicked.connect(lambda: self.editor_widget.zoom_out())
        
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedWidth(32)
        self.btn_zoom_in.clicked.connect(lambda: self.editor_widget.zoom_in())
        
        self.btn_zoom_reset = QPushButton("Fit")
        self.btn_zoom_reset.clicked.connect(lambda: self.editor_widget.zoom_reset())
        
        self.lbl_zoom_val = QLabel("100%")
        self.lbl_zoom_val.setStyleSheet("color: #888; min-width: 45px;")
        
        toolbar2.addWidget(lbl_zoom)
        toolbar2.addWidget(self.btn_zoom_out)
        toolbar2.addWidget(self.btn_zoom_in)
        toolbar2.addWidget(self.btn_zoom_reset)
        toolbar2.addWidget(self.lbl_zoom_val)
        toolbar2.addSpacing(15)
        
        self.btn_undo = QPushButton("↩ Undo")
        self.btn_undo.clicked.connect(lambda: self.editor_widget.undo())
        
        self.btn_invert = QPushButton("🔄 Invert")
        self.btn_invert.clicked.connect(lambda: self.editor_widget.invert_selection())
        
        toolbar2.addWidget(self.btn_undo)
        toolbar2.addWidget(self.btn_invert)
        toolbar2.addStretch()
        
        lbl_hint = QLabel("Space+Drag to pan | Scroll to zoom")
        lbl_hint.setStyleSheet("color: #555; font-style: italic;")
        toolbar2.addWidget(lbl_hint)
        
        layout.addLayout(toolbar2)
        
        # --- Editor Area ---
        self.editor_widget = InteractivePreview()
        self.editor_widget.setStyleSheet("background-color: #111; border: 1px solid #333; border-radius: 4px;")
        self.editor_widget.zoom_changed.connect(self.on_zoom_changed)
        self.editor_widget.cursor_moved.connect(self.on_cursor_moved)
        
        layout.addWidget(self.editor_widget, 1)
        
        # --- Footer ---
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 8, 0, 0)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("background: transparent; border: 1px solid #555;")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("💾 Save Changes")
        self.btn_save.setStyleSheet("background: #2a6; color: #fff;")
        self.btn_save.clicked.connect(self.save_and_close)
        
        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_save)
        
        layout.addLayout(footer)
        
        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("Ready")
        layout.addWidget(self.status_bar)

    def load_image(self):
        self.editor_widget.set_image(self.image_path)
        self.btn_wand.click()
        self.status_bar.showMessage(f"Loaded: {self.image_path}")

    def set_tool(self, tool_id):
        self.editor_widget.set_tool(tool_id)
        
        self.btn_wand.setChecked(tool_id == InteractivePreview.TOOL_WAND)
        self.btn_rect.setChecked(tool_id == InteractivePreview.TOOL_RECT)
        self.btn_lasso.setChecked(tool_id == InteractivePreview.TOOL_LASSO)
        self.btn_eraser.setChecked(tool_id == InteractivePreview.TOOL_ERASER)
        
    def on_tolerance_changed(self, value):
        self.lbl_tol_val.setText(str(value))
        self.editor_widget.set_tolerance(value)
        
    def on_brush_changed(self, value):
        self.editor_widget.set_brush_size(value)
        
    def on_zoom_changed(self, level):
        self.lbl_zoom_val.setText(f"{int(level * 100)}%")
        
    def on_cursor_moved(self, x, y):
        self.status_bar.showMessage(f"Position: ({x}, {y})")

    def save_and_close(self):
        success = self.editor_widget.save_to_disk()
        if success:
            self.accept()
