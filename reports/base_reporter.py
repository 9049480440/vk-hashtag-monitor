"""
Абстрактный базовый класс для всех типов репортеров.

Модуль определяет общий интерфейс для генерации отчётов
в различных форматах (Google Sheets, PDF, Excel и т.д.).
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from database import Database


class BaseReporter(ABC):
    """
    Абстрактный базовый класс для генераторов отчётов.

    Определяет общий интерфейс для всех репортеров.
    Позволяет легко добавлять новые форматы отчётов
    (PDF, Excel, CSV и т.д.) без изменения существующего кода.

    Следует принципу Open/Closed: открыт для расширения,
    закрыт для модификации.
    """

    def __init__(self, database: Database, logger: logging.Logger):
        """
        Инициализирует базовый репортер.

        Args:
            database: Экземпляр Database для получения данных
            logger: Logger для логирования операций
        """
        self.database = database
        self.logger = logger
        self.logger.debug(f"Инициализация репортера {self.__class__.__name__}")

    @abstractmethod
    def generate_report(self) -> Optional[str]:
        """
        Генерирует отчёт в соответствующем формате.

        Каждый репортер должен реализовать свою логику
        генерации отчёта (в Google Sheets, PDF, Excel и т.д.).

        Returns:
            Optional[str]: URL или путь к созданному отчёту,
                          или None в случае ошибки

        Example:
            >>> reporter = GoogleSheetsReporter(db, logger)
            >>> url = reporter.generate_report()
            >>> print(f"Отчёт создан: {url}")
            Отчёт создан: https://docs.google.com/spreadsheets/d/...
        """
        pass
