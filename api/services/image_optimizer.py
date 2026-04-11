from PIL import Image
import io

class ImageOptimizerService:
    def __init__(self, quality=85, max_size=(1024, 1024)):
        self.quality = quality
        self.max_size = max_size

    def optimize_image(self, image_bytes: bytes) -> bytes:
        """
        Optimizes an image by resizing and compressing it.
        """
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Resize the image to fit within the max_size, preserving aspect ratio
                img.thumbnail(self.max_size, Image.Resampling.LANCZOS)

                # Save the image to a byte buffer with specified quality
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=self.quality, optimize=True)
                optimized_bytes = buffer.getvalue()
                
                original_size = len(image_bytes) / 1024
                optimized_size = len(optimized_bytes) / 1024
                print(f"--- Image Optimized: {original_size:.2f} KB -> {optimized_size:.2f} KB ---")
                
                return optimized_bytes
        except Exception as e:
            print(f"!!! Could not optimize image: {e} !!!")
            # If optimization fails, return the original bytes to not break the flow
            return image_bytes
