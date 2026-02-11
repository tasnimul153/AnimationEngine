from PIL import Image, ImageFilter
import numpy as np

class SpriteProcessor:
    @staticmethod
    def crop_to_content(image: Image.Image, padding: int = 0) -> Image.Image:
        """
        Crops the image to the bounding box of non-zero alpha pixels.
        Adds optional padding.
        """
        bbox = image.getbbox()
        if not bbox:
            return image  # Empty image
            
        # bbox is (left, upper, right, lower)
        left, upper, right, lower = bbox
        
        # Apply padding
        width, height = image.size
        left = max(0, left - padding)
        upper = max(0, upper - padding)
        right = min(width, right + padding)
        lower = min(height, lower + padding)
        
        return image.crop((left, upper, right, lower))

    @staticmethod
    def smooth_alpha_edges(image: Image.Image, radius: int = 2) -> Image.Image:
        """
        Applies a Gaussian Blur to the alpha channel to soften jagged edges.
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            
        # Separate alpha
        r, g, b, a = image.split()
        
        # Blur alpha
        # Use a small radius to just soften aliasing
        a_blurred = a.filter(ImageFilter.GaussianBlur(radius=radius))
        
        # Combine back
        return Image.merge('RGBA', (r, g, b, a_blurred))

    @staticmethod
    def remove_color_residue(image: Image.Image, target_color: tuple = (255, 255, 255), 
                              tolerance: int = 30, edge_only: bool = True) -> Image.Image:
        """
        Removes residual pixels that are similar to a target background color.
        Useful for cleaning up white/colored backgrounds the AI missed.
        
        Args:
            image: PIL Image in RGBA mode
            target_color: RGB tuple of the background color to remove (default white)
            tolerance: How similar a pixel must be to be removed (0-255)
            edge_only: If True, only removes pixels near transparent areas (safer)
        """
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        arr = np.array(image)
        rgb = arr[:, :, :3].astype(np.float32)
        alpha = arr[:, :, 3]
        
        # Calculate color distance from target
        target = np.array(target_color, dtype=np.float32)
        distance = np.sqrt(np.sum((rgb - target) ** 2, axis=2))
        
        # Mask of pixels similar to target color
        similar_mask = distance < tolerance
        
        if edge_only:
            # Only affect pixels near transparent edges
            from scipy import ndimage
            # Dilate the transparent region to find edge pixels
            transparent_mask = alpha < 128
            dilated = ndimage.binary_dilation(transparent_mask, iterations=3)
            edge_region = dilated & ~transparent_mask
            similar_mask = similar_mask & edge_region
        
        # Set matching pixels to transparent
        arr[similar_mask, 3] = 0
        
        return Image.fromarray(arr)

    @staticmethod
    def apply_anchor_and_resize(image: Image.Image, target_size: tuple[int, int], anchor: str = 'center') -> Image.Image:
        """
        Places the image onto a canvas of target_size.
        anchor: 'center' or 'bottom_center'
        """
        canvas = Image.new("RGBA", target_size, (0, 0, 0, 0))
        
        img_w, img_h = image.size
        canvas_w, canvas_h = target_size
        
        if anchor == 'center':
            x = (canvas_w - img_w) // 2
            y = (canvas_h - img_h) // 2
        elif anchor == 'bottom_center':
            x = (canvas_w - img_w) // 2
            y = canvas_h - img_h
        else:
            # Default to center
            x = (canvas_w - img_w) // 2
            y = (canvas_h - img_h) // 2
            
        canvas.paste(image, (x, y), image)
        return canvas

class SpriteSheetPacker:
    # Placeholder for future implementation if needed
    pass

