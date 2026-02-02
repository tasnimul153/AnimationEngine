import cv2
import typing

class VideoLoader:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise FileNotFoundError(f"Could not open video file: {video_path}")
            
    def get_metadata(self) -> dict:
        """Returns metadata about the video: fps, total_frames, duration, width, height."""
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps > 0:
            duration = total_frames / fps
        else:
            duration = 0
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        return {
            "fps": fps,
            "total_frames": total_frames,
            "duration": duration,
            "width": width,
            "height": height
        }

    def extract_frames(self, skip_frames: int = 0, target_fps: float = None) -> typing.Generator[typing.Tuple[int, any], None, None]:
        """
        Yields frames from the video.
        
        Args:
            skip_frames: Number of frames to skip strictly (e.g. 1 means extract every 2nd frame).
            target_fps: If set, tries to match this FPS by skipping frames dynamically. Overrides skip_frames if set.
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        source_fps = self.cap.get(cv2.CAP_PROP_FPS)
        if target_fps and source_fps > 0:
            step = source_fps / target_fps
        else:
            step = skip_frames + 1
            
        current_frame_idx = 0.0
        
        while True:
            # If we need to jump ahead significantly, we can use set(), but strictly standard reading is often safer for some formats
            # However, for performance on large skips, set() is better.
            
            # Simple approach: read every frame but only yield if it matches the step
            ret, frame = self.cap.read()
            if not ret:
                break
                
            # If using target_fps, we accumulate "time"
            # If using skip_frames (step is integer >= 1), we check modulo
            
            # Hybrid approach for simplicity and accuracy:
            # We want to yield frames at indices: 0, step, 2*step, ...
            
            # Integer index of the process
            actual_frame_index = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            
            if actual_frame_index >= int(current_frame_idx):
                yield actual_frame_index, frame
                current_frame_idx += step
                
                # Optimization: if step is large (e.g. > 10), seek ahead to save decode time
                # But seeking can be slow on some codecs. keeping it simple for now (sequential read) is robust.
                # If performance is an issue, we can toggle seek.

    def release(self):
        self.cap.release()
