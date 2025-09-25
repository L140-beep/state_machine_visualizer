import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from state_machine_visualizer.visualizers.base import BaseVisualizer
from state_machine_visualizer.simulator import StateMachineResult, run_state_machine, StateMachine, Gardener, GardenerCrashException, EventLoop


# Настройки для визуализации матрицы
settings = {
    "Ширина матрицы": "10",
    "Высота матрицы": "8",
}


def process_file(file_path):
    """Обрабатывает файл и создает матрицу"""
    print(f"Создаю матрицу из файла: {file_path}")
    # Здесь можно добавить логику чтения матрицы из файла
    return {"status": "success", "message": "Матрица создана"}


def get_preview_data(file_path):
    """Возвращает данные для предпросмотра"""
    return {"type": "matrix", "width": 10, "height": 8}


class JuniorGardenerVisualizer(BaseVisualizer):
    def __init__(self, parent, state_machine_data: Dict[str, Any]):
        self.width = 10
        self.height = 8
        self.orientation = 'Север'  # новый параметр
        # Отдельно храним редактируемое поле и поле результата
        self.editable_field = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.result_field = None  # появляется после запуска
        self.edit_mode = False  # Режим редактирования поля
        self.current_gardener = None  # Текущий экземпляр gardener
        super().__init__(parent, state_machine_data)

    def get_display_matrix(self):
        """Возвращает матрицу, которая должна отображаться в текущем режиме."""
        if self.edit_mode:
            return self.editable_field
        # В режиме просмотра показываем результат, если он есть, иначе исходное поле
        return self.result_field if self.result_field is not None else self.editable_field

    def create_initial_view(self):
        """Создает исходное отображение машины состояний."""
        # Основной фрейм
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Заголовок и кнопка переключения режимов
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="Junior Gardener - Машина состояний",
                                font=("Arial", 14, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Кнопка переключения режимов
        self.mode_button = ttk.Button(header_frame, text="✏️ Режим редактирования",
                                     command=self.toggle_edit_mode)
        self.mode_button.pack(side=tk.RIGHT)

        # Информация о машине состояний
        if self.state_machine_data:
            platform = self.state_machine_data.get('platform', 'Неизвестно')
            name = self.state_machine_data.get('name', 'Без названия')
            states_count = len(self.state_machine_data.get('states', {}))
            transitions_count = len(
                self.state_machine_data.get('transitions', {}))

            info_text = f"Платформа: {platform}\nНазвание: {name}\nСостояний: {states_count}\nПереходов: {transitions_count}"
        else:
            info_text = "Данные машины состояний не загружены"

        info_label = ttk.Label(main_frame, text=info_text,
                               font=("Arial", 10), justify=tk.LEFT)
        info_label.pack(pady=(0, 10))

        # Фрейм для матрицы с прокруткой
        matrix_container = ttk.Frame(main_frame)
        matrix_container.pack(fill=tk.BOTH, expand=True)

        # Canvas для матрицы
        self.canvas = tk.Canvas(matrix_container, bg='white', highlightthickness=1,
                                highlightbackground='#cccccc')

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            matrix_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(
            matrix_container, orient="horizontal", command=self.canvas.xview)

        # Настраиваем Canvas для прокрутки
        self.canvas.configure(yscrollcommand=v_scrollbar.set,
                              xscrollcommand=h_scrollbar.set)

        # Размещаем виджеты
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Настраиваем веса для растяжения
        matrix_container.grid_rowconfigure(0, weight=1)
        matrix_container.grid_columnconfigure(0, weight=1)

        # Фрейм внутри Canvas для матрицы
        self.matrix_frame = ttk.Frame(self.canvas)
        self.canvas.create_window(
            (0, 0), window=self.matrix_frame, anchor="nw")

        # Отрисовываем матрицу
        self.draw_matrix()

        # Обновляем область прокрутки
        self.matrix_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.widget = main_frame

    def get_settings(self):
        """Возвращает настройки визуализатора для окна настроек."""
        return {
            "Ширина матрицы": str(self.width),
            "Высота матрицы": str(self.height),
            "Ориентация": self.orientation  # Север/Юг/Запад/Восток
        }

    def apply_settings(self, settings):
        """Применяет настройки к визуализатору."""
        try:
            # Обновляем размеры матрицы
            if "Ширина матрицы" in settings:
                self.width = int(settings["Ширина матрицы"])
            if "Высота матрицы" in settings:
                self.height = int(settings["Высота матрицы"])
            if "Ориентация" in settings:
                self.orientation = settings["Ориентация"]

            # Обновляем размеры матрицы
            self.ensure_matrix_size()

            # Перерисовываем матрицу
            if hasattr(self, 'matrix_frame'):
                for widget in self.matrix_frame.winfo_children():
                    widget.destroy()
                self.draw_matrix()
                self.matrix_frame.update_idletasks()
                if hasattr(self, 'canvas'):
                    self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except (ValueError, TypeError) as e:
            print(f"Ошибка при применении настроек: {e}")

    def toggle_edit_mode(self):
        """Переключает режим редактирования поля"""
        self.edit_mode = not self.edit_mode
        
        if self.edit_mode:
            self.mode_button.config(text="👁️ Режим просмотра")
        else:
            self.mode_button.config(text="✏️ Режим редактирования")
        
        # Перерисовываем матрицу с учетом нового режима
        if hasattr(self, 'matrix_frame'):
            for widget in self.matrix_frame.winfo_children():
                widget.destroy()
            self.draw_matrix()
            self.matrix_frame.update_idletasks()
            if hasattr(self, 'canvas'):
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_cell_click(self, row, col):
        """Обрабатывает клик по ячейке в режиме редактирования"""
        if not self.edit_mode:
            return
        
        # Проверяем границы матрицы
        if row < 0 or row >= self.height or col < 0 or col >= self.width:
            return
        
        # Убеждаемся, что матрица имеет правильные размеры
        if row >= len(self.editable_field) or col >= len(self.editable_field[row]):
            return
        
        # Циклически изменяем значение: 0 -> -1 -> 1 -> 2 -> 3 -> 0
        current_value = self.editable_field[row][col]
        if current_value == 0:
            new_value = -1
        elif current_value == -1:
            new_value = 1
        elif current_value == 1:
            new_value = 2
        elif current_value == 2:
            new_value = 3
        else:  # current_value == 3
            new_value = 0
        
        self.editable_field[row][col] = new_value
        
        # Перерисовываем только эту ячейку
        self.redraw_cell(row, col)

    def redraw_cell(self, row, col):
        """Перерисовывает конкретную ячейку"""
        if not hasattr(self, 'matrix_frame'):
            return
        
        # Находим и удаляем старую ячейку
        for widget in self.matrix_frame.winfo_children():
            widget_info = widget.grid_info()
            if widget_info.get('row') == row and widget_info.get('column') == col:
                widget.destroy()
                break
        
        # Создаем новую ячейку
        self.create_cell(row, col)

    def set_field(self, field_matrix):
        """Устанавливает поле для gardener"""
        if hasattr(self, 'current_gardener') and self.current_gardener:
            self.current_gardener.set_field(field_matrix)
        # исходное поле обновляем отдельно
        self.editable_field = field_matrix
        # Перерисовываем матрицу
        if hasattr(self, 'matrix_frame'):
            for widget in self.matrix_frame.winfo_children():
                widget.destroy()
            self.draw_matrix()
            self.matrix_frame.update_idletasks()
            if hasattr(self, 'canvas'):
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def ensure_matrix_size(self):
        """Убеждается, что исходное поле имеет правильные размеры"""
        new_matrix = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for row in range(min(len(self.editable_field), self.height)):
            for col in range(min(len(self.editable_field[row]) if row < len(self.editable_field) else 0, self.width)):
                new_matrix[row][col] = self.editable_field[row][col]
        self.editable_field = new_matrix

    def run_state_machine(self):
        """Запускает машину состояний и возвращает результат."""
        try:
            gardener = Gardener(self.width, self.height)
            if self.orientation == "Север":
                gardener.orientation = gardener.NORTH
            elif self.orientation == "Юг":
                gardener.orientation = gardener.SOUTH
            elif self.orientation == "Запад":
                gardener.orientation = gardener.WEST
            elif self.orientation == "Восток":
                gardener.orientation = gardener.EAST

            if not self.state_machine_data:
                raise ValueError("Данные машины состояний не загружены")

            cgml_sm = self.state_machine_data.get('cgml_state_machine')
            if not cgml_sm:
                raise ValueError("CGMLStateMachine не найден в данных")

            # используем неизменяемое пользователем исходное поле
            gardener.set_field(self.editable_field)

            sm = StateMachine(cgml_sm, sm_parameters={'gardener': gardener})

            print(f"Запускаю машину состояний с Gardener (поле {self.width}x{self.height})")
            result = run_state_machine(sm, [], timeout_sec=1000.0)
            self.current_gardener = gardener
            # сохраняем поле результата отдельно
            self.result_field = gardener.field
            return result

        except GardenerCrashException as e:
            import tkinter.messagebox as mb
            print(f"Gardener упал: {e}")
            mb.showerror("Ошибка выполнения", f"Gardener упал: {e}")
            if 'gardener' in locals():
                self.current_gardener = gardener
                self.result_field = gardener.field
            return StateMachineResult(True, EventLoop.events, EventLoop.called_events, sm.components)
        except Exception as e:
            import tkinter.messagebox as mb
            message_text = str(e)
            if 'Клетка уже засажена' in message_text:
                mb.showerror("Ошибка", "Ошибка! Клетка уже засажена")
            else:
                mb.showerror("Ошибка выполнения", message_text)
            if 'gardener' in locals():
                self.current_gardener = gardener
            return None

    def update_with_result(self, result: StateMachineResult):
        """Обновляет отображение с результатом работы машины состояний."""
        print(f"Обновляю отображение с результатом: {result}")
        if hasattr(self, 'widget') and self.widget:
            for child in self.widget.winfo_children():
                if isinstance(child, ttk.Label) and "Платформа:" in child.cget("text"):
                    if hasattr(result, 'gardener_crashed'):
                        result_text = f"Результат выполнения:\n"
                        result_text += f"⚠️ Gardener упал во время выполнения!\n"
                        result_text += f"Поле отображается в состоянии до краша.\n"
                        result_text += f"Таймаут: {'Да' if result.timeout else 'Нет'}\n"
                        result_text += f"Вызванные сигналы: {', '.join(result.called_signals)}\n"
                        result_text += f"Все сигналы: {', '.join(result.signals)}\n"
                        result_text += f"Компоненты: {len(result.components)}"
                    else:
                        result_text = f"Результат выполнения:\n"
                        result_text += f"Таймаут: {'Да' if result.timeout else 'Нет'}\n"
                        result_text += f"Вызванные сигналы: {', '.join(result.called_signals)}\n"
                        result_text += f"Все сигналы: {', '.join(result.signals)}\n"
                        result_text += f"Компоненты: {len(result.components)}"
                    child.config(text=result_text)
                    break

        # при обновлении отображаем результат, не трогая исходное поле
        if hasattr(self, 'matrix_frame'):
            for widget in self.matrix_frame.winfo_children():
                widget.destroy()
            self.draw_matrix()
            self.matrix_frame.update_idletasks()
            if hasattr(self, 'canvas'):
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def draw_matrix(self):
        """Отрисовывает матрицу в виде таблицы с выделением gardener"""
        matrix = self.get_display_matrix()
        # на случай рассинхронизации размеров
        rows = self.height if self.edit_mode else len(matrix)
        cols = self.width if self.edit_mode else (len(matrix[0]) if matrix else 0)
        for row in range(rows):
            for col in range(cols):
                self.create_cell(row, col)

    def create_cell(self, row, col):
        """Создает отдельную ячейку матрицы"""
        cell_size = 40
        matrix = self.get_display_matrix()
        # Получаем значение безопасно
        value = 0
        if row < len(matrix) and matrix and col < len(matrix[0]):
            value = matrix[row][col]

        gardener_pos = None
        if hasattr(self, 'current_gardener') and self.current_gardener:
            if hasattr(self.current_gardener, 'x') and hasattr(self.current_gardener, 'y'):
                gardener_pos = (self.current_gardener.y, self.current_gardener.x)

        if value == 0:
            cell_color = '#f0f0f0'
        elif value == 1:
            cell_color = '#ff6b6b'
        elif value == 2:
            cell_color = '#4ecdc4'
        elif value == 3:
            cell_color = '#45b7d1'
        elif value == -1:
            cell_color = '#2c3e50'
        else:
            cell_color = '#f0f0f0'

        if gardener_pos == (row, col) and not self.edit_mode:
            border_color = '#ffa500'
            border_width = 3
        else:
            border_color = '#cccccc'
            border_width = 1

        cell = tk.Frame(self.matrix_frame, bg=cell_color, relief=tk.RAISED, bd=border_width,
                        width=cell_size, height=cell_size, highlightbackground=border_color, highlightcolor=border_color, highlightthickness=border_width)
        cell.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
        cell.grid_propagate(False)

        if self.edit_mode:
            cell.bind("<Button-1>", lambda e, r=row, c=col: self.on_cell_click(r, c))
            cell.config(cursor="hand2")

        value_text = str(value)
        label = tk.Label(cell, text=value_text, bg=cell_color, font=("Arial", 8, "bold"), wraplength=cell_size-10)
        label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        if self.edit_mode:
            label.bind("<Button-1>", lambda e, r=row, c=col: self.on_cell_click(r, c))
            label.config(cursor="hand2")


def create_matrix_visualizer(parent, settings_dict):
    """Фабричная функция для создания визуализатора матрицы"""
    try:
        width = int(settings_dict.get("Ширина матрицы", 10))
        height = int(settings_dict.get("Высота матрицы", 8))

        return JuniorGardenerVisualizer(parent, settings_dict)
    except (ValueError, TypeError):
        return JuniorGardenerVisualizer(parent)  # Со значениями по умолчанию
