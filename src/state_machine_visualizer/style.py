import tkinter.ttk as ttk
from state_machine_visualizer.theme import COLORS, FONTS, SIZES


class Style:
    def __init__(self):
        self.style = ttk.Style()
        self.configure_styles()

    def configure_styles(self):
        # Настройка основной темы
        self.style.theme_use('clam')

        # Стиль для сайдбара
        self.style.configure('Sidebar.TFrame', background=COLORS['sidebar_bg'])

        # Стиль для кнопок сайдбара - центрирование текста
        self.style.configure('Sidebar.TButton',
                             background=COLORS['sidebar_bg'],
                             foreground=COLORS['sidebar_fg'],
                             borderwidth=0,
                             focuscolor=COLORS['sidebar_bg'],
                             font=FONTS['button'],
                             padding=SIZES['button_padding'],
                             anchor='center')  # Центрирование текста

        self.style.map('Sidebar.TButton',
                       background=[('active', COLORS['sidebar_active']),
                                   ('pressed', COLORS['sidebar_active']),
                                   ('disabled', COLORS['sidebar_disabled'])],
                       foreground=[('active', COLORS['sidebar_fg']),
                                   ('pressed', COLORS['sidebar_fg']),
                                   ('disabled', COLORS['sidebar_disabled_fg'])])

        # Стиль для основной области
        self.style.configure('Main.TFrame', background=COLORS['main_bg'])

        # Стиль для обычных кнопок
        self.style.configure('Primary.TButton',
                             background=COLORS['button_bg'],
                             foreground=COLORS['button_fg'],
                             borderwidth=0,
                             focuscolor=COLORS['button_bg'],
                             font=FONTS['button'],
                             padding=(15, 10),
                             anchor='center')

        self.style.map('Primary.TButton',
                       background=[('active', COLORS['button_active']),
                                   ('pressed', COLORS['button_active']),
                                   ('disabled', COLORS['button_disabled'])],
                       foreground=[('disabled', COLORS['button_disabled_fg'])])

        # Стиль для полей ввода
        self.style.configure('Custom.TEntry',
                             fieldbackground=COLORS['entry_bg'],
                             foreground=COLORS['entry_fg'],
                             borderwidth=1,
                             focusthickness=2,
                             padding=(8, 6))

        self.style.map('Custom.TEntry',
                       bordercolor=[('focus', COLORS['primary']),
                                    ('!focus', COLORS['entry_border'])])

        # Стиль для меток
        self.style.configure('Title.TLabel',
                             background=COLORS['main_bg'],
                             foreground=COLORS['main_fg'],
                             font=FONTS['title'])

        self.style.configure('Normal.TLabel',
                             background=COLORS['main_bg'],
                             foreground=COLORS['main_fg'],
                             font=FONTS['normal'])

        self.style.configure('SidebarTitle.TLabel',
                             background=COLORS['sidebar_bg'],
                             foreground=COLORS['sidebar_fg'],
                             # Используем новый шрифт
                             font=FONTS['sidebar_title'],
                             anchor='center')  # Центрирование заголовка

        # Стиль для окна настроек
        self.style.configure(
            'Settings.TFrame', background=COLORS['settings_bg'])
        self.style.configure('Settings.TLabel',
                             background=COLORS['settings_bg'],
                             foreground=COLORS['settings_fg'],
                             font=FONTS['normal'])
