"""
генератор раскладки закладок для двусторонней печати на принтере с односторонней печатью.
скрипт автоматически размещает изображения на листе а4, учитывая отступы и поля.
для обратной стороны генерируется зеркально отраженный макет, чтобы при печати
на второй стороне листа изображения точно совпадали.
поддерживает файлы .png, .jpg, и .studio3.

by @pingalinux
"""

import os
import io
from PIL import Image, ImageOps

# размеры листа а4 в миллиметрах
PAPER_WIDTH_MM = 210
PAPER_HEIGHT_MM = 297

# качество печати (точек на дюйм), стандартное для полиграфии
DPI = 300

# отступ от края страницы (1.5 см = 15 мм)
MARGIN_MM = 15
# расстояние между изображениями на листе (1.5 см = 15 мм)
SPACING_MM = 15

# коэффициент масштабирования изображений (1.0 = исходный размер, 1.35 = увеличение на 35%)
SCALE_FACTOR = 1.0

# =============================================================================
# ВЫЧИСЛЕНИЯ
# =============================================================================

def mm_to_px(mm):
    # конвертирует миллиметры в пиксели на основе заданного dpi
    return int(mm * DPI / 25.4)

def px_to_mm(px):
    # конвертирует пиксели обратно в миллиметры для отображения информации
    return px * 25.4 / DPI

# вычисляем размеры страницы и отступов в пикселях
PAGE_WIDTH = mm_to_px(PAPER_WIDTH_MM)
PAGE_HEIGHT = mm_to_px(PAPER_HEIGHT_MM)
MARGIN = mm_to_px(MARGIN_MM)
SPACING = mm_to_px(SPACING_MM)

# определяем пути к папкам относительно текущего скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "input")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")

# =============================================================================
# ФУНКЦИИ
# =============================================================================

def extract_image_from_studio3(file_path):
    # извлекает самое большое png из .studio3 файла.
    # сканирует файл на наличие заголовков png, находит самый большой блок данных
    # и возвращает его как объект изображения.
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # сигнатура заголовка png файла (8 байт)
        png_header = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        # сигнатура конца png файла (8 байт)
        iend_chunk = b'\x49\x45\x4E\x44\xAE\x42\x60\x82'
        
        largest_data = None
        max_size = 0
        offset = 0
        
        # проходим по всему файлу в поисках блоков png
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
        
        # если нашли данные, создаем изображение
        if largest_data:
            return Image.open(io.BytesIO(largest_data))
        return None
    except Exception as e:
        print(f"  ОШИБКА: {e}")
        return None


def load_image(file_path):
    # загружает изображение в зависимости от расширения файла (.studio3, .png, .jpg).
    # также выполняет масштабирование изображения, если задан scale_factor.
    img = None
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.studio3':
            img = extract_image_from_studio3(file_path)
        else:
            img = Image.open(file_path)
    except Exception as e:
        print(f"  ОШИБКА: {e}")
        return None

    if img is None:
        return None

    # применяем масштабирование если коэффициент отличается от 1.0
    if SCALE_FACTOR != 1.0:
        new_w = int(img.width * SCALE_FACTOR)
        new_h = int(img.height * SCALE_FACTOR)
        # используем lanczos для сохранения качества при ресайзе
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    return img


