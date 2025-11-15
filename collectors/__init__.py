"""
Модуль коллекторов данных из социальных сетей.

Предоставляет базовый класс BaseCollector и реализации
для различных платформ (VK, Telegram, YouTube и т.д.).
"""

from collectors.vk.vk_collector import VKCollector

__all__ = ['VKCollector']
