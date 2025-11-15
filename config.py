"""
Централизованная конфигурация приложения.

Модуль содержит класс Config для загрузки и валидации
переменных окружения и констант приложения.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """
    Класс для управления конфигурацией приложения.

    Загружает переменные окружения из .env файла и предоставляет
    доступ к настройкам через свойства класса.
    """

    # Константы приложения
    VK_API_DELAY: float = 0.35  # секунд между запросами к VK API
    DB_PATH: str = "data/stats.db"
    LOG_PATH: str = "logs/bot.log"
    TIMEZONE: str = "Europe/Yekaterinburg"

    # Переменные окружения
    VK_TOKEN: Optional[str] = None
    HASHTAG: Optional[str] = None
    START_DATE: Optional[str] = None
    GOOGLE_SHEET_ID: Optional[str] = None
    GOOGLE_CREDENTIALS_FILE: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    @classmethod
    def load_from_env(cls, env_file: str = ".env") -> None:
        """
        Загружает конфигурацию из .env файла и валидирует обязательные переменные.

        Args:
            env_file: Путь к файлу с переменными окружения (по умолчанию .env)

        Raises:
            FileNotFoundError: Если .env файл не найден
            ValueError: Если отсутствуют обязательные переменные окружения
        """
        env_path = Path(env_file)

        if not env_path.exists():
            raise FileNotFoundError(
                f"Файл конфигурации '{env_file}' не найден. "
                f"Создайте его на основе .env.example"
            )

        # Загрузка переменных из .env
        load_dotenv(env_path, encoding='utf-8')

        # Загрузка VK настроек
        cls.VK_TOKEN = os.getenv("VK_TOKEN")
        cls.HASHTAG = os.getenv("HASHTAG")
        cls.START_DATE = os.getenv("START_DATE")

        # Загрузка Google Sheets настроек
        cls.GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
        cls.GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

        # Загрузка Telegram настроек
        cls.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        cls.TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

        # Валидация обязательных переменных
        cls._validate_required_variables()

    @classmethod
    def _validate_required_variables(cls) -> None:
        """
        Проверяет наличие всех обязательных переменных окружения.

        Raises:
            ValueError: Если хотя бы одна обязательная переменная отсутствует
        """
        required_vars = {
            "VK_TOKEN": cls.VK_TOKEN,
            "HASHTAG": cls.HASHTAG,
            "START_DATE": cls.START_DATE,
            "GOOGLE_SHEET_ID": cls.GOOGLE_SHEET_ID,
            "GOOGLE_CREDENTIALS_FILE": cls.GOOGLE_CREDENTIALS_FILE,
            "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": cls.TELEGRAM_CHAT_ID,
        }

        missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]

        if missing_vars:
            raise ValueError(
                f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}. "
                f"Проверьте файл .env"
            )

    @classmethod
    def get_db_path(cls) -> Path:
        """
        Возвращает путь к файлу базы данных.

        Returns:
            Path: Абсолютный путь к файлу БД
        """
        return Path(cls.DB_PATH)

    @classmethod
    def get_log_path(cls) -> Path:
        """
        Возвращает путь к файлу логов.

        Returns:
            Path: Абсолютный путь к файлу логов
        """
        return Path(cls.LOG_PATH)

    @classmethod
    def get_credentials_path(cls) -> Path:
        """
        Возвращает путь к файлу с Google credentials.

        Returns:
            Path: Абсолютный путь к файлу credentials
        """
        return Path(cls.GOOGLE_CREDENTIALS_FILE)
