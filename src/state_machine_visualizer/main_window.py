import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os

from .style import Style
from .theme import COLORS, SIZES
from .settings_window import SettingsWindow
from .simulator import CGMLParser
from .visualizers import get_visualizer_class


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Визуализатор машин состояний")
        self.geometry("1000x600")
        self.configure(bg=COLORS['main_bg'])

        # Инициализация стилей
        self.style = Style()

        # Переменная для хранения пути к файлу
        self.file_path = tk.StringVar()

        # Переменные для хранения данных
        self.cgml_parser = CGMLParser()
        self.current_visualizer = None
        self.state_machine_data = None

        self.create_widgets()

    def create_widgets(self):
        # Создание сайдбара
        sidebar = ttk.Frame(
            self, width=SIZES['sidebar_width'], style='Sidebar.TFrame')
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Заголовок сайдбара
        sidebar_title = ttk.Label(
            sidebar, text="Меню", style='SidebarTitle.TLabel')
        sidebar_title.pack(pady=20)

        # Кнопки в сайдбаре
        self.load_btn = ttk.Button(sidebar, text="Загрузить файл",
                                   command=self.load_file, style='Sidebar.TButton')
        self.load_btn.pack(fill=tk.X, padx=10, pady=5)

        self.run_btn = ttk.Button(sidebar, text="Запустить",
                                  command=self.run_simulation, style='Sidebar.TButton', state='disabled')
        self.run_btn.pack(fill=tk.X, padx=10, pady=5)

        self.settings_btn = ttk.Button(sidebar, text="Настройки запуска",
                                       command=self.open_settings, style='Sidebar.TButton', state='disabled')
        self.settings_btn.pack(fill=tk.X, padx=10, pady=5)

        # Основная область для модуля
        self.main_area = ttk.Frame(self, style='Main.TFrame')
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH,
                            expand=True, padx=20, pady=20)

        # Заглушка для будущего модуля
        placeholder = ttk.Label(self.main_area,
                                text="Загрузите GraphML файл для начала работы",
                                style='Title.TLabel')
        placeholder.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def load_file(self):
        """Загружает GraphML файл и парсит его с помощью CGMLParser."""
        file_path = filedialog.askopenfilename(
            title="Выберите GraphML файл",
            filetypes=(("GraphML файлы", "*.graphml"),
                       ("Все файлы", "*.*"),)
        )

        if file_path:
            try:
                # Читаем файл
                with open(file_path, 'r', encoding='utf-8') as f:
                    graphml_content = f.read()

                # Парсим с помощью CGMLParser
                elements = self.cgml_parser.parse_cgml(graphml_content)

                # Получаем первую машину состояний
                if elements.state_machines:
                    # Берем первую машину состояний
                    first_machine_id = list(elements.state_machines.keys())[0]
                    state_machine = elements.state_machines[first_machine_id]

                    # Извлекаем название платформы
                    platform = state_machine.platform
                    print(f"Найдена платформа: {platform}")

                    # Сохраняем данные машины состояний
                    self.state_machine_data = {
                        'platform': platform,
                        'name': state_machine.name,
                        'states': state_machine.states,
                        'transitions': state_machine.transitions,
                        'components': state_machine.components,
                        'meta': state_machine.meta,
                        'cgml_state_machine': state_machine  # Сохраняем полный CGMLStateMachine
                    }

                    # Показываем имя файла в заголовке приложения
                    filename = os.path.basename(file_path)
                    self.title(f"Визуализатор машин состояний [{filename}]")

                    # Проверяем, совпадает ли платформа с текущей
                    current_platform = None
                    if self.current_visualizer and hasattr(self.current_visualizer, 'state_machine_data'):
                        current_platform = self.current_visualizer.state_machine_data.get('platform')
                    if current_platform and str(current_platform).lower() == str(platform).lower():
                        print(f"Платформа совпадает ({platform}), не перезагружаем компонент.")
                        # Только обновляем данные и UI, не пересоздаём визуализатор
                        self.file_path.set(file_path)
                        self.enable_buttons()
                        messagebox.showinfo(
                            "Успех", f"Файл загружен успешно!\nПлатформа: {platform}")
                        return

                    # Импортируем модуль с нужным визуализатором
                    print(f"Загружаю визуализатор для платформы: {platform}")
                    self.load_visualizer(platform)

                    self.file_path.set(file_path)
                    self.enable_buttons()  # Разблокируем кнопки после успешной загрузки
                    messagebox.showinfo(
                        "Успех", f"Файл загружен успешно!\nПлатформа: {platform}")

                else:
                    messagebox.showerror(
                        "Ошибка", "В файле не найдены машины состояний")
                    self.disable_buttons()  # Блокируем кнопки при ошибке

            except Exception as e:
                messagebox.showerror(
                    "Ошибка", f"Ошибка при загрузке файла:\n{str(e)}")
                print(f"Ошибка при загрузке файла: {e}")
                self.disable_buttons()  # Блокируем кнопки при ошибке

    def load_visualizer(self, platform: str):
        """Загружает визуализатор для указанной платформы."""
        try:
            print(f"Начинаю загрузку визуализатора для платформы: {platform}")

            # Очищаем основную область
            for widget in self.main_area.winfo_children():
                widget.destroy()

            # Получаем класс визуализатора
            print(f"Ищу класс визуализатора для платформы: {platform}")
            visualizer_class = get_visualizer_class(platform)
            print(f"Найденный класс визуализатора: {visualizer_class}")

            if visualizer_class:
                # Создаем экземпляр визуализатора
                self.current_visualizer = visualizer_class(
                    self.main_area, self.state_machine_data)

                # Получаем виджет и размещаем его
                visualizer_widget = self.current_visualizer.get_widget()
                if visualizer_widget:
                    visualizer_widget.pack(fill=tk.BOTH, expand=True)
                else:
                    self.show_error_message(
                        f"Ошибка создания визуализатора для платформы {platform}")
                    self.disable_buttons()  # Блокируем кнопки при ошибке

            else:
                self.show_error_message(
                    f"Визуализатор для платформы '{platform}' не найден")
                self.disable_buttons()  # Блокируем кнопки при ошибке

        except Exception as e:
            self.show_error_message(
                f"Ошибка при загрузке визуализатора:\n{str(e)}")
            print(f"Ошибка при загрузке визуализатора: {e}")
            self.disable_buttons()  # Блокируем кнопки при ошибке

    def run_simulation(self):
        """Запускает симуляцию машины состояний."""
        if not self.current_visualizer:
            messagebox.showwarning(
                "Предупреждение", "Сначала загрузите файл с машиной состояний")
            return

        try:
            # Запускаем машину состояний через визуализатор
            result = self.current_visualizer.run_state_machine()

            if result:
                # Обновляем отображение через функцию визуализатора
                self.current_visualizer.update_with_result(result)

                # Проверяем, был ли краш Gardener
                if hasattr(result, 'gardener_crashed') and result.gardener_crashed:
                    messagebox.showwarning("Предупреждение",
                                           "Gardener упал во время выполнения!\n"
                                           "Поле отображается в состоянии до краша.")
                else:
                    messagebox.showinfo(
                        "Симуляция", "Симуляция завершена! Отображение обновлено.")
            else:
                messagebox.showerror(
                    "Ошибка", "Не удалось запустить симуляцию")

        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Ошибка при запуске симуляции:\n{str(e)}")
            print(f"Ошибка при запуске симуляции: {e}")

    def show_error_message(self, message: str):
        """Показывает сообщение об ошибке в основной области."""
        for widget in self.main_area.winfo_children():
            widget.destroy()

        error_label = ttk.Label(self.main_area, text=message,
                                style='Title.TLabel', foreground='red')
        error_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def enable_buttons(self):
        """Разблокирует кнопки после загрузки файла."""
        self.run_btn.config(state='normal')
        self.settings_btn.config(state='normal')

    def disable_buttons(self):
        """Блокирует кнопки при отсутствии загруженного файла."""
        self.run_btn.config(state='disabled')
        self.settings_btn.config(state='disabled')

    def open_settings(self):
        """Открывает окно настроек."""
        if not self.current_visualizer:
            messagebox.showwarning(
                "Предупреждение", "Сначала загрузите файл с машиной состояний")
            return

        # Получаем актуальные настройки от текущего визуализатора
        visualizer_settings = {}
        if hasattr(self.current_visualizer, 'get_settings'):
            visualizer_settings = self.current_visualizer.get_settings()

        settings_win = SettingsWindow(self, visualizer_settings)
        if hasattr(settings_win, 'refresh_widgets'):
            settings_win.refresh_widgets(visualizer_settings)

        # Переопределяем метод save_settings, чтобы сохранять настройки в MainApp
        original_save_settings = settings_win.save_settings

        def save_and_store():
            self.visualizer_settings = settings_win.settings.copy()
            original_save_settings()
        settings_win.save_settings = save_and_store
