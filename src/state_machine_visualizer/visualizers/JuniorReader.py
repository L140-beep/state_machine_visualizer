import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

from state_machine_visualizer.visualizers.base import BaseVisualizer
from state_machine_visualizer.simulator import (
    StateMachineResult,
    run_state_machine,
    StateMachine
)


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
        self.message = 'Привет, мир!'
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
            label = ttk.Label(
                self.signals_list_frame,
                text=display_signal or '',
                font=("Consolas", 10),
                anchor="w",
                justify=tk.LEFT
            )
            label.grid(row=i, column=0, sticky="w", padx=10, pady=2)
        self.signals_list_frame.update_idletasks()
        self.signals_list_frame.master.configure(
            scrollregion=self.signals_list_frame.master.bbox("all")
        )

    def get_settings(self):
        """Возвращает настройки визуализатора для окна настроек."""
        return {
            "Сообщение для чтения": self.message,
        }

    def get_settings_values(self, widgets_dict: Dict[str, ttk.Widget]) -> Dict[str, Any]:
        return {
            'Сообщение для чтения': widgets_dict["Сообщение для чтения"].get(),
        }

    def apply_settings(self, settings: Dict[str, Any]):
        """Применяет настройки к визуализатору
          и сохраняет их в атрибутах экземпляра."""
        try:
            self.message = settings.get("Сообщение для чтения", self.message)
        except (ValueError, TypeError) as e:
            print(f"Ошибка при применении настроек: {e}")

    def draw_settings(self, parent_frame):  # type: ignore
        message = ttk.Entry(parent_frame,
                            style='Custom.TEntry')
        message.insert(0, self.message)
        message.grid(row=1, column=1, padx=10, pady=6, sticky="ew")
        ttk.Label(
            parent_frame,
            text='Сообщение для чтения',
            style='Settings.TLabel'
        ).grid(row=1, column=0, padx=10, pady=6, sticky="w")

        return {
            "Сообщение для чтения": message,
        }

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
