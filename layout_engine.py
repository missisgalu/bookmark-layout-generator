from PIL import Image, ImageOps
import os
from config import PAPER_WIDTH_MM, PAPER_HEIGHT_MM, MARGIN_MM, SPACING_MM, OUTPUT_FOLDER, DPI
from utils import mm_to_px

class LayoutEngine:
    def __init__(self):
        # вычисляем размеры страницы и отступов в пикселях один раз при инициализации
        self.page_w = mm_to_px(PAPER_WIDTH_MM)
        self.page_h = mm_to_px(PAPER_HEIGHT_MM)
        self.margin = mm_to_px(MARGIN_MM)
        self.spacing = mm_to_px(SPACING_MM)
        self.max_w = self.page_w - 2 * self.margin
        self.max_h = self.page_h - 2 * self.margin

    def pack_images(self, images):
        # распределяет список изображений по страницам и строкам
        sheets = []
        current_page_rows = []
        current_page_h = 0
        
        current_row = []
        current_row_w = 0
        current_row_h = 0
        
        def finalize_row(row, w, h):
            return {'items': row, 'width': w, 'height': h}

        for filename, img in images:
            w, h = img.size
            if w > self.max_w:
                print(f"  Внимание: {filename} слишком широкое, пропуск.")
                continue

            # проверяем влезет ли в текущую строку
            if not current_row:
                current_row = [(filename, img)]
                current_row_w = w
                current_row_h = h
            else:
                new_w = current_row_w + self.spacing + w
                if new_w <= self.max_w:
                    current_row.append((filename, img))
                    current_row_w = new_w
                    current_row_h = max(current_row_h, h)
                else:
                    # финализируем строку и проверяем место на странице
                    row_data = finalize_row(current_row, current_row_w, current_row_h)
                    
                    new_h = current_page_h
                    if current_page_rows:
                        new_h += self.spacing
                    new_h += row_data['height']
                    
                    if new_h > self.max_h:
                        # страница полная
                        sheets.append({'rows': current_page_rows, 'total_h': current_page_h})
                        current_page_rows = [row_data]
                        current_page_h = row_data['height']
                    else:
                        current_page_rows.append(row_data)
                        if len(current_page_rows) > 1:
                            current_page_h += self.spacing
                        current_page_h += row_data['height']
                    
                    current_row = [(filename, img)]
                    current_row_w = w
                    current_row_h = h

        # сбрасываем последние остатки
        if current_row:
            row_data = finalize_row(current_row, current_row_w, current_row_h)
            new_h = current_page_h
            if current_page_rows:
                new_h += self.spacing
            new_h += row_data['height']
            
            if new_h > self.max_h:
                 sheets.append({'rows': current_page_rows, 'total_h': current_page_h})
                 sheets.append({'rows': [row_data], 'total_h': row_data['height']})
            else:
                 if current_page_rows:
                     current_page_h += self.spacing
                 current_page_h += row_data['height']
                 current_page_rows.append(row_data)
                 sheets.append({'rows': current_page_rows, 'total_h': current_page_h})
        
        return sheets

    def generate_sheets(self, sheets):
        # генерирует и сохраняет финальные изображения для каждой страницы
        for idx, page in enumerate(sheets):
            rows = page['rows']
            total_h = page['total_h']
            
            start_y = (self.page_h - total_h) // 2
            front = Image.new('RGBA', (self.page_w, self.page_h), (0, 0, 0, 0))
            back = Image.new('RGBA', (self.page_w, self.page_h), (0, 0, 0, 0))
            
            curr_y = start_y
            for row in rows:
                row_w = row['width']
                start_x = (self.page_w - row_w) // 2
                
                curr_x = start_x
                for filename, img in row['items']:
                    front.paste(img, (curr_x, curr_y), mask=img)
                    
                    w, h = img.size
                    back_img = ImageOps.mirror(img)
                    back_x = self.page_w - curr_x - w
                    back.paste(back_img, (back_x, curr_y), mask=back_img)
                    
                    curr_x += w + self.spacing
                
                curr_y += row['height'] + self.spacing
            
            # сохраняем
            num = idx + 1
            f_name = f"layout_sheet_{num:02d}_front.png"
            b_name = f"layout_sheet_{num:02d}_back.png"
            
            front.save(os.path.join(OUTPUT_FOLDER, f_name), dpi=(DPI, DPI))
            back.save(os.path.join(OUTPUT_FOLDER, b_name), dpi=(DPI, DPI))
            print(f"  Лист {num:02d}: сохранено.")

        return len(sheets)
