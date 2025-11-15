"""
Парсер данных постов ВКонтакте.

Модуль отвечает за извлечение и нормализацию данных
из структуры VK API в формат для сохранения в базу данных.
"""

import logging
from typing import Dict, Any
from datetime import datetime


class VKPostParser:
    """
    Парсер данных постов VK.

    Отвечает ТОЛЬКО за извлечение и нормализацию данных из структуры VK API.
    Знает все детали формата данных VK (поля, вложенные структуры),
    но не знает про базу данных или API запросы.
    """

    def __init__(self, logger: logging.Logger):
        """
        Инициализирует парсер постов VK.

        Args:
            logger: Logger для логирования операций
        """
        self.logger = logger

    @staticmethod
    def parse_post_id(owner_id: int, post_id: int) -> str:
        """
        Создает уникальный идентификатор поста.

        Args:
            owner_id: ID владельца поста
            post_id: ID поста

        Returns:
            str: Уникальный ID в формате "owner_id_post_id"

        Example:
            >>> VKPostParser.parse_post_id(-12345, 67890)
            '-12345_67890'
        """
        return f"{owner_id}_{post_id}"

    @staticmethod
    def build_post_url(owner_id: int, post_id: int) -> str:
        """
        Создает URL поста ВКонтакте.

        Args:
            owner_id: ID владельца поста
            post_id: ID поста

        Returns:
            str: URL поста

        Example:
            >>> VKPostParser.build_post_url(-12345, 67890)
            'https://vk.com/wall-12345_67890'
        """
        return f"https://vk.com/wall{owner_id}_{post_id}"

    def extract_video_info(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает информацию о видео из поста.

        Ищет первое видео во вложениях поста и извлекает
        его метаданные (просмотры, длительность, название).

        Args:
            post: Данные поста от VK API

        Returns:
            Dict: Словарь с полями has_video, video_views,
                  video_duration, video_title

        Example:
            >>> info = parser.extract_video_info(post)
            >>> print(info['has_video'], info['video_views'])
            1 1500
        """
        # Значения по умолчанию (нет видео)
        video_info = {
            'has_video': 0,
            'video_views': 0,
            'video_duration': None,
            'video_title': None
        }

        # Проверка наличия вложений
        attachments = post.get('attachments', [])
        if not attachments:
            return video_info

        # Поиск первого видео в вложениях
        for attachment in attachments:
            if attachment.get('type') == 'video':
                video = attachment.get('video', {})

                video_info['has_video'] = 1
                video_info['video_views'] = video.get('views', 0)
                video_info['video_duration'] = video.get('duration')
                video_info['video_title'] = video.get('title')

                self.logger.debug(
                    f"Найдено видео в посте: '{video_info['video_title']}', "
                    f"просмотров: {video_info['video_views']}"
                )

                # Берём только первое видео
                break

        return video_info

    def _extract_metrics(self, post: Dict[str, Any]) -> Dict[str, int]:
        """
        Извлекает метрики поста (просмотры, лайки, комментарии, репосты).

        Args:
            post: Данные поста от VK API

        Returns:
            Dict: Словарь с метриками
        """
        # Извлечение просмотров
        views_data = post.get('views', {})
        post_views = views_data.get('count', 0) if isinstance(views_data, dict) else 0

        # Извлечение лайков
        likes_data = post.get('likes', {})
        likes = likes_data.get('count', 0) if isinstance(likes_data, dict) else 0

        # Извлечение комментариев
        comments_data = post.get('comments', {})
        comments = comments_data.get('count', 0) if isinstance(comments_data, dict) else 0

        # Извлечение репостов
        reposts_data = post.get('reposts', {})
        reposts = reposts_data.get('count', 0) if isinstance(reposts_data, dict) else 0

        return {
            'post_views': post_views,
            'likes': likes,
            'comments': comments,
            'reposts': reposts
        }

    def parse_post_data(
        self,
        post: Dict[str, Any],
        source_type: str,
        owner_name: str,
        hashtag: str
    ) -> Dict[str, Any]:
        """
        Извлекает все данные поста для сохранения в БД.

        Преобразует структуру VK API в формат для базы данных,
        включая все метаданные, метрики и информацию о видео.

        Args:
            post: Данные поста от VK API
            source_type: Тип источника ('group' или 'user')
            owner_name: Название источника
            hashtag: Хештег поиска

        Returns:
            Dict: Словарь со всеми полями для сохранения в БД

        Example:
            >>> data = parser.parse_post_data(post, 'group', 'Медиастанция', '#Снежинск')
            >>> print(data['post_id'], data['likes'])
        """
        # Получение ID (owner_id может быть в разных полях)
        owner_id = post.get('owner_id') or post.get('from_id')
        post_id = post.get('id')

        # Базовые данные поста
        post_data = {
            'post_id': self.parse_post_id(owner_id, post_id),
            'source_type': source_type,
            'owner_id': owner_id,
            'owner_name': owner_name,
            'post_url': self.build_post_url(owner_id, post_id),
            'text': post.get('text', ''),
            'date_published': post.get('date', 0),
            'hashtag': hashtag
        }

        # Метрики поста
        metrics = self._extract_metrics(post)
        post_data.update(metrics)

        # Информация о видео
        video_info = self.extract_video_info(post)
        post_data.update(video_info)

        # Временные метки
        current_timestamp = int(datetime.now().timestamp())
        post_data.update({
            'first_collected': current_timestamp,
            'last_updated': current_timestamp
        })

        self.logger.debug(
            f"Распарсен пост {post_data['post_id']}: "
            f"просмотры={metrics['post_views']}, лайки={metrics['likes']}"
        )

        return post_data

    def parse_metrics(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает только метрики для обновления существующего поста.

        Используется при обновлении постов в БД - извлекает
        только изменяемые поля (метрики и видео).

        Args:
            post: Данные поста от VK API

        Returns:
            Dict: Словарь с метриками для обновления

        Example:
            >>> metrics = parser.parse_metrics(post)
            >>> print(metrics['likes'], metrics['last_updated'])
            145 1699999999
        """
        # Извлечение метрик
        metrics = self._extract_metrics(post)

        # Информация о видео
        video_info = self.extract_video_info(post)
        metrics.update(video_info)

        # Временная метка обновления
        metrics['last_updated'] = int(datetime.now().timestamp())

        self.logger.debug(
            f"Извлечены метрики для обновления: "
            f"просмотры={metrics['post_views']}, лайки={metrics['likes']}"
        )

        return metrics
