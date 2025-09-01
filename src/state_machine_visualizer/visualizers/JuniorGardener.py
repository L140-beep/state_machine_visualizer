import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from . import BaseVisualizer
from ..simulator import StateMachineResult, run_state_machine, StateMachine, Gardener, GardenerCrashException, EventLoop


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
        self.matrix = [[0, 0, 0, 0],
                       [0, 0, 0, 0],
                       [0, 0, 0, 0]]
        super().__init__(parent, state_machine_data)

    def create_initial_view(self):
        """Создает исходное отображение машины состояний."""
        # Основной фрейм
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Заголовок
        title_label = ttk.Label(main_frame, text="Junior Gardener - Машина состояний",
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

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

            # Пересоздаем матрицу с новыми размерами
            self.matrix = [[0 for _ in range(self.width)]
                           for _ in range(self.height)]

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

    def run_state_machine(self):
        """Запускает машину состояний и возвращает результат."""
        try:
            # Создаем экземпляр Gardener с текущими размерами
            gardener = Gardener(self.width, self.height)
            # Присваиваем ориентацию
            if self.orientation == "Север":
                gardener.orientation = gardener.NORTH
            elif self.orientation == "Юг":
                gardener.orientation = gardener.SOUTH
            elif self.orientation == "Запад":
                gardener.orientation = gardener.WEST
            elif self.orientation == "Восток":
                gardener.orientation = gardener.EAST

            # Создаем машину состояний из данных
            if not self.state_machine_data:
                raise ValueError("Данные машины состояний не загружены")

            # Получаем CGMLStateMachine из уже распарсенных данных
            cgml_sm = self.state_machine_data.get('cgml_state_machine')
            if not cgml_sm:
                raise ValueError("CGMLStateMachine не найден в данных")

            # Создаем StateMachine с параметром gardener
            sm = StateMachine(cgml_sm, sm_parameters={'gardener': gardener})

            # Запускаем машину состояний
            print(
                f"Запускаю машину состояний с Gardener (поле {self.width}x{self.height})")
            result = run_state_machine(sm, [], timeout_sec=1000.0)
            # Сохраняем gardener для отображения поля
            self.current_gardener = gardener

            return result

        except GardenerCrashException as e:
            import tkinter.messagebox as mb
            print(f"Gardener упал: {e}")
            # Показываем пользователю сообщение об ошибке
            mb.showerror("Ошибка выполнения", f"Gardener упал: {e}")
            # Сохраняем gardener для отображения поля даже при крахе
            if 'gardener' in locals():
                self.current_gardener = gardener
            # Возвращаем специальный результат для краша (timeout=True)
            return StateMachineResult(True, EventLoop.events, EventLoop.called_events, sm.components)
        except Exception as e:
            print(f"Ошибка при запуске машины состояний: {e}")
            return None

    def update_with_result(self, result: StateMachineResult):
        """Обновляет отображение с результатом работы машины состояний."""
        print(f"Обновляю отображение с результатом: {result}")

        # Обновляем информацию о результате
        if hasattr(self, 'widget') and self.widget:
            # Находим существующий info_label и обновляем его
            for child in self.widget.winfo_children():
                if isinstance(child, ttk.Label) and "Платформа:" in child.cget("text"):
                    # Проверяем, был ли краш Gardener
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

        # Обновляем матрицу с данными из Gardener
        if hasattr(self, 'current_gardener') and self.current_gardener:
            self.matrix = self.current_gardener.field
            if hasattr(self, 'matrix_frame'):
                # Очищаем старую матрицу
                for widget in self.matrix_frame.winfo_children():
                    widget.destroy()
                # Перерисовываем матрицу с новыми данными
                self.draw_matrix()
                self.matrix_frame.update_idletasks()
                if hasattr(self, 'canvas'):
                    self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def draw_matrix(self):
        """Отрисовывает матрицу в виде таблицы"""
        cell_size = 40

        # Заполняем матрицу значениями (без заголовков)
        for row in range(self.height):
            for col in range(self.width):
                if row < len(self.matrix) and col < len(self.matrix[0]):
                    value = self.matrix[row][col]
                else:
                    value = 0

                # Определяем цвет ячейки в зависимости от значения
                if value == 0:
                    cell_color = '#f0f0f0'  # Пустая клетка - светло-серый
                elif value == 1:
                    cell_color = '#ff6b6b'  # Роза - красный
                elif value == 2:
                    cell_color = '#4ecdc4'  # Мята - бирюзовый
                elif value == 3:
                    cell_color = '#45b7d1'  # Василек - синий
                elif value == -1:
                    cell_color = '#2c3e50'  # Стена - темно-серый
                else:
                    cell_color = '#f0f0f0'  # Неизвестное значение - светло-серый

                # Создаем ячейку с соответствующим цветом
                cell = tk.Frame(self.matrix_frame, bg=cell_color, relief=tk.RAISED, bd=1,
                                width=cell_size, height=cell_size)
                cell.grid(row=row, column=col,
                          padx=1, pady=1, sticky="nsew")
                cell.grid_propagate(False)

                # Добавляем текст значения
                value_text = str(value)
                label = tk.Label(cell, text=value_text, bg=cell_color,
                                 font=("Arial", 8, "bold"), wraplength=cell_size-10)
                label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)


def create_matrix_visualizer(parent, settings_dict):
    """Фабричная функция для создания визуализатора матрицы"""
    try:
        width = int(settings_dict.get("Ширина матрицы", 10))
        height = int(settings_dict.get("Высота матрицы", 8))

        return JuniorGardenerVisualizer(parent, settings_dict)
    except (ValueError, TypeError):
        return JuniorGardenerVisualizer(parent)  # Со значениями по умолчанию
