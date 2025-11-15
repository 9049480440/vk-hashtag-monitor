"""
Модуль для отправки отчётов в Telegram.

Содержит клиент Telegram Bot API, форматтер сообщений
и основной репортер.
"""

from reports.telegram.telegram_reporter import TelegramReporter
from reports.telegram.telegram_client import TelegramClient
from reports.telegram.message_formatter import MessageFormatter

__all__ = ['TelegramReporter', 'TelegramClient', 'MessageFormatter']
