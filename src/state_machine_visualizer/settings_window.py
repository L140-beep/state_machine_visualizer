import tkinter as tk
from tkinter import ttk
from typing import Dict
from state_machine_visualizer.theme import COLORS
from state_machine_visualizer.visualizers.base import BaseVisualizer


class SettingsWindow:

    def __init__(self, parent, visualizer: BaseVisualizer):
        self.parent = parent
        self.settings: Dict[str, ttk.Widget] = {}
        self.visualizer = visualizer
        self.window = tk.Toplevel(parent)
        self.window.title("Настройки")
        self.window.configure(bg=COLORS['settings_bg'])
        self.window.resizable(True, True)
        self.window.minsize(400, 300)
        self.create_widgets()

    def center_window(self):
        """Центрирует окно относительно родительского"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()

        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)

        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.window, style='Settings.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Заголовок
        title_label = ttk.Label(
            main_frame, text="Настройки", style='Title.TLabel')
        title_label.pack(pady=(0, 20))

        # Контейнер для скроллинга
        container = ttk.Frame(main_frame, style='Settings.TFrame')
        container.pack(fill=tk.BOTH, expand=True)

        # Создаем Canvas и Scrollbar
        self.canvas = tk.Canvas(
            container, bg=COLORS['settings_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self.canvas.yview)

        # Фрейм для содержимого внутри Canvas
        self.scrollable_frame = ttk.Frame(self.canvas, style='Settings.TFrame')

        # Привязываем изменение размера фрейма к Canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.on_frame_configure(self.canvas)
        )

        # Создаем окно в Canvas для фрейма с центрированием
        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковываем Canvas и Scrollbar
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")

        # Привязываем изменение размера Canvas для центрирования содержимого
        self.canvas.bind(
            '<Configure>', lambda e: self.center_content(self.canvas))

        # Заголовки таблицы
        ttk.Label(self.scrollable_frame, text="Название",
                  style='Settings.TLabel', font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, padx=10, pady=8, sticky="w")
        ttk.Label(self.scrollable_frame, text="Значение",
                  style='Settings.TLabel', font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=1, padx=10, pady=8, sticky="w")

        self.settings = self.visualizer.draw_settings(self.scrollable_frame)

        # Настройка весов колонок для растяжения
        self.scrollable_frame.columnconfigure(1, weight=1)
        # Кнопка сохранения будет создана в refresh_widgets
        if not hasattr(self, 'button_frame'):
            self.create_save_button()

        button_row = len(self.settings) + 2
        self.button_frame.grid(row=button_row, column=0,
                               columnspan=2, sticky="ew", pady=(20, 0))

        # Привязываем обработчик изменения размера
        self.window.bind('<Configure>', self.on_window_configure)

        # Обновляем геометрию после создания виджетов
        self.window.after(100, self.adjust_window_size)

    def create_save_button(self):
        """Создает кнопку сохранения внизу окна"""
        # Фрейм для кнопки сохранения
        self.button_frame = ttk.Frame(
            self.scrollable_frame, style='Settings.TFrame')
        # Позиция будет установлена в refresh_widgets

        self.save_btn = ttk.Button(self.button_frame, text="Сохранить",
                                   command=self.save_settings,
                                   style='Primary.TButton')
        self.save_btn.pack(pady=10)

    def on_frame_configure(self, canvas):
        """Обновляет область прокрутки при изменении размера фрейма"""
        canvas.configure(scrollregion=canvas.bbox("all"))
        # Центрируем содержимое после обновления
        self.center_content(canvas)

    def center_content(self, canvas):
        """Центрирует содержимое в Canvas"""
        canvas.update_idletasks()
        # Получаем размеры Canvas и содержимого
        canvas_width = canvas.winfo_width()
        frame_width = self.scrollable_frame.winfo_reqwidth()

        # Вычисляем позицию для центрирования
        if frame_width < canvas_width:
            x = (canvas_width - frame_width) // 2
        else:
            x = 0

        # Обновляем позицию окна в Canvas
        if canvas.find_all():
            canvas.coords(canvas.find_all()[0], x, 0)

    def on_window_configure(self, event):
        """Обрабатывает изменение размера окна"""
        if event.widget == self.window:
            # Можно добавить дополнительную логику при изменении размера
            pass

    def adjust_window_size(self):
        """Автоматически подстраивает размер окна под содержимое"""
        self.window.update_idletasks()

        # Получаем размеры содержимого
        content_width = self.scrollable_frame.winfo_reqwidth() + 60  # + отступы
        content_height = self.scrollable_frame.winfo_reqheight() + \
            150  # + заголовок и кнопка

        # Ограничиваем максимальный размер
        max_width = min(content_width, 800)
        max_height = min(content_height, 600)

        # Устанавливаем размер окна
        self.window.geometry(f"{max_width}x{max_height}")

        # Центрируем окно
        self.center_window()

    def save_settings(self):
        values = self.visualizer.get_settings_values(self.settings)
        self.visualizer.apply_settings(values)
        self.window.destroy()
