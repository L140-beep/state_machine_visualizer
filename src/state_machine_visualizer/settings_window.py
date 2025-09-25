import tkinter as tk
from tkinter import ttk
import json
import os
from .theme import COLORS


class SettingsWindow:
    def refresh_widgets(self, new_settings=None):
        """Обновляет содержимое окна настроек динамически."""
        if new_settings is not None:
            self.settings = new_settings
        # Очищаем содержимое scrollable_frame, но сохраняем кнопку
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(self, 'button_frame') and widget != self.button_frame:
                widget.destroy()
            elif not hasattr(self, 'button_frame'):
                widget.destroy()

        # Заголовки таблицы
        ttk.Label(self.scrollable_frame, text="Название",
                  style='Settings.TLabel', font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, padx=10, pady=8, sticky="w")
        ttk.Label(self.scrollable_frame, text="Значение",
                  style='Settings.TLabel', font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=1, padx=10, pady=8, sticky="w")

        # Загрузка существующих настроек
        self.entries = {}
        if self.settings:
            for i, (key, value) in enumerate(self.settings.items(), start=1):
                ttk.Label(self.scrollable_frame, text=key, style='Settings.TLabel').grid(
                    row=i, column=0, padx=10, pady=6, sticky="w")

                if key == "Ориентация":
                    directions = ["Север", "Юг", "Запад", "Восток"]
                    entry = ttk.Combobox(self.scrollable_frame, values=directions, state="readonly")
                    if value in directions:
                        entry.set(value)
                    else:
                        entry.set("Север")
                    entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
                else:
                    entry = ttk.Entry(self.scrollable_frame, style='Custom.TEntry')
                    entry.insert(0, value)
                    entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
                self.entries[key] = entry
        else:
            ttk.Label(self.scrollable_frame, text="Нет доступных настроек.", style='Settings.TLabel').grid(
                row=1, column=0, columnspan=2, padx=10, pady=20, sticky="w")

        self.scrollable_frame.columnconfigure(1, weight=1)

        # Создаем или обновляем позицию кнопки сохранения
        if not hasattr(self, 'button_frame'):
            self.create_save_button()
        
        # Обновляем позицию кнопки
        button_row = len(self.settings) + 2 if self.settings else 2
        self.button_frame.grid(row=button_row, column=0,
                              columnspan=2, sticky="ew", pady=(20, 0))

    def __init__(self, parent, visualizer_settings=None):
        self.parent = parent
        self.visualizer_settings = visualizer_settings or {}
        self.settings = {}
        self.load_settings()  # settings и visualizer_settings будут заполнены

        self.window = tk.Toplevel(parent)
        self.window.title("Настройки")
        self.window.configure(bg=COLORS['settings_bg'])
        self.window.resizable(True, True)
        self.window.minsize(400, 300)

        self.create_widgets()  # теперь виджеты создаются только после загрузки настроек
    # Центрируем окно только после полной отрисовки (см. adjust_window_size)
    # self.center_window()  # убрано отсюда

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
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковываем Canvas и Scrollbar
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")

        # Привязываем изменение размера Canvas для центрирования содержимого
        self.canvas.bind('<Configure>', lambda e: self.center_content(self.canvas))

        # Заголовки таблицы
        ttk.Label(self.scrollable_frame, text="Название",
                  style='Settings.TLabel', font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=0, padx=10, pady=8, sticky="w")
        ttk.Label(self.scrollable_frame, text="Значение",
                  style='Settings.TLabel', font=('Segoe UI', 10, 'bold')).grid(
            row=0, column=1, padx=10, pady=8, sticky="w")

        # Загрузка существующих настроек
        self.entries = {}
        if self.settings:
            # Определяем, Gardener ли это (по ключам или платформе)
            platform = ''
            if 'platform' in self.settings:
                platform = str(self.settings['platform']).lower()
            elif self.visualizer_settings and 'platform' in self.visualizer_settings:
                platform = str(self.visualizer_settings['platform']).lower()
            is_gardener = 'gardener' in platform
            for i, (key, value) in enumerate(self.settings.items(), start=1):
                ttk.Label(self.scrollable_frame, text=key, style='Settings.TLabel').grid(
                    row=i, column=0, padx=10, pady=6, sticky="w")

                if key == "Ориентация" and is_gardener:
                    entry = ttk.Combobox(self.scrollable_frame, values=[
                                         "Север", "Юг", "Запад", "Восток"], state="readonly")
                    entry.set(value)
                    entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
                else:
                    entry = ttk.Entry(self.scrollable_frame,
                                      style='Custom.TEntry')
                    entry.insert(0, value)
                    entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
                self.entries[key] = entry
        else:
            # Если настроек нет, показываем заглушку
            ttk.Label(self.scrollable_frame, text="Нет доступных настроек.", style='Settings.TLabel').grid(
                row=1, column=0, columnspan=2, padx=10, pady=20, sticky="w")

        # Настройка весов колонок для растяжения
        self.scrollable_frame.columnconfigure(1, weight=1)

        # Кнопка сохранения будет создана в refresh_widgets

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

    def load_settings(self):
        # Начинаем с настроек визуализатора (они имеют приоритет)
        self.settings = {}

        # Добавляем настройки визуализатора
        for key, value in self.visualizer_settings.items():
            self.settings[key] = value

        # Загружаем базовые настройки (только те, которых нет в настройках визуализатора)
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                basic_settings = json.load(f)
                for key, value in basic_settings.items():
                    if key not in self.visualizer_settings:
                        self.settings[key] = value
        else:
            # Базовые настройки по умолчанию
            default_basic_settings = {
            }
            for key, value in default_basic_settings.items():
                if key not in self.visualizer_settings:
                    self.settings[key] = value


    def save_settings(self):
        # Собираем настройки из полей ввода
        for key, entry in self.entries.items():
            self.settings[key] = entry.get()

        # Сохраняем базовые настройки в файл (исключаем настройки визуализатора)
        basic_settings = {k: v for k, v in self.settings.items()
                          if k not in self.visualizer_settings}
        with open("settings.json", "w") as f:
            json.dump(basic_settings, f, indent=4)

        # Применяем настройки к визуализатору
        if hasattr(self.parent, 'current_visualizer') and self.parent.current_visualizer:
            visualizer_settings = {k: v for k, v in self.settings.items()
                                   if k in self.visualizer_settings}
            if hasattr(self.parent.current_visualizer, 'apply_settings'):
                self.parent.current_visualizer.apply_settings(
                    visualizer_settings)

        self.window.destroy()
