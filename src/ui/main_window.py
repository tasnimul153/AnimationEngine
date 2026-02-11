import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QGroupBox, 
    QFormLayout, QSpinBox, QCheckBox, QComboBox, 
    QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage
from src.workers.processing_thread import ProcessingWorker

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QFrame, 
    QFormLayout, QSpinBox, QCheckBox, QComboBox, 
    QTextEdit, QProgressBar, QMessageBox, QSizePolicy,
    QTabWidget, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage
from src.workers.processing_thread import ProcessingWorker

from src.core.video_processor import VideoLoader
import cv2

from src.ui.animator_tab import AnimatorTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video to Unity Sprite Converter")
        self.resize(1200, 850)
        
        # Load Stylesheet
        with open(os.path.join(os.path.dirname(__file__), 'styles.qss'), 'r') as f:
            self.setStyleSheet(f.read())

        self.worker = None
        self.selected_video = None
        self.selected_output = os.path.abspath("output")
        self.video_meta = None

        # Content Container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Top-Level Tabs
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("MainTabs")
        
        # TAB 1: Frame Extractor (Existing UI)
        self.extractor_tab = QWidget()
        self.setup_extractor_tab()
        self.main_tabs.addTab(self.extractor_tab, "Frame Extractor")
        
        # TAB 2: Animator (New UI)
        self.animator_tab = AnimatorTab()
        self.main_tabs.addTab(self.animator_tab, "Animator Studio")
        
        self.main_layout.addWidget(self.main_tabs)

    def setup_extractor_tab(self):
        layout = QVBoxLayout(self.extractor_tab)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(20)

        # 1. Header
        header = QLabel("Video to Unity Sprites")
        header.setObjectName("HeaderLabel")
        layout.addWidget(header)

        # --- DASHBOARD (Info Card) ---
        self.dashboard_card = QFrame()
        self.dashboard_card.setObjectName("Card")
        self.dashboard_card.setVisible(False) # Hidden until video loaded
        dash_layout = QHBoxLayout(self.dashboard_card)
        dash_layout.setContentsMargins(20, 15, 20, 15)
        
        # Source Stats
        self.source_info_label = QLabel("Source: -")
        self.source_info_label.setStyleSheet("color: #B3B3B3; font-weight: bold;")
        dash_layout.addWidget(self.source_info_label)
        
        dash_layout.addStretch()
        
        # Output Estimates
        self.est_frames_label = QLabel("Output: -")
        self.est_frames_label.setStyleSheet("color: #E50914; font-size: 16px; font-weight: bold;")
        dash_layout.addWidget(self.est_frames_label)
        
        layout.addWidget(self.dashboard_card)

        # 2. Content Area (Split View)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # --- LEFT COLUMN (Configuration) ---
        left_column = QVBoxLayout()
        left_column.setSpacing(20)

        # Card: Input Source
        input_card = QFrame()
        input_card.setObjectName("Card")
        input_layout = QVBoxLayout(input_card)
        
        input_title = QLabel("Input Source")
        input_title.setObjectName("SectionTitle")
        input_layout.addWidget(input_title)
        
        self.video_path_label = QLabel("No video selected")
        self.video_path_label.setStyleSheet("color: #5F6368; font-style: italic;")
        self.video_path_label.setWordWrap(True)
        
        self.select_video_btn = QPushButton("Select Video File")
        self.select_video_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_video_btn.clicked.connect(self.select_video)
        
        input_layout.addWidget(self.select_video_btn)
        input_layout.addWidget(self.video_path_label)
        left_column.addWidget(input_card)

        # Card: Output Destination
        output_card = QFrame()
        output_card.setObjectName("Card")
        output_layout = QVBoxLayout(output_card)
        
        output_title = QLabel("Output Folder")
        output_title.setObjectName("SectionTitle")
        output_layout.addWidget(output_title)
        
        self.output_path_label = QLabel(self.selected_output)
        self.output_path_label.setStyleSheet("color: #5F6368; font-size: 12px;")
        self.output_path_label.setWordWrap(True)
        
        self.select_output_btn = QPushButton("Change Output Folder")
        self.select_output_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_output_btn.clicked.connect(self.select_output)
        
        output_layout.addWidget(self.select_output_btn)
        output_layout.addWidget(self.output_path_label)
        left_column.addWidget(output_card)

        # Tabs for Settings (Renamed variable to avoid conflict if I used self.settings_tabs elsewhere, but I will keep name self.settings_tabs as it's class member)
        self.settings_tabs = QTabWidget()
        
        # Helper lambda for cleaner code
        def add_block(layout, label_text, widget, subtext):
            l = QLabel(label_text)
            l.setObjectName("SettingLabel")
            l.setWordWrap(True)
            layout.addWidget(l)
            layout.addWidget(widget)
            s = QLabel(subtext)
            s.setObjectName("SettingSubtext")
            s.setWordWrap(True)
            layout.addWidget(s)
            layout.addSpacing(10)

        # --- TAB 1: General ---
        tab_general = QWidget()
        scroll_gen = QScrollArea() # Use scroll area for taller UI
        scroll_gen.setWidgetResizable(True)
        scroll_gen.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content_gen = QWidget()
        layout_gen = QVBoxLayout(scroll_content_gen)
        layout_gen.setSpacing(5)
        
        # Mode
        self.extract_mode = QComboBox()
        self.extract_mode.addItems(["Extract Every N Frames", "Target FPS"])
        self.extract_mode.currentIndexChanged.connect(self.toggle_fps_input)
        add_block(layout_gen, "Extraction Strategy", self.extract_mode, 
                  "Choose 'Target FPS' to resample video (e.g. convert 60fps to 12fps) or 'Extract Every N' to just skip frames.")

        # Skips
        self.skip_frames_input = QSpinBox()
        self.skip_frames_input.setRange(0, 60)
        self.skip_frames_input.valueChanged.connect(self.update_dashboard)
        add_block(layout_gen, "Skip Frames", self.skip_frames_input,
                  "discard N frames between each capture. Higher values make the animation faster/choppier.")

        # FPS
        self.target_fps_input = QSpinBox()
        self.target_fps_input.setRange(1, 120)
        self.target_fps_input.setValue(12)
        self.target_fps_input.setEnabled(False)
        self.target_fps_input.valueChanged.connect(self.update_dashboard)
        add_block(layout_gen, "Target FPS", self.target_fps_input,
                  "The desired output frame rate. Useful for matching Unity animation speeds.")
        
        layout_gen.addStretch()
        scroll_gen.setWidget(scroll_content_gen)
        
        # --- TAB 2: Sizing & Crop ---
        tab_sizing = QWidget()
        scroll_siz = QScrollArea()
        scroll_siz.setWidgetResizable(True)
        scroll_siz.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content_siz = QWidget()
        layout_siz = QVBoxLayout(scroll_content_siz)
        layout_siz.setSpacing(5)
        
        # Keep Original
        self.keep_original_cb = QCheckBox("Keep Original Position (Fix Jitter)")
        self.keep_original_cb.toggled.connect(self.toggle_sizing_options)
        add_block(layout_siz, "Stability Control", self.keep_original_cb,
                  "CRITICAL: Enables full-frame output. Prevents the character from 'jumping' around by disabling auto-cropping. Best for standing animations.")
        
        self.sizing_group = QGroupBox("Cropping & Canvas")
        layout_group = QVBoxLayout(self.sizing_group)
        
        # Padding
        self.padding_input = QSpinBox()
        self.padding_input.setRange(0, 100)
        self.padding_input.setValue(10)
        add_block(layout_group, "Padding (px)", self.padding_input,
                  "Adds transparent space around the character to prevent clipping edges.")

        # Uniform Size
        self.uniform_size_cb = QCheckBox("Force Uniform Size")
        self.uniform_size_cb.toggled.connect(self.toggle_size_input)
        add_block(layout_group, "Canvas Normalization", self.uniform_size_cb,
                  "Places every sprite on a fixed-size canvas (e.g., 512x512). Essential for robust Unity animations.")

        # Width/Height
        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        self.width_input = QSpinBox()
        self.width_input.setRange(32, 4096)
        self.width_input.setValue(512)
        self.width_input.setEnabled(False)
        self.height_input = QSpinBox()
        self.height_input.setRange(32, 4096)
        self.height_input.setValue(512)
        self.height_input.setEnabled(False)
        size_layout.addWidget(QLabel("W:"))
        size_layout.addWidget(self.width_input)
        size_layout.addWidget(QLabel("H:"))
        size_layout.addWidget(self.height_input)
        add_block(layout_group, "Target Canvas Size", size_widget, 
                  "The physical dimensions of the output PNG files.")

        # Anchor
        self.anchor_cb = QComboBox()
        self.anchor_cb.addItems(["Center", "Bottom Center"])
        self.anchor_cb.setEnabled(False)
        add_block(layout_group, "Anchor Point", self.anchor_cb,
                  "Where the character stands on the canvas. 'Bottom Center' is standard for grounded characters.")
        
        layout_siz.addWidget(self.sizing_group)
        layout_siz.addStretch()
        scroll_siz.setWidget(scroll_content_siz)

        # --- TAB 3: AI Quality ---
        tab_quality = QWidget()
        scroll_qual = QScrollArea()
        scroll_qual.setWidgetResizable(True)
        scroll_qual.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content_qual = QWidget()
        layout_qual = QVBoxLayout(scroll_content_qual)
        layout_qual.setSpacing(5)
        
        # Model
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "isnet-general-use",  # Best balance of speed/quality
            "u2net",              # Classic, reliable
            "birefnet-general",   # State-of-the-art (slower, 1GB download)
            "isnet-anime",        # For cartoons/anime
            "u2net_human_seg",    # Optimized for people
        ])
        self.model_combo.setCurrentText("isnet-general-use")
        add_block(layout_qual, "AI Model", self.model_combo,
                  "'isnet-general-use' is recommended. 'birefnet-general' is most accurate but slower.")
        
        # Alpha Matting (enabled by default for better edges)
        self.alpha_matting_cb = QCheckBox("Enable Alpha Matting")
        self.alpha_matting_cb.setChecked(True)  # ON by default
        self.alpha_matting_cb.toggled.connect(self.toggle_alpha_options)
        add_block(layout_qual, "Edge Refinement", self.alpha_matting_cb,
                  "Improves edge quality. Essential for hair, smoke, or semi-transparent areas.")
        
        # Edge Smoothing (NEW)
        self.edge_smoothing_cb = QCheckBox("Enable Edge Smoothing")
        self.edge_smoothing_cb.setChecked(False)
        add_block(layout_qual, "Edge Cleanup", self.edge_smoothing_cb,
                  "Applies a subtle blur to the cut-out edges to remove the 'jagged pixel' look. Makes sprites blend better in-game.")

        # Thresholds
        self.alpha_group = QGroupBox("Matting Thresholds")
        self.alpha_group.setEnabled(True)  # Enabled by default since alpha matting is on
        layout_alpha = QVBoxLayout(self.alpha_group)
        
        self.fg_threshold = QSpinBox()
        self.fg_threshold.setRange(0, 255)
        self.fg_threshold.setValue(240)
        add_block(layout_alpha, "Foreground Cutoff", self.fg_threshold,
                  "Pixels brighter than this are Opaque. Lower it if the white character is disappearing.")
        
        self.bg_threshold = QSpinBox()
        self.bg_threshold.setRange(0, 255)
        self.bg_threshold.setValue(10)
        add_block(layout_alpha, "Background Cutoff", self.bg_threshold,
                  "Pixels darker than this are Transparent. Raise it if noise remains.")
        
        layout_qual.addWidget(self.alpha_group)
        
        # Background Color Cleanup (NEW)
        self.cleanup_cb = QCheckBox("Clean Residual Background")
        self.cleanup_cb.setChecked(True)  # On by default
        self.cleanup_cb.toggled.connect(self.toggle_cleanup_options)
        add_block(layout_qual, "Color Cleanup", self.cleanup_cb,
                  "Removes leftover pixels similar to the background color. Great for stubborn white/green/blue screens.")
        
        self.cleanup_group = QGroupBox("Cleanup Settings")
        self.cleanup_group.setEnabled(True)
        layout_cleanup = QVBoxLayout(self.cleanup_group)
        
        self.cleanup_color_combo = QComboBox()
        self.cleanup_color_combo.addItems(["White", "Black", "Green (Chroma)", "Blue (Chroma)", "Custom..."])
        add_block(layout_cleanup, "Background Color", self.cleanup_color_combo,
                  "Select the original background color to clean up.")
        
        self.cleanup_tolerance = QSpinBox()
        self.cleanup_tolerance.setRange(5, 100)
        self.cleanup_tolerance.setValue(30)
        add_block(layout_cleanup, "Cleanup Tolerance", self.cleanup_tolerance,
                  "Higher = more aggressive cleanup. Start at 30 and increase if residue remains.")
        
        layout_qual.addWidget(self.cleanup_group)
        
        layout_qual.addStretch()
        scroll_qual.setWidget(scroll_content_qual)

        # Add tabs (using the ScrollAreas as the widgets)
        self.settings_tabs.addTab(scroll_gen, "General")
        self.settings_tabs.addTab(scroll_siz, "Sizing & Crop")
        self.settings_tabs.addTab(scroll_qual, "Quality & AI")
        
        left_column.addWidget(self.settings_tabs)
        left_column.addStretch()

        # Add left column to content
        content_layout.addLayout(left_column, 1)

        # --- RIGHT COLUMN (Preview & Actions) ---
        right_column = QVBoxLayout()
        right_column.setSpacing(20)

        # Card: Preview
        preview_card = QFrame()
        preview_card.setObjectName("Card")
        preview_layout = QVBoxLayout(preview_card)
        
        preview_title = QLabel("Preview")
        preview_title.setObjectName("SectionTitle")
        preview_layout.addWidget(preview_title)
        
        self.preview_label = QLabel("Preview Area")
        self.preview_label.setObjectName("PreviewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        preview_layout.addWidget(self.preview_label)

        right_column.addWidget(preview_card, 2) # Higher stretch for preview

        # Card: Status & Actions
        status_card = QFrame()
        status_card.setObjectName("Card")
        status_layout = QVBoxLayout(status_card)
        
        # Log Area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setObjectName("LogArea")
        self.log_area.setMaximumHeight(150)
        status_layout.addWidget(self.log_area)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DestructiveButton")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.start_btn)
        
        status_layout.addLayout(btn_layout)

        right_column.addWidget(status_card, 1)

        # Add right column to content
        content_layout.addLayout(right_column, 2)
        
        layout.addLayout(content_layout)
        
        # Connect signals for Dashboard Updates
        self.extract_mode.currentIndexChanged.connect(self.update_dashboard)
        self.skip_frames_input.valueChanged.connect(self.update_dashboard)
        self.target_fps_input.valueChanged.connect(self.update_dashboard)

    # ... [Existing helper methods] ...

    def update_dashboard(self):
        if not self.video_meta:
            self.dashboard_card.setVisible(False)
            return
            
        self.dashboard_card.setVisible(True)
        
        if self.video_meta.get("type") == "image":
            self.source_info_label.setText("Source: Single Image")
            self.est_frames_label.setText("Output: 1 Frame")
            return

        # Video Stats
        w, h = '?', '?'
        if 'width' in self.video_meta:
            w, h = self.video_meta['width'], self.video_meta['height']
            
        fps = self.video_meta.get('fps', 0)
        dur = self.video_meta.get('duration', 0)
        total_frames = self.video_meta.get('total_frames', 0)
        
        self.source_info_label.setText(f"Source: {w}x{h} @ {fps:.2f} FPS ({dur:.1f}s)")
        
        # Calculate Estimate
        mode = self.extract_mode.currentIndex()
        if mode == 1: # Target FPS
            target = self.target_fps_input.value()
            if dur > 0:
                estimated_count = int(dur * target)
            else:
                estimated_count = 0
        else: # Skip frames
            skip = self.skip_frames_input.value()
            estimated_count = total_frames // (skip + 1)
            
        self.est_frames_label.setText(f"Estimated Output: ~{estimated_count} Frames")

    def toggle_sizing_options(self):
        # If Keep Original is Check, disable resizing settings
        keep_original = self.keep_original_cb.isChecked()
        self.sizing_group.setEnabled(not keep_original)

    def toggle_alpha_options(self):
        enabled = self.alpha_matting_cb.isChecked()
        self.alpha_group.setEnabled(enabled)

    def toggle_cleanup_options(self):
        enabled = self.cleanup_cb.isChecked()
        self.cleanup_group.setEnabled(enabled)

    def get_cleanup_color(self):
        text = self.cleanup_color_combo.currentText()
        if text == "White": return (255, 255, 255)
        if text == "Black": return (0, 0, 0)
        if text == "Green (Chroma)": return (0, 255, 0)
        if text == "Blue (Chroma)": return (0, 0, 255)
        return (255, 255, 255) # Default to white
    
    def toggle_fps_input(self):
        is_target_fps = self.extract_mode.currentIndex() == 1
        self.target_fps_input.setEnabled(is_target_fps)
        self.skip_frames_input.setEnabled(not is_target_fps)
        self.update_dashboard()
    
    def toggle_size_input(self):
        enabled = self.uniform_size_cb.isChecked()
        self.width_input.setEnabled(enabled)
        self.height_input.setEnabled(enabled)
        self.anchor_cb.setEnabled(enabled)

    def select_video(self):
        # ... [Same as before, ensuring it calls update_dashboard] ...
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Input", 
            "", 
            "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.webp);;Video Files (*.mp4 *.avi *.mov *.mkv);;Image Files (*.jpg *.jpeg *.png *.webp)"
        )
        if file_path:
            self.selected_video = file_path
            self.video_path_label.setText(os.path.basename(file_path))
            self.log_message(f"Selected input: {file_path}")
            
            try:
                # Check if image
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                    self.video_meta = {"type": "image"}
                    self.update_dashboard()
                else:
                    loader = VideoLoader(file_path)
                    self.video_meta = loader.get_metadata()
                    loader.release()
                    self.update_dashboard()
            except Exception as e:
                self.log_message(f"Error reading metadata: {e}")
                self.video_meta = None
                self.update_dashboard()

    def select_output(self):
        # ... [Rest is unchanged] ...

        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if dir_path:
            self.selected_output = dir_path
            self.output_path_label.setText(dir_path)
            self.log_message(f"Selected output: {dir_path}")

    def log_message(self, msg):
        self.log_area.append(msg)
        # Auto scroll
        cursor = self.log_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_area.setTextCursor(cursor)

    def start_processing(self):
        if not self.selected_video:
            QMessageBox.warning(self, "Missing Input", "Please select a video file first.")
            return

        settings = {
            'video_path': self.selected_video,
            'output_dir': self.selected_output,
            'skip_frames': self.skip_frames_input.value(),
            'target_fps': self.target_fps_input.value() if self.extract_mode.currentIndex() == 1 else None,
            
            # Sizing Logic
            'keep_original_position': self.keep_original_cb.isChecked(),
            'padding': self.padding_input.value(),
            'use_uniform_size': self.uniform_size_cb.isChecked(),
            'uniform_width': self.width_input.value(),
            'uniform_height': self.height_input.value(),
            'anchor': 'center' if self.anchor_cb.currentIndex() == 0 else 'bottom_center',
            
            # Quality Logic
            'alpha_matting': self.alpha_matting_cb.isChecked(),
            'alpha_matting_foreground_threshold': self.fg_threshold.value(),
            'alpha_matting_background_threshold': self.bg_threshold.value(),
            'model_name': self.model_combo.currentText(),
            'edge_smoothing': self.edge_smoothing_cb.isChecked(),
            'cleanup_residue': self.cleanup_cb.isChecked(),
            'cleanup_color': self.get_cleanup_color(),
            'cleanup_tolerance': self.cleanup_tolerance.value()
        }

        self.worker = ProcessingWorker(settings)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.frame_processed.connect(self.update_preview)
        self.worker.log_message.connect(self.log_message)
        self.worker.finished_processing.connect(self.processing_finished)
        self.worker.error_occurred.connect(self.processing_error)
        
        self.worker.start()
        
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_message("Starting processing...")

    def cancel_processing(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.cancel_btn.setEnabled(False)
            self.log_message("Cancelling...")

    def update_progress(self, val, msg):
        self.progress_bar.setValue(val)

    def update_preview(self, q_image):
        pixmap = QPixmap.fromImage(q_image)
        # Check aspect ratio to scale nicely
        scaled = pixmap.scaled(
            self.preview_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled)
        self.preview_label.setText("")

    def processing_finished(self):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log_message("Processing complete!")
        QMessageBox.information(self, "Finished", "Processing complete!")

    def processing_error(self, err_msg):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.log_message(f"ERROR: {err_msg}")
        QMessageBox.critical(self, "Error", err_msg)
