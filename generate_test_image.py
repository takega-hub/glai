
from PIL import Image, ImageDraw
import os

# Убедимся, что директория существует
uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True)

# Создаем простое изображение
img = Image.new('RGB', (100, 100), color = 'red')
d = ImageDraw.Draw(img)
d.text((10,10), "Test Face", fill=(255,255,0))

# Сохраняем изображение
file_path = os.path.join(uploads_dir, "test_face.jpg")
img.save(file_path)

print(f"Test image saved to {file_path}")
