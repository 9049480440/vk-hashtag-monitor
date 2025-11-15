"""
Коллектор данных из ВКонтакте.

Модуль реализует бизнес-логику сбора постов из VK.
Использует VKAPIClient для API запросов и VKPostParser
для обработки данных.
"""

import logging
from typing import Tuple, Dict, Any

from database import Database
from config import Config
from collectors.base_collector import BaseCollector
from collectors.vk.vk_api_client import VKAPIClient
from collectors.vk.vk_post_parser import VKPostParser


class VKCollector(BaseCollector):
    """
    Коллектор данных из ВКонтакте.

    Реализует бизнес-логику сбора постов из VK.
    Отвечает ТОЛЬКО за оркестрацию: координирует работу
    API клиента, парсера и базы данных.

    Не знает деталей VK API (за это отвечает VKAPIClient)
    и формата данных VK (за это отвечает VKPostParser).
    """

    def __init__(
        self,
        config: Config,
        database: Database,
        logger: logging.Logger
    ):
        """
        Инициализирует коллектор VK.

        Args:
            config: Конфигурация приложения
            database: База данных для сохранения постов
            logger: Logger для логирования операций
        """
        super().__init__(database, logger)

        # Инициализация API клиента
        self.api_client = VKAPIClient(
            token=config.VK_TOKEN,
            api_delay=config.VK_API_DELAY,
            logger=logger
        )

        # Инициализация парсера
        self.parser = VKPostParser(logger)

        self.logger.info("VKCollector успешно инициализирован")

    def _get_owner_info(self, owner_id: int) -> Tuple[str, str]:
        """
        Определяет тип источника и получает название владельца.

        Args:
            owner_id: ID владельца поста (отрицательный для групп,
                     положительный для пользователей)

        Returns:
            Tuple[str, str]: Кортеж (source_type, owner_name)

        Example:
            >>> source_type, name = collector._get_owner_info(-12345)
            >>> print(source_type, name)
            'group' 'Медиастанция'
        """
        if owner_id < 0:
            # Группа (отрицательный ID)
            group_id = abs(owner_id)
            name = self.api_client.get_group_info(group_id)

            if name:
                self.logger.debug(f"Получена информация о группе: {name}")
                return ('group', name)
            else:
                return ('group', f'Group {group_id}')

        else:
            # Пользователь (положительный ID)
            name = self.api_client.get_user_info(owner_id)

            if name:
                self.logger.debug(f"Получена информация о пользователе: {name}")
                return ('user', name)
            else:
                return ('user', f'User {owner_id}')

    def process_new_post(self, post: Dict[str, Any], hashtag: str) -> bool:
        """
        Обрабатывает и сохраняет новый пост в БД.

        Args:
            post: Данные поста от VK API
            hashtag: Хештег поиска

        Returns:
            bool: True если пост успешно сохранён, False в противном случае

        Example:
            >>> success = collector.process_new_post(vk_post, '#Снежинск')
            >>> if success:
            ...     print("Пост сохранён")
        """
        try:
            # Получение ID владельца поста
            owner_id = post.get('owner_id') or post.get('from_id')
            post_id = post.get('id')

            if not owner_id or not post_id:
                self.logger.error("Пост не содержит owner_id или id")
                return False

            # Получение информации о владельце
            source_type, owner_name = self._get_owner_info(owner_id)

            # Парсинг данных поста
            post_data = self.parser.parse_post_data(
                post, source_type, owner_name, hashtag
            )

            # Сохранение в БД
            if self.database.add_post(post_data):
                self.logger.info(
                    f"Новый пост добавлен: {post_data['post_id']} "
                    f"от {owner_name}"
                )
                return True
            else:
                self.logger.warning(
                    f"Не удалось добавить пост {post_data['post_id']}"
                )
                return False

        except Exception as e:
            self.logger.error(
                f"Ошибка обработки нового поста: {e}",
                exc_info=True
            )
            return False

    def update_post_metrics(self, post_id: str) -> bool:
        """
        Обновляет метрики существующего поста в БД.

        Args:
            post_id: ID поста в формате "owner_id_post_id"

        Returns:
            bool: True если пост успешно обновлён, False в противном случае

        Example:
            >>> success = collector.update_post_metrics('-12345_67890')
        """
        try:
            # Парсинг post_id для получения owner_id и post_id
            parts = post_id.split('_')
            if len(parts) != 2:
                self.logger.error(f"Неверный формат post_id: {post_id}")
                return False

            owner_id = int(parts[0])
            vk_post_id = int(parts[1])

            # Получение актуальных данных от VK API
            post = self.api_client.get_post_by_id(owner_id, vk_post_id)

            if not post:
                self.logger.warning(
                    f"Пост {post_id} недоступен для обновления"
                )
                return False

            # Извлечение метрик
            metrics = self.parser.parse_metrics(post)

            # Обновление в БД
            if self.database.update_post(post_id, metrics):
                self.logger.debug(f"Метрики поста {post_id} обновлены")
                return True
            else:
                self.logger.warning(
                    f"Не удалось обновить пост {post_id} в БД"
                )
                return False

        except ValueError as e:
            self.logger.error(f"Ошибка парсинга post_id '{post_id}': {e}")
            return False
        except Exception as e:
            self.logger.error(
                f"Ошибка обновления поста {post_id}: {e}",
                exc_info=True
            )
            return False

    def collect_new_posts(self, hashtag: str) -> int:
        """
        Собирает новые посты по хештегу.

        Реализует метод базового класса BaseCollector.
        Находит новые посты, которых нет в БД, и сохраняет их.

        Args:
            hashtag: Хештег для поиска

        Returns:
            int: Количество добавленных новых постов

        Example:
            >>> new_count = collector.collect_new_posts('#Снежинск')
            >>> print(f"Добавлено {new_count} новых постов")
        """
        self.logger.info(
            f"Начало сбора новых постов по хештегу: {hashtag}"
        )

        # Поиск постов через API клиент
        posts = self.api_client.search_posts(hashtag, count=100)

        if not posts:
            self.logger.info("Посты не найдены")
            return 0

        added_count = 0

        # Обработка каждого найденного поста
        for post in posts:
            try:
                # Получение ID поста
                owner_id = post.get('owner_id') or post.get('from_id')
                post_id = post.get('id')

                if not owner_id or not post_id:
                    self.logger.warning("Пост без ID, пропуск")
                    continue

                # Формирование уникального ID
                unique_post_id = self.parser.parse_post_id(owner_id, post_id)

                # Проверка существования в БД
                if self.database.post_exists(unique_post_id):
                    self.logger.debug(
                        f"Пост {unique_post_id} уже существует в БД, пропуск"
                    )
                    continue

                # Обработка нового поста
                if self.process_new_post(post, hashtag):
                    added_count += 1

            except Exception as e:
                self.logger.error(
                    f"Ошибка при обработке поста: {e}",
                    exc_info=True
                )
                continue

        self.logger.info(
            f"Сбор завершён. Добавлено новых постов: {added_count} "
            f"из {len(posts)} найденных"
        )

        return added_count

    def update_all_posts(self) -> Tuple[int, int]:
        """
        Обновляет метрики всех постов в БД.

        Реализует метод базового класса BaseCollector.
        Проходит по всем постам в БД и обновляет их метрики.

        Returns:
            Tuple[int, int]: Кортеж (успешно_обновлено, ошибок)

        Example:
            >>> updated, errors = collector.update_all_posts()
            >>> print(f"Обновлено: {updated}, ошибок: {errors}")
        """
        self.logger.info("Начало обновления метрик всех постов")

        # Получение всех постов из БД
        all_posts = self.database.get_all_posts()

        if not all_posts:
            self.logger.info("В базе данных нет постов для обновления")
            return (0, 0)

        total_posts = len(all_posts)
        self.logger.info(f"Найдено {total_posts} постов для обновления")

        updated_count = 0
        error_count = 0

        # Обновление каждого поста
        for index, post in enumerate(all_posts, 1):
            try:
                post_id = post.get('post_id')

                if not post_id:
                    self.logger.warning("Пост без ID в БД, пропуск")
                    error_count += 1
                    continue

                # Обновление метрик
                if self.update_post_metrics(post_id):
                    updated_count += 1
                else:
                    error_count += 1

                # Логирование прогресса каждые 10 постов
                if index % 10 == 0:
                    self.logger.info(
                        f"Прогресс: {index}/{total_posts} постов обработано "
                        f"(успешно: {updated_count}, ошибок: {error_count})"
                    )

            except Exception as e:
                self.logger.error(
                    f"Ошибка при обновлении поста: {e}",
                    exc_info=True
                )
                error_count += 1
                continue

        self.logger.info(
            f"Обновление завершено. Успешно: {updated_count}, "
            f"ошибок: {error_count} из {total_posts} постов"
        )

        return (updated_count, error_count)
