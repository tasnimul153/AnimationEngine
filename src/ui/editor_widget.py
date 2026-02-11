import cv2
import numpy as np
import os
from PyQt6.QtWidgets import QLabel, QMessageBox
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QPen, QBrush, QCursor

class InteractivePreview(QLabel):
    # Tool Enums
    TOOL_NONE = 0
    TOOL_WAND = 1
    TOOL_RECT = 2
    TOOL_LASSO = 3
    TOOL_ERASER = 4
    
    # Signals
    file_changed = pyqtSignal()
    zoom_changed = pyqtSignal(float)
    cursor_moved = pyqtSignal(int, int) # x, y in image coords

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # State
        self.current_image_path = None
        self.cv_image = None
        self.original_pixmap = None
        
        self.active_tool = self.TOOL_NONE
        self.selection_mask = None
        
        # Geometry
        self.draw_rect = QRect()
        self.base_scale = 1.0
        self.zoom_level = 1.0
        
        # Pan
        self.pan_offset = QPointF(0, 0)
        self.is_panning = False
        self.pan_start = QPoint()
        self.space_held = False
        
        # Tools State
        self.rect_start = None
        self.rect_current = None
        self.lasso_points = []
        self.eraser_last_pos = None
        
        # Settings
        self.tolerance = 20
        self.brush_size = 15
        
        # Undo
        self.undo_stack = []
        self.max_undo = 5
        
        # Overlay
        self.wand_overlay = None
        
        # Checkerboard
        self.checker_pixmap = self._create_checkerboard(16)

    def _create_checkerboard(self, size):
        img = QImage(size*2, size*2, QImage.Format.Format_RGB32)
        c1, c2 = QColor("#3a3a3a"), QColor("#2a2a2a")
        for y in range(2):
            for x in range(2):
                color = c1 if (x + y) % 2 == 0 else c2
                for py in range(size):
                    for px in range(size):
                        img.setPixelColor(x*size + px, y*size + py, color)
        return QPixmap.fromImage(img)

    def set_tool(self, tool_id):
        self.active_tool = tool_id
        self.selection_mask = None
        self.wand_overlay = None
        self.rect_start = None
        self.lasso_points = []
        self.update()

    def set_tolerance(self, value):
        self.tolerance = max(1, min(value, 100))
        
    def set_brush_size(self, value):
        self.brush_size = max(1, min(value, 100))
        
    def set_image(self, path):
        self.current_image_path = path
        self.selection_mask = None
        self.wand_overlay = None
        self.rect_start = None
        self.lasso_points = []
        self.undo_stack = []
        self.zoom_level = 1.0
        self.pan_offset = QPointF(0, 0)
        
        if path and os.path.exists(path):
            self.cv_image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if self.cv_image is None: return 
            
            if len(self.cv_image.shape) == 2:
                self.cv_image = cv2.cvtColor(self.cv_image, cv2.COLOR_GRAY2BGRA)
            elif self.cv_image.shape[2] == 3:
                self.cv_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2BGRA)
                
            self._update_pixmap()
        else:
            self.cv_image = None
            self.original_pixmap = None
            
        self.update()

    def _update_pixmap(self):
        if self.cv_image is None: return
        rgb_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGRA2RGBA)
        h, w, ch = rgb_image.shape
        q_img = QImage(rgb_image.data, w, h, w*ch, QImage.Format.Format_RGBA8888)
        self.original_pixmap = QPixmap.fromImage(q_img.copy())

    # --- Zoom ---
    def zoom_in(self):
        self.zoom_level = min(self.zoom_level * 1.25, 10.0)
        self.zoom_changed.emit(self.zoom_level)
        self.update()
        
    def zoom_out(self):
        self.zoom_level = max(self.zoom_level / 1.25, 0.1)
        self.zoom_changed.emit(self.zoom_level)
        self.update()
        
    def zoom_reset(self):
        self.zoom_level = 1.0
        self.pan_offset = QPointF(0, 0)
        self.zoom_changed.emit(self.zoom_level)
        self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # --- Undo ---
    def save_state(self):
        if self.cv_image is None: return
        self.undo_stack.append(self.cv_image.copy())
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
            
    def undo(self):
        if not self.undo_stack: return
        self.cv_image = self.undo_stack.pop()
        self._update_pixmap()
        self.selection_mask = None
        self.wand_overlay = None
        self.update()

    # --- Paint ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#1a1a1a"))
        
        if self.original_pixmap is None:
            painter.setPen(QColor("#666"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Frame Selected")
            return
            
        w_widget = self.width()
        h_widget = self.height()
        w_img = self.original_pixmap.width()
        h_img = self.original_pixmap.height()
        
        self.base_scale = min(w_widget / w_img, h_widget / h_img)
        effective_scale = self.base_scale * self.zoom_level
        
        draw_w = int(w_img * effective_scale)
        draw_h = int(h_img * effective_scale)
        
        # Apply pan offset
        off_x = int((w_widget - draw_w) / 2 + self.pan_offset.x())
        off_y = int((h_widget - draw_h) / 2 + self.pan_offset.y())
        
        self.draw_rect = QRect(off_x, off_y, draw_w, draw_h)
        
        # Checkerboard behind image
        painter.save()
        painter.setClipRect(self.draw_rect)
        for y in range(off_y, off_y + draw_h, 32):
            for x in range(off_x, off_x + draw_w, 32):
                painter.drawPixmap(x, y, self.checker_pixmap)
        painter.restore()
        
        # Draw image
        painter.drawPixmap(self.draw_rect, self.original_pixmap)
        
        # Overlay
        if self.wand_overlay is not None:
            scaled_overlay = self.wand_overlay.scaled(
                self.draw_rect.size(), 
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            )
            painter.setOpacity(0.5)
            painter.drawPixmap(self.draw_rect.topLeft(), scaled_overlay)
            painter.setOpacity(1.0)
             
        # Active tools
        if self.active_tool == self.TOOL_RECT and self.rect_start and self.rect_current:
            painter.setPen(QPen(QColor("#00FF00"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(0, 255, 0, 50)))
            r = QRect(self.rect_start, self.rect_current).normalized()
            painter.drawRect(r)
            
        elif self.active_tool == self.TOOL_LASSO and self.lasso_points:
            painter.setPen(QPen(QColor("#00FF00"), 2, Qt.PenStyle.SolidLine))
            for i in range(len(self.lasso_points) - 1):
                painter.drawLine(self.lasso_points[i], self.lasso_points[i+1])

    def _widget_to_image(self, pos):
        if self.cv_image is None or self.draw_rect.isEmpty():
            return None, None
        effective_scale = self.base_scale * self.zoom_level
        img_x = int((pos.x() - self.draw_rect.x()) / effective_scale)
        img_y = int((pos.y() - self.draw_rect.y()) / effective_scale)
        h, w = self.cv_image.shape[:2]
        img_x = max(0, min(img_x, w-1))
        img_y = max(0, min(img_y, h-1))
        return img_x, img_y

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_held = True
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selection()
        elif event.key() == Qt.Key.Key_Escape:
            self.selection_mask = None
            self.wand_overlay = None
            self.update()
        elif event.key() == Qt.Key.Key_I and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.invert_selection()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.undo()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.space_held = False
            self.is_panning = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, event):
        # Pan with middle mouse or space+left
        if event.button() == Qt.MouseButton.MiddleButton or (self.space_held and event.button() == Qt.MouseButton.LeftButton):
            self.is_panning = True
            self.pan_start = event.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return
            
        if self.cv_image is None or not self.draw_rect.contains(event.pos()):
            return
            
        img_x, img_y = self._widget_to_image(event.pos())
        if img_x is None: return
        
        if self.active_tool == self.TOOL_WAND:
            self.do_magic_wand(img_x, img_y)
        elif self.active_tool == self.TOOL_RECT:
            self.rect_start = event.pos()
            self.rect_current = event.pos()
        elif self.active_tool == self.TOOL_LASSO:
            self.lasso_points = [event.pos()]
        elif self.active_tool == self.TOOL_ERASER:
            self.save_state()
            self.eraser_last_pos = (img_x, img_y)
            self._erase_at(img_x, img_y)

    def mouseMoveEvent(self, event):
        # Emit cursor position
        if self.cv_image is not None and self.draw_rect.contains(event.pos()):
            img_x, img_y = self._widget_to_image(event.pos())
            if img_x is not None:
                self.cursor_moved.emit(img_x, img_y)
        
        # Pan
        if self.is_panning:
            delta = event.pos() - self.pan_start
            self.pan_offset += QPointF(delta.x(), delta.y())
            self.pan_start = event.pos()
            self.update()
            return
            
        if self.active_tool == self.TOOL_RECT and self.rect_start:
            self.rect_current = event.pos()
            self.update()
        elif self.active_tool == self.TOOL_LASSO and self.lasso_points:
            self.lasso_points.append(event.pos())
            self.update()
        elif self.active_tool == self.TOOL_ERASER and self.eraser_last_pos:
            img_x, img_y = self._widget_to_image(event.pos())
            if img_x is not None:
                self._erase_at(img_x, img_y)
                self.eraser_last_pos = (img_x, img_y)

    def mouseReleaseEvent(self, event):
        if self.is_panning:
            self.is_panning = False
            self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor if self.space_held else Qt.CursorShape.ArrowCursor))
            return
            
        if self.active_tool == self.TOOL_RECT and self.rect_start:
            self.finalize_rect_selection()
        elif self.active_tool == self.TOOL_LASSO and self.lasso_points:
            self.finalize_lasso_selection()
        elif self.active_tool == self.TOOL_ERASER:
            self.eraser_last_pos = None

    def _erase_at(self, x, y):
        if self.cv_image is None: return
        h, w = self.cv_image.shape[:2]
        r = self.brush_size // 2
        y1, y2 = max(0, y-r), min(h, y+r)
        x1, x2 = max(0, x-r), min(w, x+r)
        
        for py in range(y1, y2):
            for px in range(x1, x2):
                if (px - x)**2 + (py - y)**2 <= r**2:
                    self.cv_image[py, px, 3] = 0
        
        self._update_pixmap()
        self.update()

    def do_magic_wand(self, seed_x, seed_y):
        if self.cv_image is None: return
        h, w = self.cv_image.shape[:2]
        mask = np.zeros((h+2, w+2), np.uint8)
        
        tol = self.tolerance
        loDiff = (tol, tol, tol)
        upDiff = (tol, tol, tol)
        flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE
        
        src_img = np.ascontiguousarray(self.cv_image[:, :, :3])
        cv2.floodFill(src_img, mask, (seed_x, seed_y), (0,0,0), loDiff, upDiff, flags)
        self.selection_mask = mask[1:-1, 1:-1]
        self.update_overlay()

    def finalize_rect_selection(self):
        if not self.rect_start or not self.rect_current: return
        wr = QRect(self.rect_start, self.rect_current).normalized().intersected(self.draw_rect)
        if wr.isEmpty(): return
        
        effective_scale = self.base_scale * self.zoom_level
        ix = int((wr.x() - self.draw_rect.x()) / effective_scale)
        iy = int((wr.y() - self.draw_rect.y()) / effective_scale)
        iw = int(wr.width() / effective_scale)
        ih = int(wr.height() / effective_scale)
        
        h, w = self.cv_image.shape[:2]
        self.selection_mask = np.zeros((h, w), dtype=np.uint8)
        self.selection_mask[iy:iy+ih, ix:ix+iw] = 255
        
        self.rect_start = None
        self.update_overlay()
        
    def finalize_lasso_selection(self):
        if not self.lasso_points: return
        
        effective_scale = self.base_scale * self.zoom_level
        pts = []
        for p in self.lasso_points:
            ix = int((p.x() - self.draw_rect.x()) / effective_scale)
            iy = int((p.y() - self.draw_rect.y()) / effective_scale)
            pts.append([ix, iy])
            
        pts = np.array([pts], dtype=np.int32)
        h, w = self.cv_image.shape[:2]
        self.selection_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(self.selection_mask, pts, 255)
        
        self.lasso_points = []
        self.update_overlay()

    def update_overlay(self):
        if self.selection_mask is None: return
        h, w = self.selection_mask.shape
        overlay_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        overlay_rgba[self.selection_mask == 255] = [255, 0, 0, 100]
        q_img = QImage(overlay_rgba.data, w, h, w*4, QImage.Format.Format_RGBA8888)
        self.wand_overlay = QPixmap.fromImage(q_img.copy())
        self.update()

    def invert_selection(self):
        if self.selection_mask is None: return
        self.selection_mask = 255 - self.selection_mask
        self.update_overlay()

    def delete_selection(self):
        if self.selection_mask is None or self.cv_image is None: return
        
        self.save_state()
        self.cv_image[self.selection_mask == 255, 3] = 0
        self._update_pixmap()
        
        self.selection_mask = None
        self.wand_overlay = None
        self.update()
        
    def save_to_disk(self):
        if self.cv_image is None or not self.current_image_path: return False
        try:
            cv2.imwrite(self.current_image_path, self.cv_image)
            self.file_changed.emit()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save: {e}")
            return False
