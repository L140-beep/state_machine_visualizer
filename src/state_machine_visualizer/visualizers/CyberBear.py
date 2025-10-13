from typing import Any, Dict
import tkinter as tk
from state_machine_visualizer.visualizers.base import BaseVisualizer
from state_machine_visualizer.simulator import StateMachineResult


class CyberBearVisualizer(BaseVisualizer):
    """Визуализатор для платформы КиберМишка (blg-mb-1-a12)."""

    def __init__(self, parent, state_machine_data: Dict[str, Any]):
        # Инициализируем атрибуты до вызова super().__init__,
        # так как оно вызывает create_initial_view
        self.matrix_size = (5, 7)  # Размер матрицы светодиодов
        self.pixel_size = 30  # Размер одного пикселя в пикселях
        self.matrix_pixels = []  # Хранит канвасы для пикселей матрицы
        self.left_eye = None  # Канвас для левого глаза
        self.right_eye = None  # Канвас для правого глаза
        super().__init__(parent, state_machine_data)

    def create_initial_view(self):
        """Создает начальное отображение КиберМишки."""
        # Создаем основной контейнер
        self.widget = tk.Frame(self.parent)
        self.widget.pack(padx=10, pady=10)

        # Создаем заголовок
        title = tk.Label(self.widget, text="КиберМишка",
                         font=("Arial", 16, "bold"))
        title.pack(pady=5)

        # Контейнер для глаз
        eyes_frame = tk.Frame(self.widget)
        eyes_frame.pack(pady=10)

        # Создаем глаза (круглые RGB-светодиоды)
        eye_size = 50
        self.left_eye = tk.Canvas(eyes_frame, width=eye_size, height=eye_size)
        self.left_eye.pack(side=tk.LEFT, padx=10)
        self.left_eye.create_oval(
            2, 2, eye_size-2, eye_size-2, fill='black', tags='led')

        self.right_eye = tk.Canvas(eyes_frame, width=eye_size, height=eye_size)
        self.right_eye.pack(side=tk.LEFT, padx=10)
        self.right_eye.create_oval(
            2, 2, eye_size-2, eye_size-2, fill='black', tags='led')

        # Создаем матрицу светодиодов
        matrix_frame = tk.Frame(self.widget)
        matrix_frame.pack(pady=10)

        # Создаем сетку светодиодов
        rows, cols = self.matrix_size
        for row in range(rows):
            row_pixels = []
            for col in range(cols):
                pixel = tk.Canvas(
                    matrix_frame, width=self.pixel_size, height=self.pixel_size)
                pixel.grid(row=row, column=col, padx=1, pady=1)
                pixel.create_rectangle(2, 2, self.pixel_size-2, self.pixel_size-2,
                                       fill='black', tags='led')
                row_pixels.append(pixel)
            self.matrix_pixels.append(row_pixels)

    def update_with_result(self, result: StateMachineResult):
        """Обновляет отображение состояния КиберМишки."""
        if not hasattr(result, 'bear') or result.bear is None:
            return

        # Обновляем цвет глаз
        def rgbk_to_color(rgbk):
            r, g, b, k = rgbk
            # Преобразуем RGBK в RGB, учитывая компонент K
            k_factor = 1 - (k / 255)
            r = int(r * k_factor)
            g = int(g * k_factor)
            b = int(b * k_factor)
            return f'#{r:02x}{g:02x}{b:02x}'

        # Обновляем левый глаз
        left_color = rgbk_to_color(result.bear.left_eye)
        self.left_eye.itemconfig('led', fill=left_color)

        # Обновляем правый глаз
        right_color = rgbk_to_color(result.bear.right_eye)
        self.right_eye.itemconfig('led', fill=right_color)

        # Обновляем матрицу светодиодов
        for row in range(self.matrix_size[0]):
            for col in range(self.matrix_size[1]):
                brightness = result.bear.get_matrix_pixel(row, col)
                # Преобразуем яркость (0-100) в оттенок серого
                color = f'#{int(brightness * 2.55):02x}' * 3
                self.matrix_pixels[row][col].itemconfig('led', fill=color)

    def get_settings(self):
        """Возвращает настройки визуализатора."""
        return {
            "pixel_size": {
                "type": "int",
                "label": "Размер пикселя (px)",
                "value": self.pixel_size,
                "min": 10,
                "max": 50
            }
        }
