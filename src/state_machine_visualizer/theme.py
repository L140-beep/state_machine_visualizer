# Цветовая схема приложения
COLORS = {
    'primary': '#3498db',
    'secondary': '#2c3e50',
    'success': '#27ae60',
    'danger': '#e74c3c',
    'warning': '#f39c12',
    'info': '#17a2b8',
    'light': '#ecf0f1',
    'dark': '#34495e',
    'sidebar_bg': '#2c3e50',
    'sidebar_fg': '#ecf0f1',
    'sidebar_active': '#34495e',
    'sidebar_disabled': '#1a252f',
    'sidebar_disabled_fg': '#7f8c8d',
    'main_bg': '#ecf0f1',
    'main_fg': '#2c3e50',
    'button_bg': '#3498db',
    'button_fg': 'white',
    'button_active': '#2980b9',
    'button_disabled': '#bdc3c7',
    'button_disabled_fg': '#7f8c8d',
    'settings_bg': '#ffffff',
    'settings_fg': '#2c3e50',
    'entry_bg': '#ffffff',
    'entry_fg': '#2c3e50',
    'entry_border': '#bdc3c7'
}

SIZES = {
    'sidebar_width': 250,  # Немного уменьшил для баланса
    'button_padding': (20, 15),  # Увеличил вертикальные отступы
    'border_radius': 4,
    'font_family': 'Segoe UI'
}

FONTS = {
    'title': (SIZES['font_family'], 16, 'bold'),
    'subtitle': (SIZES['font_family'], 14, 'bold'),
    'normal': (SIZES['font_family'], 11),
    # Увеличил размер шрифта кнопок
    'button': (SIZES['font_family'], 12, 'bold'),
    # Отдельный шрифт для заголовка
    'sidebar_title': (SIZES['font_family'], 18, 'bold')
}
