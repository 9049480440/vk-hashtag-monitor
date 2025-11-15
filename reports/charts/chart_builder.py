"""
Строитель графиков для отчётов.

Модуль координирует создание всех графиков,
используя DataAggregator для данных и ChartGenerator для генерации.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional

from database import Database
from reports.data_aggregator import DataAggregator
from reports.charts.chart_config import ChartConfig
from reports.charts.chart_generator import ChartGenerator


class ChartBuilder:
    """
    Строитель графиков для отчётов.

    Отвечает за оркестрацию создания всех графиков.
    Использует DataAggregator для получения данных
    и ChartGenerator для создания PNG файлов.
    """

    def __init__(
        self,
        database: Database,
        logger: logging.Logger,
        output_dir: str = 'temp_charts'
    ):
        """
        Инициализирует строитель графиков.

        Args:
            database: База данных для получения данных
            logger: Logger для логирования операций
            output_dir: Директория для сохранения графиков
        """
        self.database = database
        self.logger = logger
        self.output_dir = Path(output_dir)

        # Инициализация компонентов
        self.aggregator = DataAggregator(database, logger)
        self.config = ChartConfig()
        self.generator = ChartGenerator(self.config, logger)

        # Создание директории для графиков
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"ChartBuilder инициализирован (output_dir: {output_dir})")

    def build_all_charts(self) -> Optional[List[str]]:
        """
        Создаёт все графики для отчёта.

        Генерирует 3 графика:
        1. Столбчатая диаграмма публикаций
        2. Линейный график охвата (просмотры)
        3. Линейный график вовлечённости

        Returns:
            Optional[List[str]]: Список путей к созданным файлам
                                или None в случае ошибки

        Example:
            >>> builder = ChartBuilder(db, logger)
            >>> charts = builder.build_all_charts()
            >>> print(len(charts))
            3
        """
        self.logger.info("Начало генерации графиков")

        try:
            # Получение данных
            daily_data = self.aggregator.get_daily_dynamics()

            # Валидация данных
            if not daily_data:
                self.logger.warning("Нет данных для создания графиков")
                return None

            if len(daily_data) < 1:
                self.logger.warning(
                    f"Недостаточно данных для графиков: {len(daily_data)} дней "
                    "(минимум 1)"
                )
                return None

            self.logger.info(f"Данные получены: {len(daily_data)} дней")

            # Создание файлов графиков
            chart_files = []

            # 1. График публикаций
            publications_path = str(self.output_dir / 'publications.png')
            if self.generator.generate_publications_chart(daily_data, publications_path):
                chart_files.append(publications_path)
                self.logger.info("График публикаций создан")
            else:
                self.logger.error("Не удалось создать график публикаций")

            # 2. График охвата
            reach_path = str(self.output_dir / 'reach.png')
            if self.generator.generate_reach_chart(daily_data, reach_path):
                chart_files.append(reach_path)
                self.logger.info("График охвата создан")
            else:
                self.logger.error("Не удалось создать график охвата")

            # 3. График вовлечённости
            engagement_path = str(self.output_dir / 'engagement.png')
            if self.generator.generate_engagement_chart(daily_data, engagement_path):
                chart_files.append(engagement_path)
                self.logger.info("График вовлечённости создан")
            else:
                self.logger.error("Не удалось создать график вовлечённости")

            # Проверка результатов
            if not chart_files:
                self.logger.error("Не удалось создать ни одного графика")
                return None

            self.logger.info(
                f"Генерация графиков завершена: {len(chart_files)}/3 успешно"
            )

            return chart_files

        except Exception as e:
            self.logger.error(f"Ошибка при создании графиков: {e}", exc_info=True)
            return None

    def cleanup_charts(self, file_paths: List[str]) -> None:
        """
        Удаляет временные файлы графиков.

        Args:
            file_paths: Список путей к файлам для удаления

        Example:
            >>> builder.cleanup_charts(chart_files)
        """
        self.logger.info("Очистка временных файлов графиков")

        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    self.logger.debug(f"Удалён файл: {file_path}")
            except Exception as e:
                self.logger.warning(f"Не удалось удалить {file_path}: {e}")

        # Попытка удалить директорию если пуста
        try:
            if self.output_dir.exists() and not list(self.output_dir.iterdir()):
                self.output_dir.rmdir()
                self.logger.debug(f"Удалена пустая директория: {self.output_dir}")
        except Exception as e:
            self.logger.debug(f"Не удалось удалить директорию {self.output_dir}: {e}")
