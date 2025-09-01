from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import importlib
from ..simulator import StateMachineResult


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
    
    def run_state_machine(self):
        """Запускает машину состояний и возвращает результат."""
        # Базовая реализация - возвращает None
        # Должна быть переопределена в конкретных визуализаторах
        return None


# Словарь для сопоставления платформ с модулями визуализаторов
PLATFORM_VISUALIZERS = {
    'junior-gardener': 'JuniorGardener',
    'junior-reader': 'JuniorReader',
    # Добавьте другие платформы по мере необходимости
}


def get_visualizer_class(platform: str):
    """Возвращает класс визуализатора для указанной платформы."""
    print(f"get_visualizer_class вызван с платформой: {platform}")
    print(f"Доступные платформы: {list(PLATFORM_VISUALIZERS.keys())}")
    
    # Нормализуем название платформы (приводим к нижнему регистру и заменяем дефисы на подчеркивания)
    normalized_platform = platform.lower().replace('-', '_')
    print(f"Нормализованная платформа: {normalized_platform}")
    
    # Ищем точное совпадение
    if platform in PLATFORM_VISUALIZERS:
        module_name = PLATFORM_VISUALIZERS[platform]
        print(f"Найдено точное совпадение, модуль: {module_name}")
        try:
            module = importlib.import_module(f'.{module_name}', 'state_machine_visualizer.visualizers')
            print(f"Модуль импортирован: {module}")
            visualizer_class = getattr(module, f'{module_name}Visualizer')
            print(f"Класс визуализатора найден: {visualizer_class}")
            return visualizer_class
        except (ImportError, AttributeError) as e:
            print(f"Ошибка при импорте модуля {module_name}: {e}")
            return None
    
    # Ищем по нормализованному названию
    print("Ищу по нормализованному названию...")
    for key, value in PLATFORM_VISUALIZERS.items():
        normalized_key = key.lower().replace('-', '_')
        print(f"Сравниваю {normalized_key} с {normalized_platform}")
        if normalized_key == normalized_platform:
            print(f"Найдено совпадение по нормализованному названию, модуль: {value}")
            try:
                module = importlib.import_module(f'.{value}', 'state_machine_visualizer.visualizers')
                print(f"Модуль импортирован: {module}")
                visualizer_class = getattr(module, f'{value}Visualizer')
                print(f"Класс визуализатора найден: {visualizer_class}")
                return visualizer_class
            except (ImportError, AttributeError) as e:
                print(f"Ошибка при импорте модуля {value}: {e}")
                return None
    
    print("Класс визуализатора не найден")
    return None
