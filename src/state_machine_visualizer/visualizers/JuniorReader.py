import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from state_machine_visualizer.visualizers.base import BaseVisualizer
from state_machine_visualizer.simulator import StateMachineResult, run_state_machine, StateMachine


class JuniorReaderVisualizer(BaseVisualizer):
    def update_state_machine_data(self, new_data: Dict[str, Any]):
        """Обновляет данные машины состояний и UI для Reader."""
        self.state_machine_data = new_data
        # Обновляем инфо-лейбл, если он есть
        if hasattr(self, 'widget') and self.widget:
            for child in self.widget.winfo_children():
                if isinstance(child, ttk.Label) and "Платформа:" in child.cget("text"):
                    platform = new_data.get('platform', 'Неизвестно')
                    name = new_data.get('name', 'Без названия')
                    states_count = len(new_data.get('states', {}))
                    transitions_count = len(new_data.get('transitions', {}))
                    info_text = f"Платформа: {platform}\nНазвание: {name}\nСостояний: {states_count}\nПереходов: {transitions_count}"
                    child.config(text=info_text)
        # Можно добавить обновление списка сигналов, если требуется

    def __init__(self, parent, state_machine_data: Dict[str, Any]):
        super().__init__(parent, state_machine_data)

    def create_initial_view(self):
        """Создает исходное отображение Junior Reader: только скроллируемый список вызыванных сигналов."""
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = ttk.Label(main_frame, text="Junior Reader - Сигналы",
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 15))

        # Фрейм для скроллируемого списка сигналов
        signals_frame = ttk.Frame(main_frame)
        signals_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(signals_frame, bg='white',
                           highlightthickness=1, highlightbackground='#cccccc')
        v_scrollbar = ttk.Scrollbar(
            signals_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.signals_list_frame = ttk.Frame(canvas)
        canvas.create_window(
            (0, 0), window=self.signals_list_frame, anchor="nw")

        self.widget = main_frame

        # Изначально пусто, заполняется в update_with_result
        self.update_signals_list([])

    def update_signals_list(self, signals):
        """Обновляет скроллируемый список сигналов с маппингом."""
        signal_map = {
            'impulseA': 'Импульс А',
            'impulseB': 'Импульс Б',
            'impulseC': 'Импульс В',
        }
        for widget in self.signals_list_frame.winfo_children():
            widget.destroy()
        for i, signal in enumerate(signals):
            display_signal = signal_map.get(signal, signal)
            label = ttk.Label(self.signals_list_frame, text=display_signal, font=(
                "Consolas", 10), anchor="w", justify=tk.LEFT)
            label.grid(row=i, column=0, sticky="w", padx=10, pady=2)
        self.signals_list_frame.update_idletasks()
        self.signals_list_frame.master.configure(
            scrollregion=self.signals_list_frame.master.bbox("all"))

    def get_settings(self):
        """Возвращает настройки визуализатора для окна настроек."""
        if hasattr(self, 'settings') and self.settings:
            return self.settings.copy()
        return {
            "Сообщение для чтения": "Привет, мир!",
        }

    def apply_settings(self, settings):
        """Применяет настройки к визуализатору и сохраняет их в атрибутах экземпляра."""
        try:
            self.settings = settings.copy()
            # Пример: обновление размера шрифта
            if "Размер шрифта" in settings:
                font_size = int(settings["Размер шрифта"])
                if hasattr(self, 'widget'):
                    for child in self.widget.winfo_children():
                        if isinstance(child, ttk.Label):
                            current_font = child.cget("font")
                            if isinstance(current_font, str):
                                new_font = ("Consolas", font_size)
                            else:
                                new_font = list(current_font)
                                new_font[1] = font_size
                                new_font = tuple(new_font)
                            child.configure(font=new_font)
        except (ValueError, TypeError) as e:
            print(f"Ошибка при применении настроек: {e}")

    def run_state_machine(self) -> None | StateMachineResult:
        return self._start_simulation()

    def _start_simulation(self):
        """Запускает симуляцию машины состояний."""
        try:
            # Получаем настройки для чтения из self.settings
            settings = getattr(self, 'settings', self.get_settings())
            message = settings.get("Сообщение для чтения", "Привет, мир!")
            speed = float(settings.get("Скорость чтения", "1.0"))

            # Создаем машину состояний из данных
            if not self.state_machine_data:
                raise ValueError("Данные машины состояний не загружены")

            # Получаем CGMLStateMachine из уже распарсенных данных
            cgml_sm = self.state_machine_data.get('cgml_state_machine')
            if not cgml_sm:
                raise ValueError("CGMLStateMachine не найден в данных")

            # Создаем StateMachine с параметрами для Reader
            sm = StateMachine(cgml_sm, sm_parameters={
                              'message': message, 'speed': speed})
            print(cgml_sm)
            # Запускаем машину состояний
            print(
                f"Запускаю машину состояний Junior Reader с сообщением: '{message}', скорость: {speed}")
            result = run_state_machine(sm, [], timeout_sec=10.0)

            return result

        except Exception as e:
            print(f"Ошибка при запуске машины состояний: {e}")
            return None

    def update_with_result(self, result: StateMachineResult):
        """Обновляет скроллируемый список сигналов по результату работы машины состояний."""
        print(f"Обновляю отображение Junior Reader с результатом: {result}")
        if hasattr(result, 'called_signals'):
            self.update_signals_list(result.called_signals)
