"""
Настройка системы логирования.

Модуль предоставляет функцию для создания настроенных логгеров
с выводом в файл и консоль, а также ротацией логов.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO,
    console_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Создает и настраивает логгер с выводом в файл и консоль.

    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        level: Уровень логирования (по умолчанию INFO)
        console_output: Выводить ли логи в консоль (по умолчанию True)
        max_bytes: Максимальный размер файла лога в байтах (по умолчанию 10 MB)
        backup_count: Количество файлов для ротации (по умолчанию 5)

    Returns:
        logging.Logger: Настроенный объект логгера

    Example:
        >>> logger = setup_logger("my_app", "logs/app.log")
        >>> logger.info("Application started")
    """
    # Создание логгера
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Очистка существующих handlers (чтобы избежать дублирования)
    if logger.handlers:
        logger.handlers.clear()

    # Формат логов
    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Создание папки для логов, если её нет
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Handler для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # Handler для вывода в консоль
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Цветной формат для консоли (опционально)
        if _supports_color():
            console_format = ColoredFormatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(console_format)
        else:
            console_handler.setFormatter(log_format)

        logger.addHandler(console_handler)

    return logger


def _supports_color() -> bool:
    """
    Проверяет, поддерживает ли терминал цветной вывод.

    Returns:
        bool: True если терминал поддерживает цвета, иначе False
    """
    # Проверка для Windows
    if sys.platform == "win32":
        try:
            import colorama
            colorama.init()
            return True
        except ImportError:
            return False

    # Проверка для Unix-подобных систем
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


class ColoredFormatter(logging.Formatter):
    """
    Форматтер логов с поддержкой цветного вывода в консоль.
    """

    # Цветовые коды ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """
        Форматирует запись лога с добавлением цветов.

        Args:
            record: Запись лога

        Returns:
            str: Отформатированная строка лога с цветовыми кодами
        """
        # Копируем record чтобы не изменять оригинал
        log_color = self.COLORS.get(record.levelname, self.RESET)

        # Сохраняем оригинальное значение levelname
        original_levelname = record.levelname

        # Применяем цвет к уровню логирования
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"

        # Форматируем сообщение
        formatted = super().format(record)

        # Восстанавливаем оригинальное значение
        record.levelname = original_levelname

        return formatted
