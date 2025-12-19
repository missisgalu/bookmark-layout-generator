import os

# размеры листа а4 в миллиметрах
PAPER_WIDTH_MM = 210
PAPER_HEIGHT_MM = 297

# качество печати (точек на дюйм)
DPI = 300

# отступ от края страницы (1.5 см = 15 мм)
MARGIN_MM = 15
# расстояние между изображениями на листе (1.5 см = 15 мм)
SPACING_MM = 15

# коэффициент масштабирования изображений (1.0 = исходный размер)
SCALE_FACTOR = 1.0

# определяем пути к папкам относительно текущего скрипта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "input")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
