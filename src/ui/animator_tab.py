import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QFileDialog, 
    QSlider, QSpinBox, QSplitter, QFrame,
    QListWidgetItem, QMessageBox, QStyle, QMenu,
    QCheckBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QImage, QIcon, QAction, QPainter, QColor

class AnimatorTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # State
        self.animations = {} # { "Name": [path1, path2, ...] }
        self.current_anim_name = None
        self.current_frames = []
        self.current_frame_index = 0
        self.is_playing = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.show_next_frame)
        
        self.setup_ui()

    def create_white_icon(self, standard_pixmap):
        icon = self.style().standardIcon(standard_pixmap)
        pixmap = icon.pixmap(32, 32)
        # Create new pixmap of same size, transparent
        white_pixmap = QPixmap(pixmap.size())
        white_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(white_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(white_pixmap.rect(), Qt.GlobalColor.white)
        painter.end()
        return QIcon(white_pixmap)

    def create_symbol_icon(self, symbol):
        pix = QPixmap(32, 32)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(24)
        painter.setFont(font)
        painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, symbol)
        painter.end()
        return QIcon(pix)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        
        # --- LEFT PANEL: Animation List ---
        left_panel = QFrame()
        left_panel.setObjectName("GlassPanel") 
        left_layout = QVBoxLayout(left_panel)
        
        lbl_anims = QLabel("Animations")
        lbl_anims.setObjectName("SectionTitle")
        left_layout.addWidget(lbl_anims)
        
        self.anim_list = QListWidget()
        self.anim_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.anim_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.anim_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Enable renaming via double-click
        self.anim_list.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.anim_list.itemChanged.connect(self.on_anim_renamed)
        self.anim_list.currentItemChanged.connect(self.on_anim_selected)
        left_layout.addWidget(self.anim_list)
        
        # Buttons
        btn_layout = QVBoxLayout() 
        
        self.btn_import_folder = QPushButton("Import Folder")
        self.btn_import_folder.setToolTip("Create animation from a folder of images")
        self.btn_import_folder.clicked.connect(self.import_folder)
        
        self.btn_new_anim = QPushButton("New Empty")
        self.btn_new_anim.clicked.connect(self.create_animation)
        
        self.btn_del_anim = QPushButton("Delete Animation")
        self.btn_del_anim.setObjectName("DestructiveButton")
        self.btn_del_anim.clicked.connect(self.delete_animation)
        
        btn_layout.addWidget(self.btn_import_folder)
        btn_layout.addWidget(self.btn_new_anim)
        btn_layout.addWidget(self.btn_del_anim)
        left_layout.addLayout(btn_layout)
        
        layout.addWidget(left_panel, 1) # Stretch 1
        
        # --- CENTER PANEL: Preview & Timeline ---
        center_panel = QFrame()
        center_panel.setObjectName("GlassPanel") 
        center_layout = QVBoxLayout(center_panel)
        
        
        # Title & Filename
        header_layout = QHBoxLayout()
        lbl_preview = QLabel("Preview")
        lbl_preview.setObjectName("SectionTitle")
        
        self.lbl_filename = QLabel("")
        self.lbl_filename.setStyleSheet("color: #7A7A7A; font-style: italic; font-size: 11px;")
        self.lbl_filename.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        header_layout.addWidget(lbl_preview)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_filename)
        center_layout.addLayout(header_layout)
        
        # Preview Area
        self.preview_label = QLabel("Select an animation to start")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #161616; border-radius: 4px; color: #5C5C5C; font-size: 13px;")
        self.preview_label.setMinimumSize(400, 300)
        center_layout.addWidget(self.preview_label, 3) # Stretch 3
        
        # Timeline Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Styled Icons
        icon_play = self.create_white_icon(QStyle.StandardPixmap.SP_MediaPlay)
        self.icon_pause = self.create_white_icon(QStyle.StandardPixmap.SP_MediaPause)
        self.icon_play_cached = icon_play # Save for toggling
        
        icon_prev = self.create_white_icon(QStyle.StandardPixmap.SP_MediaSkipBackward)
        icon_next = self.create_white_icon(QStyle.StandardPixmap.SP_MediaSkipForward)
        
        self.btn_prev = QPushButton()
        self.btn_prev.setObjectName("PlaybackButton")
        self.btn_prev.setIcon(icon_prev)
        self.btn_prev.setFixedSize(40, 40)
        self.btn_prev.clicked.connect(self.prev_frame)
        
        self.btn_play = QPushButton()
        self.btn_play.setObjectName("PlaybackButton")
        self.btn_play.setIcon(icon_play)
        self.btn_play.setFixedSize(50, 40)
        self.btn_play.clicked.connect(self.toggle_playback)
        self.btn_play.setEnabled(False)
        
        self.btn_next = QPushButton()
        self.btn_next.setObjectName("PlaybackButton")
        self.btn_next.setIcon(icon_next)
        self.btn_next.setFixedSize(40, 40)
        self.btn_next.clicked.connect(self.next_frame)
        
        # Loop Checkbox
        self.loop_cb = QCheckBox("Loop")
        self.loop_cb.setChecked(True)
        
        # FPS Controls
        fps_layout = QHBoxLayout()
        fps_layout.setSpacing(5)
        lbl_fps = QLabel("FPS:")
        
        self.btn_fps_dec = QPushButton()
        self.btn_fps_dec.setObjectName("PlaybackButton")
        self.btn_fps_dec.setIcon(self.create_symbol_icon("-"))
        self.btn_fps_dec.setFixedSize(40, 40)
        self.btn_fps_dec.clicked.connect(self.decrement_fps)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setObjectName("FPSBox")
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(12)
        self.fps_spin.setFixedWidth(80)
        self.fps_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_spin.valueChanged.connect(self.update_timer_interval)
        
        self.btn_fps_inc = QPushButton()
        self.btn_fps_inc.setObjectName("PlaybackButton")
        self.btn_fps_inc.setIcon(self.create_symbol_icon("+"))
        self.btn_fps_inc.setFixedSize(40, 40)
        self.btn_fps_inc.clicked.connect(self.increment_fps)
        
        fps_layout.addWidget(lbl_fps)
        fps_layout.addWidget(self.btn_fps_dec)
        fps_layout.addWidget(self.fps_spin)
        fps_layout.addWidget(self.btn_fps_inc)
        
        # Add Frames / Delete Frames
        action_layout = QHBoxLayout()
        self.btn_add_frames = QPushButton("Add Frames")
        self.btn_add_frames.clicked.connect(self.add_frames)
        self.btn_add_frames.setEnabled(False)
        
        self.btn_del_frames = QPushButton("Delete Frame(s)")
        self.btn_del_frames.setObjectName("DestructiveButton")
        self.btn_del_frames.clicked.connect(self.delete_selected_frames)
        self.btn_del_frames.setEnabled(False)
        self.btn_del_frames.setToolTip("Permanently deletes selected frame files from disk")
        
        self.btn_edit_frame = QPushButton("Edit Frame")
        self.btn_edit_frame.clicked.connect(self.open_editor)
        self.btn_edit_frame.setEnabled(False)
        
        controls_layout.addWidget(self.btn_prev)
        controls_layout.addWidget(self.btn_play)
        controls_layout.addWidget(self.btn_next)
        controls_layout.addWidget(self.loop_cb)
        controls_layout.addSpacing(15)
        controls_layout.addLayout(fps_layout)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_add_frames)
        controls_layout.addWidget(self.btn_del_frames)
        controls_layout.addWidget(self.btn_edit_frame)
        
        center_layout.addLayout(controls_layout)
        
        # Frame Strip
        self.frame_list_widget = QListWidget()
        self.frame_list_widget.setFlow(QListWidget.Flow.LeftToRight)
        self.frame_list_widget.setFixedHeight(100)
        self.frame_list_widget.setIconSize(QSize(80, 80))
        self.frame_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        center_layout.addWidget(self.frame_list_widget, 1)

        layout.addWidget(center_panel, 3) # Stretch 3

    def show_context_menu(self, pos):
        item = self.anim_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.anim_list.editItem(item))
            menu.addAction(rename_action)
            menu.exec(self.anim_list.mapToGlobal(pos))
    
    def increment_fps(self):
        self.fps_spin.setValue(self.fps_spin.value() + 1)

    def decrement_fps(self):
        self.fps_spin.setValue(self.fps_spin.value() - 1)


    def create_animation(self):
        # Unique name
        base_name = "New Animation"
        count = 1
        name = base_name
        while name in self.animations:
            name = f"{base_name} {count}"
            count += 1
            
        self.animations[name] = []
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.anim_list.addItem(item)
        self.anim_list.setCurrentItem(item)

    def import_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with Images")
        if not folder_path:
            return
            
        # Use folder name as animation name
        folder_name = os.path.basename(folder_path)
        base_name = folder_name
        count = 1
        name = base_name
        while name in self.animations:
            name = f"{base_name} {count}"
            count += 1
            
        # Collect images
        valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
        images = []
        try:
            for f in os.listdir(folder_path):
                if os.path.splitext(f)[1].lower() in valid_exts:
                    images.append(os.path.join(folder_path, f))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read folder: {e}")
            return
            
        if not images:
            QMessageBox.warning(self, "No Images", "No valid images found in selected folder.")
            return
            
        images.sort()
        
        # Create Animation
        self.animations[name] = images
        item = QListWidgetItem(name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.anim_list.addItem(item)
        self.anim_list.setCurrentItem(item)

    def on_anim_renamed(self, item):
        new_name = item.text()
        
        # Find old name? 
        # Since we use the item itself as the key source in some design, but here we store in dict.
        # Problem: We don't know the OLD name easily unless we tracked it.
        # Solution: Rebuild dict or track rename.
        # Simpler approach: We need to update the key in self.animations.
        # But `itemChanged` fires AFTER change.
        # To fix this robustly, we'd need to store the name in UserRole or similar.
        
        # ACTUALLY: Let's do a reverse lookup or better yet, store name in data.
        old_name = item.data(Qt.ItemDataRole.UserRole)
        
        if old_name is None: 
            # First time (creation), just set it
            item.setData(Qt.ItemDataRole.UserRole, new_name)
            return

        if old_name == new_name:
            return
            
        if new_name in self.animations:
            QMessageBox.warning(self, "Name Exists", "Animation name already exists. Reverting.")
            item.setText(old_name)
            return
            
        # Migrate data
        self.animations[new_name] = self.animations.pop(old_name)
        item.setData(Qt.ItemDataRole.UserRole, new_name)
        
        if self.current_anim_name == old_name:
            self.current_anim_name = new_name

    def delete_animation(self):
        row = self.anim_list.currentRow()
        if row >= 0:
            item = self.anim_list.takeItem(row)
            name = item.text()
            if name in self.animations:
                del self.animations[name]
            
            self.current_anim_name = None
            self.current_frames = []
            self.preview_label.clear()
            self.preview_label.setText("Select an animation")
            self.frame_list_widget.clear()
            self.btn_add_frames.setEnabled(False)
            self.btn_play.setEnabled(False)
            self.btn_del_frames.setEnabled(False)

    def on_anim_selected(self, current, previous):
        if not current:
            return
            
        # Ensure we capture name correctly (might need to set UserRole if it's new)
        self.current_anim_name = current.text()
        if current.data(Qt.ItemDataRole.UserRole) is None:
             current.setData(Qt.ItemDataRole.UserRole, self.current_anim_name)
             
        self.current_frames = self.animations.get(self.current_anim_name, [])
        
        # Enable controls
        self.btn_add_frames.setEnabled(True)
        self.btn_del_frames.setEnabled(True)
        self.btn_edit_frame.setEnabled(True)
        self.btn_play.setEnabled(len(self.current_frames) > 0)
        
        # Refresh Frame Strip
        self.frame_list_widget.clear()
        for path in self.current_frames:
            icon = QIcon(path)
            self.frame_list_widget.addItem(QListWidgetItem(icon, ""))
            
        # Show first frame
        if self.current_frames:
            self.current_frame_index = 0
            self.show_frame(0)
        else:
            self.preview_label.clear()
            self.preview_label.setText("No frames loaded")

    def add_frames(self):
        if not self.current_anim_name:
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Frame Images", 
            "", 
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if files:
            files.sort()
            self.current_frames.extend(files)
            self.animations[self.current_anim_name] = self.current_frames
            
            # Refresh list
            for f in files:
                icon = QIcon(f)
                self.frame_list_widget.addItem(QListWidgetItem(icon, ""))
                
            self.btn_play.setEnabled(True)
            if len(self.current_frames) == len(files): # First frames added
                self.show_frame(0)

    def delete_selected_frames(self):
        selected_items = self.frame_list_widget.selectedItems()
        if not selected_items:
            return
            
        count = len(selected_items)
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to PERMANENTLY DELETE {count} file(s) from your disk?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # We need indices to remove from self.current_frames correctly
        # Since standard list widget doesn't give indices easily, we iterate rows
        rows_to_delete = []
        for item in selected_items:
            rows_to_delete.append(self.frame_list_widget.row(item))
            
        rows_to_delete.sort(reverse=True) # Delete from end to avoid index shift issues
        
        for row in rows_to_delete:
            file_path = self.current_frames[row]
            
            # 1. Delete from Disk
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
                
            # 2. Remove from List in memory
            self.current_frames.pop(row)
            
            # 3. Remove from UI
            self.frame_list_widget.takeItem(row)
            
        # Update animations dict
        self.animations[self.current_anim_name] = self.current_frames
        
        # Reset Preview
        if self.current_frames:
            self.current_frame_index = 0
            self.show_frame(0)
        else:
            self.preview_label.clear()
            self.preview_label.setText("No frames left")
            self.btn_play.setEnabled(False)

    def toggle_playback(self):
        if self.is_playing:
            self.timer.stop()
            self.btn_play.setIcon(self.icon_play_cached)
            self.is_playing = False
        else:
            if not self.current_frames:
                return
            
            # Disable editing tools during playback
            # (Editor is now modal, so this is handled naturally)
            
            self.timer.start(int(1000 / self.fps_spin.value()))
            self.btn_play.setIcon(self.icon_pause)
            self.is_playing = True

    def update_timer_interval(self):
        if self.is_playing:
            self.timer.setInterval(int(1000 / self.fps_spin.value()))

    def show_next_frame(self):
        if not self.current_frames:
            self.timer.stop()
            return
            
        next_idx = self.current_frame_index + 1
        
        if next_idx >= len(self.current_frames):
            if self.loop_cb.isChecked():
                next_idx = 0
            else:
                self.timer.stop()
                self.is_playing = False
                self.btn_play.setIcon(self.icon_play_cached)
                return

        self.current_frame_index = next_idx
        self.show_frame(self.current_frame_index)

    def prev_frame(self):
        if not self.current_frames: return
        self.timer.stop()
        self.is_playing = False
        self.btn_play.setIcon(self.icon_play_cached)
        
        self.current_frame_index = (self.current_frame_index - 1) % len(self.current_frames)
        self.show_frame(self.current_frame_index)

    def next_frame(self):
        if not self.current_frames: return
        self.timer.stop()
        self.is_playing = False
        self.btn_play.setIcon(self.icon_play_cached)
        
        self.current_frame_index = (self.current_frame_index + 1) % len(self.current_frames)
        self.show_frame(self.current_frame_index)

    def show_frame(self, index):
        if 0 <= index < len(self.current_frames):
            path = self.current_frames[index]
            
            pix = QPixmap(path)
            # Scale to fit
            scaled = pix.scaled(
                self.preview_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
            
            # Update Filename Label
            self.lbl_filename.setText(os.path.basename(path))
            
            # Highlight in strip
            self.frame_list_widget.setCurrentRow(index)

    def open_editor(self):
        if not self.current_frames or self.current_frame_index >= len(self.current_frames):
            return
            
        path = self.current_frames[self.current_frame_index]
        from .frame_editor_dialog import FrameEditorDialog
        
        dlg = FrameEditorDialog(path, self)
        if dlg.exec():
            # Refresh frame if saved
            self.show_frame(self.current_frame_index)
            # Update thumbnail
            self.frame_list_widget.item(self.current_frame_index).setIcon(QIcon(path))


