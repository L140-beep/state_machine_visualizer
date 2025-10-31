from tkinter.ttk import Widget
from typing import Any, Dict
import tkinter as tk
import tkinter.ttk as ttk
from state_machine_visualizer.visualizers.base import BaseVisualizer
from state_machine_visualizer.simulator import (
    StateMachineResult,
    CyberBear,
    CyberBearSignal,
    StateMachine,
    run_state_machine,
    EventLoop
)
from copy import deepcopy


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
        self.signals = []  # Хранит список всех сигналов
        self.current_signal_index = 0  # Индекс текущего сигнала
        self.prev_signal = None  # Предыдущий отправленный сигнал
        self.bear = CyberBear()
        self.signal_rows = []  # Хранит строки с сигналами в настройках
        # Словарь для преобразования отображаемых имен в реальные
        self.signal_types = {
            "Уши-байты": "ears",
            "Нос-байты": "ir"
        }
        print("Initializing CyberBearVisualizer")
        super().__init__(parent, state_machine_data)
        # Устанавливаем callback после создания виджетов
        self.bear.on_state_changed = self.update_visualization

    def create_initial_view(self):
        """Создает начальное отображение КиберМишки."""
        # Создаем основной контейнер
        self.widget = tk.Frame(self.parent)
        self.widget.pack(padx=10, pady=10, expand=True)

        # Создаем центрирующий контейнер
        center_frame = tk.Frame(self.widget)
        center_frame.pack(expand=True)

        # Создаем контейнеры для двух колонок
        main_column = tk.Frame(center_frame)
        main_column.pack(side=tk.LEFT, padx=10)

        control_column = tk.Frame(center_frame)
        control_column.pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Создаем заголовок в основной колонке
        title = tk.Label(
            main_column,
            text="КиберМишка",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=5, anchor=tk.CENTER)

        # Контейнер для глаз
        eyes_frame = tk.Frame(main_column)
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

        # Создаем матрицу светодиодов в основной колонке
        matrix_frame = tk.Frame(main_column)
        matrix_frame.pack(pady=10)

        # Устанавливаем фиксированную ширину для контрольной колонки
        CONTROL_WIDTH = 200  # Ширина в пикселях
        MIN_HEIGHT = 100  # Минимальная высота в пикселях

        # В контрольной колонке создаем фрейм для информации о байтах
        bytes_info_frame = ttk.LabelFrame(
            control_column,
            text="Информация о байтах",
            width=CONTROL_WIDTH
        )
        bytes_info_frame.pack(pady=5, anchor=tk.CENTER,
                              expand=True, fill=tk.BOTH)

        # Метки для байтов с фиксированной высотой
        self.prev_byte_label = tk.Label(
            bytes_info_frame,
            text="Предыдущий байт: -",
            anchor=tk.CENTER,
            justify=tk.CENTER,
            width=25,  # Ширина в символах
            height=2  # Высота в строках
        )
        self.prev_byte_label.pack(padx=5, pady=2)

        self.current_byte_label = tk.Label(
            bytes_info_frame,
            text="Текущий байт: -",
            anchor=tk.CENTER,
            justify=tk.CENTER,
            width=25,  # Ширина в символах
            height=2  # Высота в строках
        )
        self.current_byte_label.pack(padx=5, pady=2)

        # Кнопки управления в контрольной колонке
        buttons_frame = ttk.LabelFrame(
            control_column,
            text="Управление",
            width=CONTROL_WIDTH
        )
        buttons_frame.pack(pady=5, anchor=tk.CENTER, expand=True, fill=tk.BOTH)

        # Кнопка отправки байта
        # Создаем кнопки с фиксированной высотой
        button_style = ttk.Style()
        button_style.configure('Fixed.TButton', padding=5)  # Добавляем отступы

        self.send_byte_button = ttk.Button(
            buttons_frame,
            text="▶ Отправить байт",
            command=self.send_next_byte,
            state='disabled',  # Изначально кнопка заблокирована
            width=20,  # Ширина в символах
            style='Fixed.TButton'
        )
        self.send_byte_button.pack(padx=5, pady=5, ipady=3)

        # Кнопка остановки
        stop_button = ttk.Button(
            buttons_frame,
            text="⏹️ Остановить",
            command=self.stop_simulation,
            width=20,  # Ширина в символах
            style='Fixed.TButton'
        )
        stop_button.pack(padx=5, pady=5, ipady=3)

        # Создаем сетку светодиодов
        rows, cols = self.matrix_size
        for row in range(rows):
            row_pixels = []
            for col in range(cols):
                pixel = tk.Canvas(
                    matrix_frame,
                    width=self.pixel_size,
                    height=self.pixel_size
                )
                pixel.grid(row=row, column=col, padx=1, pady=1)
                pixel.create_rectangle(
                    2, 2,
                    self.pixel_size-2,
                    self.pixel_size-2,
                    fill='black',
                    tags='led'
                )
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
        # Блокируем кнопку отправки байта при остановке
        self.send_byte_button.config(state='disabled')

    def get_settings(self):
        """Возвращает настройки визуализатора."""
        settings = {
            'signals': [
                {
                    'type': signal.type,
                    'value': signal.value
                }
                for signal in self.signals
            ]
        }
        print("get_settings -> returning signals:", settings['signals'])
        return settings

    def apply_settings(self, settings: Dict[str, Any]):
        """Применяет настройки."""
        signals = settings.get('signals', [])
        if signals:
            self.signals = [
                CyberBearSignal(
                    type=signal['type'],
                    value=signal['value']
                ) for signal in signals
            ]
            print("apply_settings -> created signals:",
                  [(s.type, s.value) for s in self.signals])

    def get_settings_values(
        self,
        widgets_dict: Dict[str, Widget]
    ) -> Dict[str, Any]:
        """Получает значения из виджетов настроек."""
        signals = []
        for i, row in enumerate(self.signal_rows):
            if not row['frame'].winfo_exists():
                continue

            try:
                display_type = row['type'].get()
                # Преобразуем в реальный тип
                signal_type = self.signal_types[display_type]
                value = int(row['value'].get())
                print(f"get_settings_values -> row {i}:", signal_type, value)
                if 0 <= value <= 255:
                    signals.append({
                        'type': signal_type,
                        'value': value
                    })
            except (ValueError, tk.TclError) as e:
                print(f"get_settings_values -> error in row {i}:", str(e))
                continue

        print("get_settings_values -> collected signals:", signals)
        return {'signals': signals}

    def draw_settings(self, parent_frame) -> Dict[str, Widget]:
        """Отрисовывает настройки визуализатора."""
        widgets = {}
        self.signal_rows = []  # Очищаем список сигналов перед отрисовкой

        # Фрейм для списка сигналов
        signals_frame = ttk.LabelFrame(parent_frame, text="Сигналы")
        signals_frame.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky='ew',
            padx=5,
            pady=5
        )

        def add_signal_row():
            """Добавляет новую строку с сигналом"""
            row_frame = ttk.Frame(signals_frame)
            row_frame.pack(fill='x', padx=5, pady=2)

            # Словарь для преобразования отображаемых имен в реальные
            signal_types = {
                "Уши-байты": "ears",
                "Нос-байты": "ir"
            }

            # Выпадающий список для типа сигнала
            signal_type = ttk.Combobox(
                row_frame,
                values=list(signal_types.keys()),
                state="readonly",
                width=15
            )
            signal_type.set("Уши-байты")
            signal_type.pack(side='left', padx=5)

            # Сохраняем и тип сигнала и словарь для преобразования
            self.signal_types = signal_types
            widgets[f'type_{len(self.signal_rows)}'] = signal_type

            # Поле для значения
            value = ttk.Spinbox(
                row_frame,
                from_=0,
                to=255,
                width=8
            )
            value.set(0)
            value.pack(side='left', padx=5)
            widgets[f'value_{len(self.signal_rows)}'] = value

            # Кнопка удаления
            delete_btn = ttk.Button(
                row_frame,
                text="✕",
                width=3,
                command=lambda: delete_signal_row(row_frame)
            )
            delete_btn.pack(side='left', padx=5)

            self.signal_rows.append({
                'frame': row_frame,
                'type': signal_type,
                'value': value
            })

        def delete_signal_row(row_frame):
            """Удаляет строку с сигналом и очищает связанные виджеты"""
            # Находим индекс удаляемого ряда
            for i, row in enumerate(self.signal_rows):
                if row['frame'] == row_frame:
                    # Удаляем записи из widgets_dict
                    widgets.pop(f'type_{i}', None)
                    widgets.pop(f'value_{i}', None)
                    break

            # Удаляем фрейм
            row_frame.destroy()
            # Обновляем список рядов
            self.signal_rows = [
                row for row in self.signal_rows
                if row['frame'] != row_frame
            ]

        # Кнопка добавления сигнала
        add_btn = ttk.Button(
            signals_frame,
            text="+ Добавить сигнал",
            command=add_signal_row
        )
        add_btn.pack(pady=5)

        # Загружаем существующие сигналы
        existing_signals = self.get_settings().get('signals', [])
        for signal in existing_signals:
            add_signal_row()  # Создаем новую строку
            row = self.signal_rows[-1]  # Получаем последнюю добавленную строку
            # Находим отображаемое имя по реальному типу
            display_type = next(
                name for name, type_ in self.signal_types.items()
                if type_ == signal['type']
            )
            row['type'].set(display_type)  # Устанавливаем тип
            row['value'].set(str(signal['value']))  # Устанавливаем значение

        return widgets

    def send_next_byte(self):
        """Отправляет следующий байт в КиберМишку."""
        if not self.signals:
            return

        if self.current_signal_index < len(self.signals):
            # Получаем текущий сигнал
            current_signal = self.signals[self.current_signal_index]

            # Обновляем медведя
            self.bear.signals = [deepcopy(current_signal)]

            # Обновляем метки
            if self.prev_signal:
                prev_text = (
                    f"Предыдущий байт: {self.prev_signal.type}="
                    f"{self.prev_signal.value}"
                )
                self.prev_byte_label.config(text=prev_text)

            curr_text = (
                f"Текущий байт: {current_signal.type}="
                f"{current_signal.value}"
            )
            self.current_byte_label.config(text=curr_text)

            # Сохраняем текущий сигнал как предыдущий
            self.prev_signal = current_signal

            # Увеличиваем индекс
            self.current_signal_index += 1

    def _start_simulation(self):
        """Запускает симуляцию машины состояний."""
        try:
            # Сбрасываем индексы и сигналы
            self.current_signal_index = 0
            self.prev_signal = None
            self.bear.signals = []

            # Обновляем метки
            self.prev_byte_label.config(text="Предыдущий байт: -")
            self.current_byte_label.config(text="Текущий байт: -")

            # Создаем новый экземпляр CyberBear
            self.bear = CyberBear()
            self.update_visualization()
            print(self.bear.signals)
            # Устанавливаем callback
            self.bear.on_state_changed = self.update_visualization

            if not self.state_machine_data:
                raise ValueError("Данные машины состояний не загружены")

            # Разблокируем кнопку отправки байта
            self.send_byte_button.config(state='normal')

            cgml_sm = self.state_machine_data.get('cgml_state_machine')
            if not cgml_sm:
                raise ValueError("CGMLStateMachine не найден в данных")

            sm = StateMachine(cgml_sm, sm_parameters={'CyberBear': self.bear})
            result = run_state_machine(
                sm, [], timeout_sec=1000.0, isInfinite=True)

            return result

        except Exception as e:
            print(e)