def main():
    # создаем необходимые папки, если их еще нет
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"Создана папка: {INPUT_FOLDER}")
        print("Положи туда файлы и запусти снова.")
        return
    
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    # удаляем старые сгенерированные файлы из папки вывода, чтобы не путаться
    for f in os.listdir(OUTPUT_FOLDER):
        if f.startswith('layout_'):
            os.remove(os.path.join(OUTPUT_FOLDER, f))
    
    # ищем все поддерживаемые файлы изображений в папке input
    files = sorted([
        f for f in os.listdir(INPUT_FOLDER)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.studio3'))
    ])
    
    if not files:
        print(f"Нет файлов в '{INPUT_FOLDER}'")
        return
    
    print(f"Найдено файлов: {len(files)}")
    print(f"Страница: {PAPER_WIDTH_MM}x{PAPER_HEIGHT_MM}mm @ {DPI} DPI")
    print(f"Поля: {MARGIN_MM}mm, отступ между: {SPACING_MM}mm")
    print()
    
    # загружаем все изображения в память
    images = []
    for filename in files:
        print(f"  Загрузка: {filename}")
        img = load_image(os.path.join(INPUT_FOLDER, filename))
        if img is None:
            print(f"    ПРОПУЩЕНО")
            continue
        
        # конвертируем изображение в формат rgba для поддержки прозрачности
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        w, h = img.size
        print(f"    Размер: {w}x{h}px ({px_to_mm(w):.1f}x{px_to_mm(h):.1f}mm)")
        images.append((filename, img))
    
    if not images:
        print("Нет изображений для обработки")
        return
    
    print()
    
    # раскладываем изображения по страницам
    sheets = []  # список страниц. каждая страница - это список строк.
                 # строка - это список кортежей (имя_файла, изображение)
    
    current_page_rows = []
    current_page_height = 0
    
    current_row = []
    current_row_width = 0
    current_row_height = 0
    
    def finalize_row(row, width, height):
        # вспомогательная функция для упаковки данных строки
        return {'items': row, 'width': width, 'height': height}

    for filename, img in images:
        w, h = img.size
        
        if w > PAGE_WIDTH - 2 * MARGIN:
            print(f"  Внимание: {filename} шире страницы! Пропуск.")
            continue

        # проверяем, помещается ли изображение в текущую строку
        if not current_row:
            current_row.append((filename, img))
            current_row_width = w
            current_row_height = h
        else:
            new_width = current_row_width + SPACING + w
            if new_width <= PAGE_WIDTH - 2 * MARGIN:
                # добавляем в строку, если место есть
                current_row.append((filename, img))
                current_row_width = new_width
                current_row_height = max(current_row_height, h)
            else:
                # строка заполнена, финализируем её
                row_data = finalize_row(current_row, current_row_width, current_row_height)
                
                # проверяем, помещается ли новая строка на текущую страницу по высоте
                new_page_h = current_page_height
                if current_page_rows:
                    new_page_h += SPACING
                new_page_h += row_data['height']
                
                if new_page_h > PAGE_HEIGHT - 2 * MARGIN:
                    # страница заполнена, сохраняем её и начинаем новую
                    sheets.append({'rows': current_page_rows, 'total_h': current_page_height})
                    current_page_rows = []
                    current_page_height = 0
                    
                    # добавляем строку как первую на новой странице
                    current_page_rows.append(row_data)
                    current_page_height = row_data['height']
                else:
                    # добавляем строку к текущей странице
                    current_page_rows.append(row_data)
                    if len(current_page_rows) > 1:
                        current_page_height += SPACING
                    current_page_height += row_data['height']
                
                # начинаем новую строку с текущим изображением
                current_row = [(filename, img)]
                current_row_width = w
                current_row_height = h

    # обрабатываем последний оставшийся ряд изображений
    if current_row:
        row_data = finalize_row(current_row, current_row_width, current_row_height)
        
        new_page_h = current_page_height
        if current_page_rows:
            new_page_h += SPACING
        new_page_h += row_data['height']
        
        if new_page_h > PAGE_HEIGHT - 2 * MARGIN:
             # если не влезает, сохраняем текущую страницу и создаем новую для последней строки
             sheets.append({'rows': current_page_rows, 'total_h': current_page_height})
             sheets.append({'rows': [row_data], 'total_h': row_data['height']})
        else:
             # если влезает, добавляем в конец текущей страницы
             if current_page_rows:
                 current_page_height += SPACING
             current_page_height += row_data['height']
             current_page_rows.append(row_data)
             sheets.append({'rows': current_page_rows, 'total_h': current_page_height})
    
    if not sheets:
        print("Не удалось создать листы")
        return
    
    # генерируем итоговые изображения листов и сохраняем их
    print(f"Создаём {len(sheets)} лист(ов) (с ПОЛНЫМ центрированием, прозрачный фон)...")
    print()
    
    for sheet_idx, page_data in enumerate(sheets):
        rows = page_data['rows']
        total_h = page_data['total_h']
        
        # вычисляем начальную координату y для вертикального центрирования всего содержимого на листе
        start_y = (PAGE_HEIGHT - total_h) // 2
        
        # создаем пустые холсты для лицевой и оборотной сторон с прозрачным фоном
        front_page = Image.new('RGBA', (PAGE_WIDTH, PAGE_HEIGHT), (0, 0, 0, 0))
        back_page = Image.new('RGBA', (PAGE_WIDTH, PAGE_HEIGHT), (0, 0, 0, 0))
        
        current_y = start_y
        
        for row in rows:
            # вычисляем начальную координату x для горизонтального центрирования строки
            row_w = row['width']
            start_x = (PAGE_WIDTH - row_w) // 2
            
            x_cursor = start_x
            for filename, img in row['items']:
                # размещаем изображение на лицевой стороне
                front_page.paste(img, (x_cursor, current_y), mask=img)
                
                # для оборотной стороны зеркалим изображение и вычисляем его позицию
                # позиция должна быть зеркальной относительно центра листа
                w, h = img.size
                back_img = ImageOps.mirror(img)
                back_x = PAGE_WIDTH - x_cursor - w
                back_y = current_y
                back_page.paste(back_img, (back_x, back_y), mask=back_img)
                
                print(f"  {filename}")
                print(f"    Y-pos: {current_y} (Page H: {PAGE_HEIGHT}, Content H: {total_h})")
                
                x_cursor += w + SPACING
            
            current_y += row['height'] + SPACING
        
        # сохраняем полученные листы
        sheet_num = sheet_idx + 1
        front_name = f"layout_sheet_{sheet_num:02d}_front.png"
        back_name = f"layout_sheet_{sheet_num:02d}_back.png"
        
        front_page.save(os.path.join(OUTPUT_FOLDER, front_name), dpi=(DPI, DPI))
        back_page.save(os.path.join(OUTPUT_FOLDER, back_name), dpi=(DPI, DPI))
        
        print(f"  -> {front_name}")
        print(f"  -> {back_name}")
        print()
    
    # выводим инструкцию пользователю
    print("=" * 60)
    print("ИНСТРУКЦИЯ ПО ПЕЧАТИ (Canon G1411)")
    print("=" * 60)
    print()
    print("1. Напечатай ВСЕ front-файлы")
    print()
    print("2. Переверни стопку СЛЕВА НАПРАВО")
    print()
    print("3. Положи обратно в лоток")
    print()
    print("4. Напечатай back-файлы В ОБРАТНОМ ПОРЯДКЕ:")
    for i in range(len(sheets), 0, -1):
        print(f"   layout_sheet_{i:02d}_back.png")
    print()
    print("=" * 60)
    print(f"Файлы в папке: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()