"""
Генератор графиков для визуализации данных.

Модуль создает PNG-графики на основе данных:
столбчатые диаграммы и линейные графики.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from reports.charts.chart_config import ChartConfig


class ChartGenerator:
    """
    Генератор графиков для отчётов.

    Отвечает ТОЛЬКО за создание отдельных графиков.
    НЕ знает про базу данных, работает с готовыми данными.
    """

    def __init__(self, config: ChartConfig, logger: logging.Logger):
        """
        Инициализирует генератор графиков.

        Args:
            config: Конфигурация стилей графиков
            logger: Logger для логирования операций
        """
        self.config = config
        self.logger = logger

        # Применение глобальных настроек стиля
        self.config.apply_style()

    def generate_publications_chart(
        self,
        daily_data: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        """
        Генерирует столбчатую диаграмму публикаций по дням.

        Args:
            daily_data: Список с данными по дням (из DataAggregator)
            output_path: Путь для сохранения PNG файла

        Returns:
            bool: True если график успешно создан

        Example:
            >>> data = [{'date': '2024-11-01', 'new_posts': 5}, ...]
            >>> generator.generate_publications_chart(data, 'chart.png')
            True
        """
        try:
            self.logger.info("Генерация графика публикаций")

            if not daily_data:
                self.logger.warning("Нет данных для графика публикаций")
                return False

            # Подготовка данных
            dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_data]
            posts = [d['new_posts'] for d in daily_data]

            # Создание графика
            fig, ax = plt.subplots(
                figsize=(self.config.FIGURE_WIDTH, self.config.FIGURE_HEIGHT),
                dpi=self.config.DPI
            )

            # Столбчатая диаграмма
            ax.bar(dates, posts, color=self.config.PRIMARY_COLOR, alpha=0.8)

            # Заголовок и подписи
            ax.set_title('Динамика публикаций по дням', fontweight='bold')
            ax.set_xlabel('Дата')
            ax.set_ylabel('Количество новых постов')

            # Форматирование оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            plt.xticks(rotation=45, ha='right')

            # Сетка
            ax.grid(True, alpha=self.config.GRID_ALPHA)

            # Компактное размещение
            plt.tight_layout()

            # Сохранение
            plt.savefig(output_path, dpi=self.config.DPI, bbox_inches='tight')
            plt.close(fig)

            self.logger.info(f"График публикаций сохранён: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка генерации графика публикаций: {e}")
            return False

    def generate_reach_chart(
        self,
        daily_data: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        """
        Генерирует линейный график роста охвата (просмотры).

        Args:
            daily_data: Список с данными по дням
            output_path: Путь для сохранения PNG файла

        Returns:
            bool: True если график успешно создан

        Example:
            >>> data = [{'date': '2024-11-01', 'views': 1500}, ...]
            >>> generator.generate_reach_chart(data, 'reach.png')
            True
        """
        try:
            self.logger.info("Генерация графика охвата")

            if not daily_data:
                self.logger.warning("Нет данных для графика охвата")
                return False

            # Подготовка данных
            dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_data]
            views = [d['views'] for d in daily_data]

            # Создание графика
            fig, ax = plt.subplots(
                figsize=(self.config.FIGURE_WIDTH, self.config.FIGURE_HEIGHT),
                dpi=self.config.DPI
            )

            # Линейный график с маркерами
            ax.plot(
                dates, views,
                color=self.config.ACCENT_COLOR,
                linewidth=2.5,
                marker='o',
                markersize=6,
                label='Просмотры'
            )

            # Заголовок и подписи
            ax.set_title('Рост охвата (просмотры)', fontweight='bold')
            ax.set_xlabel('Дата')
            ax.set_ylabel('Количество просмотров')

            # Форматирование оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            plt.xticks(rotation=45, ha='right')

            # Форматирование оси Y (с пробелами для тысяч)
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: self.config.format_number(int(x)))
            )

            # Сетка
            ax.grid(True, alpha=self.config.GRID_ALPHA)

            # Компактное размещение
            plt.tight_layout()

            # Сохранение
            plt.savefig(output_path, dpi=self.config.DPI, bbox_inches='tight')
            plt.close(fig)

            self.logger.info(f"График охвата сохранён: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка генерации графика охвата: {e}")
            return False

    def generate_engagement_chart(
        self,
        daily_data: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        """
        Генерирует линейный график вовлечённости (лайки, комментарии, репосты).

        Args:
            daily_data: Список с данными по дням
            output_path: Путь для сохранения PNG файла

        Returns:
            bool: True если график успешно создан

        Example:
            >>> data = [{'date': '2024-11-01', 'likes': 100, ...}, ...]
            >>> generator.generate_engagement_chart(data, 'engagement.png')
            True
        """
        try:
            self.logger.info("Генерация графика вовлечённости")

            if not daily_data:
                self.logger.warning("Нет данных для графика вовлечённости")
                return False

            # Подготовка данных
            dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in daily_data]
            likes = [d['likes'] for d in daily_data]
            comments = [d['comments'] for d in daily_data]
            reposts = [d['reposts'] for d in daily_data]

            # Создание графика
            fig, ax = plt.subplots(
                figsize=(self.config.FIGURE_WIDTH, self.config.FIGURE_HEIGHT),
                dpi=self.config.DPI
            )

            # Три линии для разных метрик
            ax.plot(
                dates, likes,
                color=self.config.ACCENT_COLOR,
                linewidth=2,
                marker='o',
                markersize=5,
                label='Лайки'
            )

            ax.plot(
                dates, comments,
                color=self.config.SUCCESS_COLOR,
                linewidth=2,
                marker='s',
                markersize=5,
                label='Комментарии'
            )

            ax.plot(
                dates, reposts,
                color=self.config.INFO_COLOR,
                linewidth=2,
                marker='^',
                markersize=5,
                label='Репосты'
            )

            # Заголовок и подписи
            ax.set_title('Вовлечённость аудитории', fontweight='bold')
            ax.set_xlabel('Дата')
            ax.set_ylabel('Количество')

            # Форматирование оси X
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            plt.xticks(rotation=45, ha='right')

            # Форматирование оси Y
            ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: self.config.format_number(int(x)))
            )

            # Легенда
            ax.legend(loc='best', framealpha=0.9)

            # Сетка
            ax.grid(True, alpha=self.config.GRID_ALPHA)

            # Компактное размещение
            plt.tight_layout()

            # Сохранение
            plt.savefig(output_path, dpi=self.config.DPI, bbox_inches='tight')
            plt.close(fig)

            self.logger.info(f"График вовлечённости сохранён: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка генерации графика вовлечённости: {e}")
            return False
