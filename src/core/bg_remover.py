from rembg import remove, new_session
from PIL import Image
import numpy as np
import io

class BackgroundRemover:
    _sessions = {}

    @classmethod
    def get_session(cls, model_name: str):
        if model_name not in cls._sessions:
            cls._sessions[model_name] = new_session(model_name)
        return cls._sessions[model_name]

    @classmethod
    def remove_background(cls, image: Image.Image, 
                         alpha_matting: bool = False, 
                         alpha_matting_foreground_threshold: int = 240, 
                         alpha_matting_background_threshold: int = 10,
                         model_name: str = "u2net") -> Image.Image:
        """
        Removes background from a PIL Image using rembg.
        Args:
            image: Input PIL Image
            alpha_matting: Enable alpha matting for better edges (slower)
            alpha_matting_foreground_threshold: Threshold for foreground
            alpha_matting_background_threshold: Threshold for background
            model_name: Name of the model to use (u2net, isnet-anime, etc.)
        """
        session = cls.get_session(model_name)
        
        return remove(
            image, 
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold
        )

    @staticmethod
    def cv2_to_pil(cv_image) -> Image.Image:
        """
        Converts an OpenCV image (BGR) to a PIL Image (RGB).
        """
        # OpenCV uses BGR, PIL uses RGB
        import cv2
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)

