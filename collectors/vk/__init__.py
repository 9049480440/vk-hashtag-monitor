"""
Модуль для работы с ВКонтакте.

Содержит клиент VK API, парсер постов и основной коллектор.
"""

from collectors.vk.vk_collector import VKCollector
from collectors.vk.vk_api_client import VKAPIClient
from collectors.vk.vk_post_parser import VKPostParser

__all__ = ['VKCollector', 'VKAPIClient', 'VKPostParser']
