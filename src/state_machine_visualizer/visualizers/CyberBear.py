from typing import Any, Dict
import tkinter as tk
from state_machine_visualizer.visualizers.base import BaseVisualizer
from state_machine_visualizer.simulator import (
    StateMachineResult,
    CyberBear,
    StateMachine,
    run_state_machine,
    EventLoop
)


class CyberBearVisualizer(BaseVisualizer):
    """Визуализатор для платформы КиберМишка (blg-mb-1-a12)."""

    def __init__(self, parent, state_machine_data: Dict[str, Any]):
        # Инициализируем атрибуты до вызова super().__init__,
        # так как оно вызывает create_initial_view
        self.matrix_size = (7, 5)  # Размер матрицы светодиодов
        self.pixel_size = 30  # Размер одного пикселя в пикселях
        self.matrix_pixels = []  # Хранит канвасы для пикселей матрицы
        self.left_eye = None  # Канвас для левого глаза
        self.right_eye = None  # Канвас для правого глаза
        self.bear = CyberBear()
        print("Initializing CyberBearVisualizer")
        super().__init__(parent, state_machine_data)
        # Устанавливаем callback после создания виджетов
        self.bear.on_state_changed = self.update_visualization

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

        # Кнопка остановки
        stop_button = tk.Button(
            self.widget,
            text="⏹️ Остановить",
            command=self.stop_simulation
        )
        stop_button.pack(pady=5)

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

    def rgbk_to_color(self, rgbk):
        """Преобразует цвет из формата RGBK в RGB."""
        r, g, b, k = rgbk
        # Преобразуем RGBK в RGB, учитывая компонент K
        k_factor = 1 - (k / 255)
        # Умножаем на 16 для усиления яркости
        r = min(255, max(0, int(r * k_factor * 16)))
        g = min(255, max(0, int(g * k_factor * 16)))
        b = min(255, max(0, int(b * k_factor * 16)))
        color = f'#{r:02x}{g:02x}{b:02x}'
        return color

    def update_visualization(self):
        """Обновляет отображение при изменении состояния."""
        print("update_visualization called")
        rows, cols = self.matrix_size
        if self.left_eye and self.right_eye:
            # Обновляем левый глаз
            left_color = self.rgbk_to_color(self.bear.left_eye)
            print("Left eye color:", left_color)
            self.left_eye.itemconfig('led', fill=left_color)

            # Обновляем правый глаз
            right_color = self.rgbk_to_color(self.bear.right_eye)
            print("Right eye color:", right_color)
            self.right_eye.itemconfig('led', fill=right_color)

            # Обновляем матрицу светодиодов
            for row in range(rows):
                for col in range(cols):
                    brightness = self.bear.get_matrix_pixel(row, col)
                    # Преобразуем яркость (0-100) в оттенок серого
                    gray = int(brightness * 2.55)
                    color = f'#{gray:02x}{gray:02x}{gray:02x}'
                    self.matrix_pixels[row][col].itemconfig('led', fill=color)
        else:
            print("Canvas doesn't exist yet")
            print("self.left_eye:", self.left_eye)
            print("self.right_eye:", self.right_eye)

    def update_with_result(self, result: StateMachineResult):
        """Обновляет отображение с результатом работы машины состояний."""
        self.update_visualization()

    def stop_simulation(self):
        """Останавливает выполнение машины состояний."""
        EventLoop.events.append('break')

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

    def _start_simulation(self):
        """Запускает симуляцию машины состояний."""
        try:
            self.bear = CyberBear()
            self.bear.on_state_changed = self.update_visualization
            if not self.state_machine_data:
                raise ValueError("Данные машины состояний не загружены")

            cgml_sm = self.state_machine_data.get('cgml_state_machine')
            if not cgml_sm:
                raise ValueError("CGMLStateMachine не найден в данных")

            sm = StateMachine(cgml_sm, sm_parameters={'CyberBear': self.bear})
            result = run_state_machine(sm, [], timeout_sec=1000.0)

            return result

        except Exception as e:
            print(e)
