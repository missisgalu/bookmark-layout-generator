"""
генератор раскладки закладок для двусторонней печати.
основной скрипт управления процессом.
by @pingalinux
"""

import os
from config import INPUT_FOLDER, OUTPUT_FOLDER, PAPER_WIDTH_MM, PAPER_HEIGHT_MM, DPI, MARGIN_MM, SPACING_MM
from utils import load_image, px_to_mm
from layout_engine import LayoutEngine

def prepare_folders():
    # подготавливаем папки и чистим старые результаты
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"Создана папка: {INPUT_FOLDER}")
        return False
    
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    
    for f in os.listdir(OUTPUT_FOLDER):
        if f.startswith('layout_'):
            os.remove(os.path.join(OUTPUT_FOLDER, f))
    return True

def main():
    if not prepare_folders():
        print("Положи файлы в 'input' и запусти снова.")
        return

    # ищем файлы
    files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.studio3'))])
    if not files:
        print(f"Нет файлов в '{INPUT_FOLDER}'")
        return

    print(f"Найдено файлов: {len(files)}")
    print(f"Настройки: {PAPER_WIDTH_MM}x{PAPER_HEIGHT_MM}mm @ {DPI} DPI")
    print(f"Поля: {MARGIN_MM}mm, зазоры: {SPACING_MM}mm\n")

    # загрузка
    images = []
    for f in files:
        print(f"  Загрузка: {f}")
        img = load_image(os.path.join(INPUT_FOLDER, f))
        if img:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            w, h = img.size
            print(f"    - {w}x{h}px ({px_to_mm(w):.1f}x{px_to_mm(h):.1f}mm)")
            images.append((f, img))
        else:
            print(f"    - ОШИБКА: Пропущено.")

    if not images:
        print("Нечего обрабатывать.")
        return

    print(f"\nРаскладка...")
    engine = LayoutEngine()
    sheets = engine.pack_images(images)
    
    if not sheets:
        print("Ошибка при создании раскладки.")
        return

    count = engine.generate_sheets(sheets)
    print(f"\nГотово! Создано листов: {count}")
    print("=" * 60)
    print("ИНСТРУКЦИЯ ПО ПЕЧАТИ (Canon G1411)")
    print("1. Напечатай ВСЕ front-файлы")
    print("2. Переверни стопку СЛЕВА НАПРАВО")
    print("3. Положи обратно в лоток")
    print("4. Напечатай back-файлы В ОБРАТНОМ ПОРЯДКЕ (как в папке)")
    print("=" * 60)

if __name__ == "__main__":
    main()