from abc import ABC, abstractmethod
from tkinter import ttk
from typing import Any, Dict
import threading
from state_machine_visualizer.simulator import StateMachineResult


class BaseVisualizer(ABC):
    """Базовый класс для всех визуализаторов."""

    def __init__(self, parent, state_machine_data: Dict[str, Any]):
        self.parent = parent
        self.state_machine_data = state_machine_data
        self.widget = None
        self.create_initial_view()

    @abstractmethod
    def create_initial_view(self):
        """Создает исходное отображение машины состояний."""
        pass

    @abstractmethod
    def update_with_result(self, result: StateMachineResult):
        """Обновляет отображение с результатом работы машины состояний."""
        pass

    def get_widget(self):
        """Возвращает виджет визуализатора."""
        return self.widget

    @abstractmethod
    def get_settings_values(self, widgets_dict: Dict[str, ttk.Widget]) -> Dict[str, Any]:
        """Получает значения из виджетов настроек.

        Args:
            widgets_dict: словарь с виджетами {имя_настройки: виджет}
        Returns:
            Dict[str, Any]: словарь с значениями настроек
        """
        pass

    @abstractmethod
    def draw_settings(self, parent_frame) -> Dict[str, ttk.Widget]:
        """Отрисовывает настройки визуализатора в указанном фрейме.

        Args:
            parent_frame: родительский фрейм для виджетов настроек

        Returns:
            dict: виджеты настроек, чтобы потом получить из них значения
        """
        pass

    def apply_settings(self, settings):
        """Применяет настройки к визуализатору."""
        pass

    @abstractmethod
    def _start_simulation(self) -> None | StateMachineResult:
        """Запускает симуляцию машины состояний. Должна быть реализована в конкретных визуализаторах."""
        pass

    def run_state_machine(self) -> None | StateMachineResult:
        """Запускает машину состояний в отдельном потоке."""
        thread = threading.Thread(target=self._start_simulation)
        thread.daemon = True  # Поток завершится при закрытии программы
        thread.start()
