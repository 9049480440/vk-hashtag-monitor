"""
Основной репортер для Google Sheets.

Модуль координирует генерацию отчёта в Google Sheets,
используя агрегатор данных, клиент API и форматтер.
"""

import logging
from typing import Optional

from database import Database
from config import Config
from reports.base_reporter import BaseReporter
from reports.data_aggregator import DataAggregator
from reports.google_sheets.sheets_client import GoogleSheetsClient
from reports.google_sheets.sheets_formatter import SheetsFormatter


class GoogleSheetsReporter(BaseReporter):
    """
    Репортер для генерации отчётов в Google Sheets.

    Реализует бизнес-логику создания отчётов в Google Sheets.
    Отвечает ТОЛЬКО за оркестрацию: координирует работу
    агрегатора данных, клиента API и форматтера.
    """

    def __init__(
        self,
        config: Config,
        database: Database,
        logger: logging.Logger
    ):
        """
        Инициализирует репортер Google Sheets.

        Args:
            config: Конфигурация приложения
            database: База данных для получения данных
            logger: Logger для логирования операций
        """
        super().__init__(database, logger)

        # Инициализация компонентов
        self.aggregator = DataAggregator(database, logger)
        self.formatter = SheetsFormatter()
        self.client = GoogleSheetsClient(
            credentials_file=config.GOOGLE_CREDENTIALS_FILE,
            sheet_id=config.GOOGLE_SHEET_ID,
            logger=logger
        )

        self.logger.info("GoogleSheetsReporter инициализирован")

    def _create_summary_sheet(self) -> bool:
        """
        Создаёт лист "Сводка".

        Returns:
            bool: True если успешно
        """
        try:
            self.logger.info("Создание листа 'Сводка'")

            # Сбор данных
            total_stats = self.aggregator.get_total_stats()
            last_24h_stats = self.aggregator.get_last_24h_stats()
            breakdown = self.aggregator.get_breakdown_by_type()

            # Форматирование данных
            data = self.formatter.format_summary_sheet(
                total_stats,
                last_24h_stats,
                breakdown
            )

            # Создание/получение листа
            worksheet = self.client.create_or_get_worksheet('Сводка')
            self.client.clear_worksheet(worksheet)

            # Запись данных
            self.client.write_data(worksheet, data)

            # Форматирование
            self.client.auto_resize_columns(worksheet)

            self.logger.info("Лист 'Сводка' создан успешно")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания листа 'Сводка': {e}")
            return False

    def _create_all_posts_sheet(self) -> bool:
        """
        Создаёт лист "Все посты".

        Returns:
            bool: True если успешно
        """
        try:
            self.logger.info("Создание листа 'Все посты'")

            # Получение всех постов
            all_posts = self.database.get_all_posts()

            if not all_posts:
                self.logger.warning("Нет постов для отчёта")
                return False

            # Форматирование данных
            data = self.formatter.format_all_posts_sheet(all_posts)

            # Создание/получение листа
            worksheet = self.client.create_or_get_worksheet('Все посты')
            self.client.clear_worksheet(worksheet)

            # Запись данных
            self.client.write_data(worksheet, data)

            # Форматирование
            self.client.format_header(worksheet, row=1)
            self.client.auto_resize_columns(worksheet)
            self.client.set_number_format(worksheet, 'K2:K1000', 'percent')

            self.logger.info(f"Лист 'Все посты' создан ({len(all_posts)} постов)")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания листа 'Все посты': {e}")
            return False

    def _create_top_posts_sheet(self) -> bool:
        """
        Создаёт лист "ТОП-10".

        Returns:
            bool: True если успешно
        """
        try:
            self.logger.info("Создание листа 'ТОП-10'")

            # Получение топ постов
            top_by_views = self.aggregator.get_top_posts(10, 'views')
            top_by_er = self.aggregator.get_top_posts(10, 'er')
            top_by_comments = self.aggregator.get_top_posts(10, 'comments')

            # Форматирование данных
            data = self.formatter.format_top_posts_sheet(
                top_by_views,
                top_by_er,
                top_by_comments
            )

            # Создание/получение листа
            worksheet = self.client.create_or_get_worksheet('ТОП-10')
            self.client.clear_worksheet(worksheet)

            # Запись данных
            self.client.write_data(worksheet, data)

            # Форматирование
            self.client.auto_resize_columns(worksheet)

            self.logger.info("Лист 'ТОП-10' создан успешно")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания листа 'ТОП-10': {e}")
            return False

    def _create_dynamics_sheet(self) -> bool:
        """
        Создаёт лист "Динамика".

        Returns:
            bool: True если успешно
        """
        try:
            self.logger.info("Создание листа 'Динамика'")

            # Получение данных динамики
            daily_data = self.aggregator.get_daily_dynamics()

            if not daily_data:
                self.logger.warning("Нет данных для динамики")
                return False

            # Форматирование данных
            data = self.formatter.format_dynamics_sheet(daily_data)

            # Создание/получение листа
            worksheet = self.client.create_or_get_worksheet('Динамика')
            self.client.clear_worksheet(worksheet)

            # Запись данных
            self.client.write_data(worksheet, data)

            # Форматирование
            self.client.format_header(worksheet, row=1)
            self.client.auto_resize_columns(worksheet)

            self.logger.info(f"Лист 'Динамика' создан ({len(daily_data)} дней)")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка создания листа 'Динамика': {e}")
            return False

    def generate_report(self) -> Optional[str]:
        """
        Генерирует полный отчёт в Google Sheets.

        Создаёт 4 листа: Сводка, Все посты, ТОП-10, Динамика.

        Returns:
            Optional[str]: URL таблицы или None в случае ошибки

        Example:
            >>> reporter = GoogleSheetsReporter(config, db, logger)
            >>> url = reporter.generate_report()
            >>> print(f"Отчёт готов: {url}")
        """
        self.logger.info("Начало генерации отчёта в Google Sheets")

        try:
            # Подключение к Google Sheets
            self.client.connect()

            # Создание листов
            success_count = 0

            if self._create_summary_sheet():
                success_count += 1

            if self._create_all_posts_sheet():
                success_count += 1

            if self._create_top_posts_sheet():
                success_count += 1

            if self._create_dynamics_sheet():
                success_count += 1

            # Проверка успешности
            if success_count == 0:
                self.logger.error("Не удалось создать ни одного листа")
                return None

            # Получение URL таблицы
            url = self.client.get_spreadsheet_url()

            self.logger.info(
                f"Отчёт успешно создан ({success_count}/4 листов): {url}"
            )

            return url

        except Exception as e:
            self.logger.error(f"Ошибка генерации отчёта: {e}", exc_info=True)
            return None
