import os
import io
from PIL import Image
from config import DPI, SCALE_FACTOR

def mm_to_px(mm):
    # конвертирует миллиметры в пиксели на основе заданного dpi
    return int(mm * DPI / 25.4)

def px_to_mm(px):
    # конвертирует пиксели обратно в миллиметры
    return px * 25.4 / DPI

def extract_image_from_studio3(file_path):
    # извлекает самое большое png из .studio3 файла
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        png_header = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        iend_chunk = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'
        
        largest_data = None
        max_size = 0
        offset = 0
        
        while True:
            start = data.find(png_header, offset)
            if start == -1:
                break
            end_marker = data.find(iend_chunk, start)
            if end_marker == -1:
                offset = start + 1
                continue
            end = end_marker + 8
            if end - start > max_size:
                max_size = end - start
                largest_data = data[start:end]
            offset = end
        
        if largest_data:
            return Image.open(io.BytesIO(largest_data))
        return None
    except Exception as e:
        print(f"  ОШИБКА extraction: {e}")
        return None

def load_image(file_path):
    # загружает изображение и масштабирует его
    img = None
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.studio3':
            img = extract_image_from_studio3(file_path)
        else:
            img = Image.open(file_path)
    except Exception as e:
        print(f"  ОШИБКА загрузки {file_path}: {e}")
        return None

    if img is None:
        return None

    if SCALE_FACTOR != 1.0:
        new_w = int(img.width * SCALE_FACTOR)
        new_h = int(img.height * SCALE_FACTOR)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    return img
