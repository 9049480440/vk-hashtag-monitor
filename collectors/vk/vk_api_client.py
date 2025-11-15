"""
Клиент для работы с VK API.

Модуль инкапсулирует все запросы к VK API,
обработку ошибок и rate limiting.
Отделяет низкоуровневые детали API от бизнес-логики.
"""

import time
import logging
from typing import Optional, List, Dict, Any

import vk_api
from vk_api.exceptions import ApiError, ApiHttpError


class VKAPIClient:
    """
    Клиент для работы с VK API.

    Отвечает ТОЛЬКО за взаимодействие с VK API.
    Знает все детали API (endpoints, параметры, ошибки),
    но не знает ничего про базу данных или бизнес-логику.
    """

    def __init__(
        self,
        token: str,
        api_delay: float,
        logger: logging.Logger
    ):
        """
        Инициализирует VK API клиент.

        Args:
            token: Токен доступа VK API
            api_delay: Задержка между запросами в секундах
            logger: Logger для логирования операций

        Raises:
            ApiError: Если токен невалиден
            ApiHttpError: Если не удается подключиться к VK API
        """
        self.logger = logger
        self.api_delay = api_delay

        try:
            # Создание сессии VK API
            vk_session = vk_api.VkApi(token=token)
            self.vk = vk_session.get_api()

            # Проверка валидности токена
            self._validate_token()

            self.logger.info("VK API клиент успешно инициализирован")

        except ApiError as e:
            self.logger.error(f"Ошибка VK API при инициализации: {e}")
            raise
        except ApiHttpError as e:
            self.logger.error(f"HTTP ошибка при инициализации VK API: {e}")
            raise

    def _validate_token(self) -> None:
        """
        Проверяет валидность токена через тестовый запрос.

        Raises:
            ApiError: Если токен невалиден (код ошибки 5)
        """
        try:
            self.vk.users.get()
            self.logger.debug("VK токен валиден")
        except ApiError as e:
            if e.code == 5:
                self.logger.error("Невалидный VK токен")
                raise
            # Для других ошибок токен может быть валидным
            self.logger.warning(f"Предупреждение при валидации токена: {e}")

    def _make_pause(self) -> None:
        """
        Делает паузу между запросами для защиты от rate limit.

        Использует заданную задержку для предотвращения блокировки
        со стороны VK API.
        """
        time.sleep(self.api_delay)
        self.logger.debug(f"Пауза {self.api_delay} сек")

    def search_posts(
        self,
        hashtag: str,
        count: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Ищет посты по хештегу через newsfeed.search.

        Args:
            hashtag: Хештег для поиска (с # или без)
            count: Количество постов для получения (максимум 200)

        Returns:
            List[Dict]: Список постов от VK API

        Example:
            >>> posts = client.search_posts('#Снежинск', count=50)
            >>> len(posts)
            50
        """
        try:
            # Убедимся что хештег начинается с #
            if not hashtag.startswith('#'):
                hashtag = f"#{hashtag}"

            self.logger.info(
                f"Поиск постов по хештегу: {hashtag}, count={count}"
            )

            # Ограничение count до 200 (лимит VK API)
            count = min(count, 200)

            # Запрос к API
            response = self.vk.newsfeed.search(
                q=hashtag,
                count=count
            )

            posts = response.get('items', [])
            self.logger.info(f"Найдено постов: {len(posts)}")

            # Пауза после запроса
            self._make_pause()

            return posts

        except ApiError as e:
            self.logger.error(f"VK API ошибка при поиске: {e}")
            if e.code == 6:
                self.logger.warning("Превышен лимит запросов (rate limit)")
            return []
        except ApiHttpError as e:
            self.logger.error(f"HTTP ошибка при поиске постов: {e}")
            return []

    def get_post_by_id(
        self,
        owner_id: int,
        post_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Получает пост по ID через wall.getById.

        Args:
            owner_id: ID владельца поста
            post_id: ID поста

        Returns:
            Optional[Dict]: Данные поста или None если недоступен

        Example:
            >>> post = client.get_post_by_id(-12345, 67890)
            >>> if post:
            ...     print(post['likes']['count'])
        """
        try:
            posts_param = f"{owner_id}_{post_id}"
            self.logger.debug(f"Запрос поста: {posts_param}")

            # Запрос к API
            response = self.vk.wall.getById(posts=posts_param)

            # Пауза после запроса
            self._make_pause()

            if response:
                return response[0]

            self.logger.warning(f"Пост {posts_param} не найден")
            return None

        except ApiError as e:
            self.logger.warning(
                f"Пост {owner_id}_{post_id} недоступен: {e}"
            )
            self._make_pause()
            return None
        except ApiHttpError as e:
            self.logger.error(
                f"HTTP ошибка при получении поста {owner_id}_{post_id}: {e}"
            )
            self._make_pause()
            return None

    def get_group_info(self, group_id: int) -> Optional[str]:
        """
        Получает название группы по ID.

        Args:
            group_id: ID группы (положительное число)

        Returns:
            Optional[str]: Название группы или None

        Example:
            >>> name = client.get_group_info(12345)
            >>> print(name)
            'Название группы'
        """
        try:
            self.logger.debug(f"Запрос информации о группе: {group_id}")

            # Запрос к API
            response = self.vk.groups.getById(group_id=group_id)

            # Пауза после запроса
            self._make_pause()

            if response:
                name = response[0].get('name', 'Unknown Group')
                self.logger.debug(f"Получено название группы: {name}")
                return name

            return None

        except ApiError as e:
            self.logger.warning(f"Группа {group_id} не найдена: {e}")
            self._make_pause()
            return None
        except ApiHttpError as e:
            self.logger.error(
                f"HTTP ошибка при получении группы {group_id}: {e}"
            )
            self._make_pause()
            return None

    def get_user_info(self, user_id: int) -> Optional[str]:
        """
        Получает полное имя пользователя по ID.

        Args:
            user_id: ID пользователя

        Returns:
            Optional[str]: Полное имя пользователя или None

        Example:
            >>> name = client.get_user_info(12345)
            >>> print(name)
            'Иван Иванов'
        """
        try:
            self.logger.debug(f"Запрос информации о пользователе: {user_id}")

            # Запрос к API
            response = self.vk.users.get(user_ids=user_id)

            # Пауза после запроса
            self._make_pause()

            if response:
                user = response[0]
                first_name = user.get('first_name', '')
                last_name = user.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()

                self.logger.debug(f"Получено имя пользователя: {full_name}")
                return full_name

            return None

        except ApiError as e:
            self.logger.warning(f"Пользователь {user_id} не найден: {e}")
            self._make_pause()
            return None
        except ApiHttpError as e:
            self.logger.error(
                f"HTTP ошибка при получении пользователя {user_id}: {e}"
            )
            self._make_pause()
            return None
