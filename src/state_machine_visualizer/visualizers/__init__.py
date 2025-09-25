from state_machine_visualizer.visualizers.base import BaseVisualizer
from state_machine_visualizer.visualizers.JuniorGardener import JuniorGardenerVisualizer
from state_machine_visualizer.visualizers.JuniorReader import JuniorReaderVisualizer


# Словарь для сопоставления платформ с классами визуализаторов
PLATFORM_VISUALIZER_CLASSES = {
    'junior-gardener': JuniorGardenerVisualizer,
    'junior-reader': JuniorReaderVisualizer,
    # Добавьте другие платформы по мере необходимости
}


def get_visualizer_class(platform: str):
    """Возвращает класс визуализатора для указанной платформы."""
    print(f"get_visualizer_class вызван с платформой: {platform}")
    print(f"Доступные платформы: {list(PLATFORM_VISUALIZER_CLASSES.keys())}")
    normalized_platform = platform.lower().replace('-', '_')
    # Пробуем найти по точному совпадению
    if platform in PLATFORM_VISUALIZER_CLASSES:
        return PLATFORM_VISUALIZER_CLASSES[platform]
    # Пробуем по нормализованному названию
    for key, cls in PLATFORM_VISUALIZER_CLASSES.items():
        if key.lower().replace('-', '_') == normalized_platform:
            return cls
    print("Класс визуализатора не найден")
    return None
