from PIL import Image, ImageFilter
import statistics

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
