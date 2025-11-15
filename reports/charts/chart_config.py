"""
Настройки стилей и конфигурация для графиков.

Модуль содержит класс ChartConfig с настройками цветов,
шрифтов, размеров и локализации для всех графиков.
"""

from typing import Dict, List
import matplotlib.pyplot as plt


class ChartConfig:
    """
    Класс конфигурации для графиков.

    Содержит все настройки стилей, цветов, размеров
    для единообразного оформления графиков.
    """

    # Цветовая палитра
    PRIMARY_COLOR = '#3b5998'      # Основной цвет (синий VK)
    ACCENT_COLOR = '#ff6b6b'       # Акцентный цвет (красный)
    SUCCESS_COLOR = '#51cf66'      # Цвет успеха (зелёный)
    WARNING_COLOR = '#ffd43b'      # Цвет предупреждения (жёлтый)
    INFO_COLOR = '#339af0'         # Информационный цвет (голубой)
    BACKGROUND_COLOR = '#ffffff'   # Фоновый цвет
    GRID_COLOR = '#e9ecef'         # Цвет сетки

    # Размеры графиков
    FIGURE_WIDTH = 12              # Ширина в дюймах
    FIGURE_HEIGHT = 6              # Высота в дюймах
    DPI = 100                      # Разрешение

    # Размеры шрифтов
    TITLE_FONTSIZE = 16            # Размер заголовка
    LABEL_FONTSIZE = 12            # Размер подписей осей
    TICK_FONTSIZE = 10             # Размер меток на осях
    LEGEND_FONTSIZE = 10           # Размер текста легенды

    # Настройки сетки
    GRID_ALPHA = 0.3               # Прозрачность сетки
    GRID_LINESTYLE = '--'          # Стиль линий сетки

    # Локализация
    MONTHS_RU: Dict[int, str] = {
        1: 'Янв', 2: 'Фев', 3: 'Мар', 4: 'Апр',
        5: 'Май', 6: 'Июн', 7: 'Июл', 8: 'Авг',
        9: 'Сен', 10: 'Окт', 11: 'Ноя', 12: 'Дек'
    }

    WEEKDAYS_RU: List[str] = [
        'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'
    ]

    @classmethod
    def apply_style(cls) -> None:
        """
        Применяет глобальные настройки стиля для matplotlib.

        Настраивает шрифты, цвета и другие параметры
        для всех создаваемых графиков.
        """
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['font.size'] = cls.TICK_FONTSIZE
        plt.rcParams['axes.titlesize'] = cls.TITLE_FONTSIZE
        plt.rcParams['axes.labelsize'] = cls.LABEL_FONTSIZE
        plt.rcParams['xtick.labelsize'] = cls.TICK_FONTSIZE
        plt.rcParams['ytick.labelsize'] = cls.TICK_FONTSIZE
        plt.rcParams['legend.fontsize'] = cls.LEGEND_FONTSIZE
        plt.rcParams['figure.facecolor'] = cls.BACKGROUND_COLOR
        plt.rcParams['axes.facecolor'] = cls.BACKGROUND_COLOR
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = cls.GRID_ALPHA
        plt.rcParams['grid.linestyle'] = cls.GRID_LINESTYLE
        plt.rcParams['grid.color'] = cls.GRID_COLOR

    @staticmethod
    def format_number(number: int) -> str:
        """
        Форматирует число с пробелами для тысяч.

        Args:
            number: Число для форматирования

        Returns:
            str: Отформатированное число

        Example:
            >>> ChartConfig.format_number(1234567)
            '1 234 567'
        """
        return f"{number:,}".replace(',', ' ')
