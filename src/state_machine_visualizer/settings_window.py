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
        # Очищаем содержимое scrollable_frame
        for widget in self.scrollable_frame.winfo_children():
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
                entry = ttk.Entry(self.scrollable_frame, style='Custom.TEntry')
                entry.insert(0, value)
                entry.grid(row=i, column=1, padx=10, pady=6, sticky="ew")
                self.entries[key] = entry
        else:
            ttk.Label(self.scrollable_frame, text="Нет доступных настроек.", style='Settings.TLabel').grid(
                row=1, column=0, columnspan=2, padx=10, pady=20, sticky="w")

        self.scrollable_frame.columnconfigure(1, weight=1)

        # Фрейм для кнопки сохранения
        button_frame = ttk.Frame(
            self.scrollable_frame, style='Settings.TFrame')
        button_frame.grid(row=len(self.settings)+2, column=0,
                          columnspan=2, sticky="ew", pady=(20, 0))
        save_btn = ttk.Button(button_frame, text="Сохранить",
                              command=self.save_settings,
                              style='Primary.TButton')
        save_btn.pack(pady=10)

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
        self.center_window()

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
        canvas = tk.Canvas(
            container, bg=COLORS['settings_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=canvas.yview)

        # Фрейм для содержимого внутри Canvas
        self.scrollable_frame = ttk.Frame(canvas, style='Settings.TFrame')

        # Привязываем изменение размера фрейма к Canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.on_frame_configure(canvas)
        )

        # Создаем окно в Canvas для фрейма
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Упаковываем Canvas и Scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")

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

    # Кнопка 'Сохранить' теперь создаётся только в refresh_widgets

        # Привязываем обработчик изменения размера
        self.window.bind('<Configure>', self.on_window_configure)

        # Обновляем геометрию после создания виджетов
        self.window.after(100, self.adjust_window_size)

    def on_frame_configure(self, canvas):
        """Обновляет область прокрутки при изменении размера фрейма"""
        canvas.configure(scrollregion=canvas.bbox("all"))

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
