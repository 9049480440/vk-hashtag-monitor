"""
Абстрактный базовый класс для коллекторов данных из соцсетей.

Модуль определяет общий интерфейс для всех коллекторов,
что позволяет легко добавлять новые источники данных
без изменения существующего кода.
"""

import logging
from abc import ABC, abstractmethod
from typing import Tuple

from database import Database


class BaseCollector(ABC):
    """
    Абстрактный базовый класс для коллекторов данных из соцсетей.

    Определяет общий интерфейс для всех коллекторов.
    Позволяет легко добавлять новые источники данных
    (Telegram, YouTube, Instagram и т.д.) без изменения существующего кода.

    Следует принципу Open/Closed: открыт для расширения,
    закрыт для модификации.
    """

    def __init__(self, database: Database, logger: logging.Logger):
        """
        Инициализирует базовый коллектор.

        Args:
            database: Экземпляр Database для сохранения данных
            logger: Logger для логирования операций
        """
        self.database = database
        self.logger = logger
        self.logger.debug(f"Инициализация коллектора {self.__class__.__name__}")

    @abstractmethod
    def collect_new_posts(self, query: str) -> int:
        """
        Собирает новые посты по поисковому запросу.

        Каждый коллектор должен реализовать свою логику поиска
        и сбора постов из соответствующей соцсети.

        Args:
            query: Поисковый запрос (хештег, ключевое слово и т.д.)

        Returns:
            int: Количество добавленных новых постов

        Example:
            >>> collector.collect_new_posts('#Снежинск')
            42
        """
        pass

    @abstractmethod
    def update_all_posts(self) -> Tuple[int, int]:
        """
        Обновляет метрики всех постов в базе данных.

        Каждый коллектор должен реализовать свою логику
        обновления метрик постов из соответствующей соцсети.

        Returns:
            Tuple[int, int]: Кортеж (успешно_обновлено, ошибок)

        Example:
            >>> updated, errors = collector.update_all_posts()
            >>> print(f"Обновлено: {updated}, ошибок: {errors}")
            Обновлено: 95, ошибок: 5
        """
        pass
