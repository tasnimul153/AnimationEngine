from PyQt6.QtCore import QThread, pyqtSignal, QObject
from src.core.video_processor import VideoLoader
from src.core.bg_remover import BackgroundRemover
from src.core.image_utils import SpriteProcessor
from PIL import Image, ImageQt
import os
import time

class ProcessingWorker(QThread):
    progress_updated = pyqtSignal(int, str) # value (0-100), status message
    frame_processed = pyqtSignal(object) # QImage for preview
    log_message = pyqtSignal(str)
    finished_processing = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        self._is_running = True

    def process_single_frame(self, pil_image, frames_dir, filename):
        # Helper to process one image
        alpha_matting = self.settings.get('alpha_matting', False)
        fg_thresh = self.settings.get('alpha_matting_foreground_threshold', 240)
        bg_thresh = self.settings.get('alpha_matting_background_threshold', 10)
        model_name = self.settings.get('model_name', "u2net")
        
        no_bg_image = BackgroundRemover.remove_background(
            pil_image, 
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=fg_thresh,
            alpha_matting_background_threshold=bg_thresh,
            model_name=model_name
        )
        
        # QUALITY BOOST: Edge Smoothing
        if self.settings.get('edge_smoothing', False):
            # Default radius 2 is good for most HD content
            no_bg_image = SpriteProcessor.smooth_alpha_edges(no_bg_image, radius=2)
        
        # QUALITY BOOST: Color Residue Cleanup
        if self.settings.get('cleanup_residue', False):
            target_color = self.settings.get('cleanup_color', (255, 255, 255))
            tolerance = self.settings.get('cleanup_tolerance', 30)
            no_bg_image = SpriteProcessor.remove_color_residue(
                no_bg_image, 
                target_color=target_color,
                tolerance=tolerance,
                edge_only=True
            )
        
        if self.settings.get('keep_original_position', False):
            # Do NOT crop. Do NOT resize/anchor (mostly).
            # Save the full frame with BG removed.
            final_image = no_bg_image
        else:
            padding = self.settings.get('padding', 0)
            cropped_image = SpriteProcessor.crop_to_content(no_bg_image, padding=padding)
            
            final_image = cropped_image
            if self.settings.get('use_uniform_size', False):
                target_w = self.settings.get('uniform_width', 512)
                target_h = self.settings.get('uniform_height', 512)
                anchor = self.settings.get('anchor', 'center')
                final_image = SpriteProcessor.apply_anchor_and_resize(
                    cropped_image, 
                    (target_w, target_h), 
                    anchor=anchor
                )
        
        save_path = os.path.join(frames_dir, filename)
        final_image.save(save_path)
        return final_image

    def run(self):
        try:
            input_path = self.settings['video_path']
            output_dir = self.settings['output_dir']
            
            self.log_message.emit(f"Starting processing for: {input_path}")
            
            frames_dir = os.path.join(output_dir, 'frames')
            os.makedirs(frames_dir, exist_ok=True)

            # Check if image or video
            ext = os.path.splitext(input_path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp', '.bmp']:
                # IMAGE MODE
                self.log_message.emit("Detected Image file.")
                original_image = Image.open(input_path)
                
                final_image = self.process_single_frame(original_image, frames_dir, f"processed_{os.path.basename(input_path)}.png")
                
                self.progress_updated.emit(100, f"Processed image")
                self.frame_processed.emit(ImageQt.ImageQt(final_image))
                self.finished_processing.emit()
                self.log_message.emit("Processing complete!")
                return

            # VIDEO MODE
            self.log_message.emit("Detected Video file.")
            loader = VideoLoader(input_path)
            meta = loader.get_metadata()
            self.log_message.emit(f"Video Info: {meta['width']}x{meta['height']} @ {meta['fps']} FPS, {meta['total_frames']} frames")
            
            # Prepare generator
            skip_frames = self.settings.get('skip_frames', 0)
            target_fps = self.settings.get('target_fps', None)
            
            # Estimate total frames to process for progress bar
            if target_fps and meta['fps'] > 0:
                estimated_total = int(meta['duration'] * target_fps)
            else:
                estimated_total = meta['total_frames'] // (skip_frames + 1)
            
            processed_count = 0
            
            for idx, frame in loader.extract_frames(skip_frames=skip_frames, target_fps=target_fps):
                if self.isInterruptionRequested():
                    self.log_message.emit("Processing cancelled by user.")
                    break
                
                pil_image = BackgroundRemover.cv2_to_pil(frame)
                
                filename = f"frame_{processed_count:05d}.png"
                final_image = self.process_single_frame(pil_image, frames_dir, filename)
                
                processed_count += 1
                progress = int((processed_count / estimated_total) * 100) if estimated_total > 0 else 0
                progress = min(progress, 100)
                
                self.progress_updated.emit(progress, f"Processed frame {idx} -> {filename}")
                self.frame_processed.emit(ImageQt.ImageQt(final_image))
                
            loader.release()
            self.finished_processing.emit()
            self.log_message.emit("Processing complete!")
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            self.log_message.emit(f"Error: {str(e)}")
