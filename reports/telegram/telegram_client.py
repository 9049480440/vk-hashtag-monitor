"""
Клиент для работы с Telegram Bot API.

Модуль инкапсулирует все операции с Telegram:
отправку сообщений, фотографий и медиа-групп.

Использует python-telegram-bot v20+ через синхронную обёртку.
"""

import asyncio
import logging
from typing import Optional, List
from pathlib import Path

from telegram import InputMediaPhoto
from telegram.ext import Application
from telegram.error import TelegramError, InvalidToken, BadRequest


class TelegramClient:
    """
    Клиент для работы с Telegram Bot API.

    Отвечает ТОЛЬКО за взаимодействие с Telegram API.
    НЕ знает про структуру отчётов или бизнес-логику.

    Использует asyncio.run() для выполнения async операций,
    предоставляя синхронный интерфейс.
    """

    # Лимиты Telegram
    MAX_MESSAGE_LENGTH = 4096      # Максимальная длина сообщения
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_MEDIA_GROUP = 10           # Максимум файлов в media group

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        logger: logging.Logger
    ):
        """
        Инициализирует Telegram клиент.

        Args:
            bot_token: Токен бота Telegram
            chat_id: ID чата для отправки сообщений
            logger: Logger для логирования операций
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logger

    def connect(self) -> bool:
        """
        Проверяет валидность токена и создаёт подключение.

        Returns:
            bool: True если подключение успешно

        Raises:
            InvalidToken: Если токен невалиден
            TelegramError: При других ошибках Telegram API
        """
        self.logger.info("Подключение к Telegram Bot API")

        async def _connect():
            """Async функция для проверки токена."""
            try:
                # Создание Application
                app = Application.builder().token(self.bot_token).build()

                # Проверка токена через запрос информации о боте
                bot_info = await app.bot.get_me()

                self.logger.info(
                    f"Подключение успешно. Бот: @{bot_info.username}"
                )
                return True

            except InvalidToken as e:
                self.logger.error(f"Неверный токен Telegram: {e}")
                raise
            except TelegramError as e:
                self.logger.error(f"Ошибка Telegram API: {e}")
                raise

        try:
            # Запуск async функции синхронно
            return asyncio.run(_connect())
        except Exception:
            raise

    def send_message(
        self,
        text: str,
        parse_mode: str = 'Markdown'
    ) -> bool:
        """
        Отправляет текстовое сообщение.

        Args:
            text: Текст сообщения
            parse_mode: Режим форматирования ('Markdown' или 'HTML')

        Returns:
            bool: True если сообщение отправлено успешно

        Example:
            >>> client.send_message("*Жирный текст*", parse_mode='Markdown')
            True
        """
        async def _send_message():
            """Async функция для отправки сообщения."""
            try:
                # Проверка длины сообщения
                message_text = text
                if len(message_text) > self.MAX_MESSAGE_LENGTH:
                    self.logger.warning(
                        f"Сообщение обрезано с {len(message_text)} до {self.MAX_MESSAGE_LENGTH} символов"
                    )
                    message_text = message_text[:self.MAX_MESSAGE_LENGTH - 3] + '...'

                # Создание Application
                app = Application.builder().token(self.bot_token).build()

                # Отправка сообщения
                await app.bot.send_message(
                    chat_id=self.chat_id,
                    text=message_text,
                    parse_mode=parse_mode
                )

                self.logger.info(f"Сообщение отправлено ({len(message_text)} символов)")
                return True

            except BadRequest as e:
                self.logger.error(f"Ошибка отправки сообщения (неверный запрос): {e}")
                return False
            except TelegramError as e:
                self.logger.error(f"Ошибка Telegram при отправке сообщения: {e}")
                return False

        try:
            return asyncio.run(_send_message())
        except Exception as e:
            self.logger.error(f"Критическая ошибка при отправке сообщения: {e}")
            return False

    def send_photo(
        self,
        photo_path: str,
        caption: Optional[str] = None
    ) -> bool:
        """
        Отправляет одну фотографию.

        Args:
            photo_path: Путь к файлу изображения
            caption: Подпись к фотографии (опционально)

        Returns:
            bool: True если фото отправлено успешно

        Example:
            >>> client.send_photo('chart.png', caption='График')
            True
        """
        async def _send_photo():
            """Async функция для отправки фото."""
            try:
                path = Path(photo_path)

                # Проверка существования файла
                if not path.exists():
                    self.logger.error(f"Файл не найден: {photo_path}")
                    return False

                # Проверка размера файла
                file_size = path.stat().st_size
                if file_size > self.MAX_FILE_SIZE:
                    self.logger.error(
                        f"Файл слишком большой: {file_size / (1024 * 1024):.1f} MB "
                        f"(максимум {self.MAX_FILE_SIZE / (1024 * 1024)} MB)"
                    )
                    return False

                # Создание Application
                app = Application.builder().token(self.bot_token).build()

                # Отправка фото
                with open(photo_path, 'rb') as photo_file:
                    await app.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo_file,
                        caption=caption
                    )

                self.logger.info(f"Фото отправлено: {photo_path}")
                return True

            except BadRequest as e:
                self.logger.error(f"Ошибка отправки фото (неверный запрос): {e}")
                return False
            except TelegramError as e:
                self.logger.error(f"Ошибка Telegram при отправке фото: {e}")
                return False

        try:
            return asyncio.run(_send_photo())
        except Exception as e:
            self.logger.error(f"Критическая ошибка при отправке фото: {e}")
            return False

    def send_media_group(
        self,
        photo_paths: List[str],
        caption: Optional[str] = None
    ) -> bool:
        """
        Отправляет группу фотографий (до 10 штук).

        Args:
            photo_paths: Список путей к файлам изображений
            caption: Подпись к первому фото (опционально)

        Returns:
            bool: True если медиа-группа отправлена успешно

        Example:
            >>> paths = ['chart1.png', 'chart2.png', 'chart3.png']
            >>> client.send_media_group(paths, caption='Графики')
            True
        """
        async def _send_media_group():
            """Async функция для отправки медиа-группы."""
            try:
                # Проверка количества файлов
                paths = photo_paths.copy()
                if len(paths) > self.MAX_MEDIA_GROUP:
                    self.logger.warning(
                        f"Слишком много файлов: {len(paths)}. "
                        f"Отправка первых {self.MAX_MEDIA_GROUP}"
                    )
                    paths = paths[:self.MAX_MEDIA_GROUP]

                if not paths:
                    self.logger.warning("Список файлов пуст")
                    return False

                # Подготовка медиа-группы
                media = []
                for i, photo_path in enumerate(paths):
                    path = Path(photo_path)

                    if not path.exists():
                        self.logger.warning(f"Файл не найден: {photo_path}, пропуск")
                        continue

                    # Открытие файла
                    with open(photo_path, 'rb') as photo_file:
                        # Добавление caption только к первому фото
                        photo_caption = caption if i == 0 else None

                        media.append(
                            InputMediaPhoto(
                                media=photo_file.read(),
                                caption=photo_caption
                            )
                        )

                if not media:
                    self.logger.error("Нет валидных файлов для отправки")
                    return False

                # Создание Application
                app = Application.builder().token(self.bot_token).build()

                # Отправка медиа-группы
                await app.bot.send_media_group(
                    chat_id=self.chat_id,
                    media=media
                )

                self.logger.info(f"Медиа-группа отправлена: {len(media)} фото")
                return True

            except BadRequest as e:
                self.logger.error(f"Ошибка отправки медиа-группы (неверный запрос): {e}")
                return False
            except TelegramError as e:
                self.logger.error(f"Ошибка Telegram при отправке медиа-группы: {e}")
                return False

        try:
            return asyncio.run(_send_media_group())
        except Exception as e:
            self.logger.error(f"Критическая ошибка при отправке медиа-группы: {e}")
            return False

    def get_bot_info(self) -> Optional[dict]:
        """
        Получает информацию о боте.

        Returns:
            Optional[dict]: Информация о боте или None при ошибке

        Example:
            >>> info = client.get_bot_info()
            >>> print(info['username'])
            'my_bot'
        """
        async def _get_bot_info():
            """Async функция для получения информации о боте."""
            try:
                # Создание Application
                app = Application.builder().token(self.bot_token).build()

                # Получение информации о боте
                bot_info = await app.bot.get_me()

                return {
                    'id': bot_info.id,
                    'username': bot_info.username,
                    'first_name': bot_info.first_name,
                    'can_join_groups': bot_info.can_join_groups,
                    'can_read_all_group_messages': bot_info.can_read_all_group_messages
                }

            except TelegramError as e:
                self.logger.error(f"Ошибка получения информации о боте: {e}")
                return None

        try:
            return asyncio.run(_get_bot_info())
        except Exception as e:
            self.logger.error(f"Критическая ошибка при получении информации о боте: {e}")
            return None
