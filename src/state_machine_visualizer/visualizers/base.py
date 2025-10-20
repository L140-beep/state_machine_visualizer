from abc import ABC, abstractmethod
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

    def get_settings(self):
        """Возвращает настройки визуализатора для окна настроек."""
        return {}

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
