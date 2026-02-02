from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt
from src.ui.editor_widget import InteractivePreview

class FrameEditorDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Frame")
        self.resize(1100, 850)
        
        self.image_path = image_path
        
        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # --- Top Toolbar ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        lbl_tools = QLabel("Tools:")
        lbl_tools.setStyleSheet("color: #ccc; font-weight: bold;")
        
        self.btn_wand = QPushButton("Magic Wand")
        self.btn_wand.setCheckable(True)
        self.btn_wand.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_WAND))
        
        self.btn_rect = QPushButton("Rect")
        self.btn_rect.setCheckable(True)
        self.btn_rect.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_RECT))
        
        self.btn_lasso = QPushButton("Lasso")
        self.btn_lasso.setCheckable(True)
        self.btn_lasso.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_LASSO))
        
        self.btn_eraser = QPushButton("Eraser")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.clicked.connect(lambda: self.set_tool(InteractivePreview.TOOL_ERASER))
        
        toolbar.addWidget(lbl_tools)
        toolbar.addWidget(self.btn_wand)
        toolbar.addWidget(self.btn_rect)
        toolbar.addWidget(self.btn_lasso)
        toolbar.addWidget(self.btn_eraser)
        toolbar.addSpacing(20)
        
        # Tolerance
        lbl_tol = QLabel("Tolerance:")
        lbl_tol.setStyleSheet("color: #aaa;")
        self.slider_tol = QSlider(Qt.Orientation.Horizontal)
        self.slider_tol.setRange(1, 100)
        self.slider_tol.setValue(20)
        self.slider_tol.setFixedWidth(100)
        self.slider_tol.valueChanged.connect(self.on_tolerance_changed)
        self.lbl_tol_val = QLabel("20")
        self.lbl_tol_val.setFixedWidth(25)
        self.lbl_tol_val.setStyleSheet("color: #ccc;")
        
        toolbar.addWidget(lbl_tol)
        toolbar.addWidget(self.slider_tol)
        toolbar.addWidget(self.lbl_tol_val)
        toolbar.addSpacing(20)
        
        # Brush Size
        lbl_brush = QLabel("Brush:")
        lbl_brush.setStyleSheet("color: #aaa;")
        self.spin_brush = QSpinBox()
        self.spin_brush.setRange(1, 100)
        self.spin_brush.setValue(15)
        self.spin_brush.setFixedWidth(60)
        self.spin_brush.valueChanged.connect(self.on_brush_changed)
        
        toolbar.addWidget(lbl_brush)
        toolbar.addWidget(self.spin_brush)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # --- Second Toolbar (Zoom, Undo, Actions) ---
        toolbar2 = QHBoxLayout()
        toolbar2.setSpacing(8)
        
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedWidth(35)
        self.btn_zoom_in.clicked.connect(lambda: self.editor_widget.zoom_in())
        
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedWidth(35)
        self.btn_zoom_out.clicked.connect(lambda: self.editor_widget.zoom_out())
        
        self.btn_zoom_reset = QPushButton("Fit")
        self.btn_zoom_reset.clicked.connect(lambda: self.editor_widget.zoom_reset())
        
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("color: #888; margin-left: 5px;")
        
        toolbar2.addWidget(QLabel("Zoom:"))
        toolbar2.addWidget(self.btn_zoom_out)
        toolbar2.addWidget(self.btn_zoom_in)
        toolbar2.addWidget(self.btn_zoom_reset)
        toolbar2.addWidget(self.lbl_zoom)
        toolbar2.addSpacing(20)
        
        self.btn_undo = QPushButton("Undo (Ctrl+Z)")
        self.btn_undo.clicked.connect(lambda: self.editor_widget.undo())
        
        self.btn_invert = QPushButton("Invert (Ctrl+I)")
        self.btn_invert.clicked.connect(lambda: self.editor_widget.invert_selection())
        
        toolbar2.addWidget(self.btn_undo)
        toolbar2.addWidget(self.btn_invert)
        toolbar2.addStretch()
        
        self.lbl_help = QLabel("Select area → DELETE to erase | ESC to deselect")
        self.lbl_help.setStyleSheet("color: #666; font-style: italic;")
        toolbar2.addWidget(self.lbl_help)
        
        layout.addLayout(toolbar2)
        
        # --- Editor Area ---
        frame_container = QFrame()
        frame_container.setStyleSheet("background-color: #000; border: 1px solid #333;")
        container_layout = QVBoxLayout(frame_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.editor_widget = InteractivePreview()
        self.editor_widget.setStyleSheet("background-color: #111;")
        self.editor_widget.zoom_changed.connect(self.on_zoom_changed)
        container_layout.addWidget(self.editor_widget)
        
        layout.addWidget(frame_container, 1)
        
        # --- Footer ---
        footer = QHBoxLayout()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("DestructiveButton")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Save Changes")
        self.btn_save.clicked.connect(self.save_and_close)
        
        footer.addStretch()
        footer.addWidget(self.btn_cancel)
        footer.addWidget(self.btn_save)
        
        layout.addLayout(footer)

    def load_image(self):
        self.editor_widget.set_image(self.image_path)
        self.btn_wand.click()

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
        self.lbl_zoom.setText(f"{int(level * 100)}%")

    def save_and_close(self):
        success = self.editor_widget.save_to_disk()
        if success:
            self.accept()
