"""
Основной репортер для Telegram.

Модуль координирует создание и отправку отчёта в Telegram:
текст, графики и ссылка на Google Sheets.
"""

import logging
from typing import Optional

from database import Database
from config import Config
from reports.base_reporter import BaseReporter
from reports.data_aggregator import DataAggregator
from reports.charts.chart_builder import ChartBuilder
from reports.telegram.telegram_client import TelegramClient
from reports.telegram.message_formatter import MessageFormatter


class TelegramReporter(BaseReporter):
    """
    Репортер для отправки отчётов в Telegram.

    Реализует бизнес-логику создания и отправки отчётов в Telegram.
    Отвечает ТОЛЬКО за оркестрацию: координирует работу
    всех компонентов для создания полного отчёта.
    """

    def __init__(
        self,
        config: Config,
        database: Database,
        logger: logging.Logger,
        sheet_url: Optional[str] = None
    ):
        """
        Инициализирует Telegram репортер.

        Args:
            config: Конфигурация приложения
            database: База данных для получения данных
            logger: Logger для логирования операций
            sheet_url: URL Google Sheets таблицы (опционально)
        """
        super().__init__(database, logger)

        self.config = config
        self.sheet_url = sheet_url

        # Инициализация компонентов
        self.aggregator = DataAggregator(database, logger)
        self.chart_builder = ChartBuilder(database, logger, 'temp_charts')
        self.telegram_client = TelegramClient(
            bot_token=config.TELEGRAM_BOT_TOKEN,
            chat_id=config.TELEGRAM_CHAT_ID,
            logger=logger
        )
        self.formatter = MessageFormatter()

        self.logger.info("TelegramReporter инициализирован")

    def generate_report(self) -> Optional[str]:
        """
        Генерирует и отправляет отчёт в Telegram.

        Создаёт текстовое сообщение, генерирует графики,
        отправляет всё в Telegram и очищает временные файлы.

        Returns:
            Optional[str]: Сообщение об успехе или None при ошибке

        Example:
            >>> reporter = TelegramReporter(config, db, logger)
            >>> result = reporter.generate_report()
            >>> print(result)
            'Отчёт успешно отправлен в Telegram'
        """
        self.logger.info("Начало генерации Telegram отчёта")

        chart_files = None

        try:
            # 1. Подключение к Telegram
            self.logger.info("Подключение к Telegram Bot API")
            if not self.telegram_client.connect():
                self.logger.error("Не удалось подключиться к Telegram")
                return None

            # 2. Сбор статистики
            self.logger.info("Сбор статистики")
            total_stats = self.aggregator.get_total_stats()
            last_24h_stats = self.aggregator.get_last_24h_stats()
            breakdown = self.aggregator.get_breakdown_by_type()

            # Извлечение информации об уникальных авторах из breakdown
            unique_authors = breakdown.get('unique_authors')

            # Получение ТОП-3 постов
            self.logger.info("Получение ТОП-3 постов по просмотрам")
            top_posts = self.aggregator.get_top_posts(limit=3, sort_by='views')

            # 3. Форматирование сообщения
            self.logger.info("Форматирование текстового сообщения")
            message = self.formatter.format_report_message(
                total_stats=total_stats,
                last_24h_stats=last_24h_stats,
                breakdown=breakdown,
                hashtag=self.config.HASHTAG,
                top_posts=top_posts,
                sheet_url=self.sheet_url,
                unique_authors=unique_authors
            )

            # 4. Отправка текстового сообщения
            self.logger.info("Отправка текстового сообщения")
            if not self.telegram_client.send_message(message, parse_mode='Markdown'):
                self.logger.error("Не удалось отправить текстовое сообщение")
                return None

            # 5. Генерация графиков
            self.logger.info("Генерация графиков")
            chart_files = self.chart_builder.build_all_charts()

            if not chart_files:
                self.logger.warning("Графики не созданы, пропускаем отправку")
            else:
                # 6. Отправка графиков
                self.logger.info(f"Отправка {len(chart_files)} графиков")
                if not self.telegram_client.send_media_group(
                    photo_paths=chart_files,
                    caption="📊 Графики за период"
                ):
                    self.logger.error("Не удалось отправить графики")
                    # Продолжаем, не критично

            self.logger.info("Отчёт успешно отправлен в Telegram")
            return "Отчёт успешно отправлен в Telegram"

        except Exception as e:
            self.logger.error(f"Ошибка генерации Telegram отчёта: {e}", exc_info=True)
            return None

        finally:
            # 7. Очистка временных файлов графиков
            if chart_files:
                self.logger.info("Очистка временных файлов")
                self.chart_builder.cleanup_charts(chart_files)
