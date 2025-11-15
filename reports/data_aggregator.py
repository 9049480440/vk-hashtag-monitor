"""
Модуль агрегации и расчёта статистики из базы данных.

Предоставляет класс DataAggregator для вычисления различных
метрик и статистики по постам из БД.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from database import Database
from config import Config


class DataAggregator:
    """
    Класс для агрегации данных и расчёта статистики.

    Отвечает ТОЛЬКО за работу с данными и вычисления.
    НЕ знает про Google Sheets или другие форматы отчётов.
    """

    def __init__(self, database: Database, logger: logging.Logger):
        """
        Инициализирует агрегатор данных.

        Args:
            database: Экземпляр Database для получения данных
            logger: Logger для логирования операций
        """
        self.database = database
        self.logger = logger

    def calculate_engagement_rate(self, post: Dict[str, Any]) -> float:
        """
        Рассчитывает коэффициент вовлечённости (ER) для поста.

        Формула: (лайки + комментарии + репосты) / просмотры * 100%

        Args:
            post: Словарь с данными поста

        Returns:
            float: ER в процентах (0.0 если просмотров нет)

        Example:
            >>> er = aggregator.calculate_engagement_rate(post)
            >>> print(f"ER: {er:.2f}%")
            ER: 3.45%
        """
        views = post.get('post_views', 0)

        if views == 0:
            return 0.0

        engagement = (
            post.get('likes', 0) +
            post.get('comments', 0) +
            post.get('reposts', 0)
        )

        er = (engagement / views) * 100
        return round(er, 2)

    def get_total_stats(self) -> Dict[str, Any]:
        """
        Получает общую статистику по всем постам.

        Returns:
            Dict: Словарь с общей статистикой

        Example:
            >>> stats = aggregator.get_total_stats()
            >>> print(stats['total_posts'], stats['total_views'])
            150 45000
        """
        self.logger.info("Расчёт общей статистики")

        all_posts = self.database.get_all_posts()

        if not all_posts:
            self.logger.warning("База данных пуста")
            return {
                'total_posts': 0,
                'total_views': 0,
                'total_likes': 0,
                'total_comments': 0,
                'total_reposts': 0,
                'avg_er': 0.0
            }

        # Подсчёт суммарных метрик
        total_views = sum(p.get('post_views', 0) for p in all_posts)
        total_likes = sum(p.get('likes', 0) for p in all_posts)
        total_comments = sum(p.get('comments', 0) for p in all_posts)
        total_reposts = sum(p.get('reposts', 0) for p in all_posts)

        # Расчёт среднего ER
        er_values = [self.calculate_engagement_rate(p) for p in all_posts]
        avg_er = sum(er_values) / len(er_values) if er_values else 0.0

        stats = {
            'total_posts': len(all_posts),
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_reposts': total_reposts,
            'avg_er': round(avg_er, 2)
        }

        self.logger.info(f"Общая статистика: {stats['total_posts']} постов")
        return stats

    def get_last_24h_stats(self) -> Dict[str, Any]:
        """
        Получает статистику за последние 24 часа.

        Фильтрует посты по дате публикации (date_published),
        а не по дате сбора (first_collected).

        Returns:
            Dict: Словарь со статистикой за 24 часа

        Example:
            >>> stats = aggregator.get_last_24h_stats()
            >>> print(stats['new_posts'])
            5
        """
        self.logger.info("Расчёт статистики за последние 24 часа")

        # Временная граница (24 часа назад)
        time_24h_ago = int((datetime.now() - timedelta(hours=24)).timestamp())

        all_posts = self.database.get_all_posts()

        # Фильтрация постов за последние 24 часа (по дате публикации)
        recent_posts = [
            p for p in all_posts
            if p.get('date_published', 0) >= time_24h_ago
        ]

        if not recent_posts:
            self.logger.info("Новых постов за последние 24 часа нет")
            return {
                'new_posts': 0,
                'views': 0,
                'likes': 0,
                'comments': 0,
                'reposts': 0
            }

        # Подсчёт метрик
        stats = {
            'new_posts': len(recent_posts),
            'views': sum(p.get('post_views', 0) for p in recent_posts),
            'likes': sum(p.get('likes', 0) for p in recent_posts),
            'comments': sum(p.get('comments', 0) for p in recent_posts),
            'reposts': sum(p.get('reposts', 0) for p in recent_posts)
        }

        self.logger.info(f"За 24 часа: {stats['new_posts']} новых постов")
        return stats

    def get_top_posts(
        self,
        limit: int = 10,
        sort_by: str = 'views'
    ) -> List[Dict[str, Any]]:
        """
        Получает топ постов по заданному критерию.

        Args:
            limit: Количество постов в топе
            sort_by: Критерий сортировки ('views', 'er', 'comments')

        Returns:
            List[Dict]: Список топ постов

        Example:
            >>> top = aggregator.get_top_posts(10, 'er')
            >>> print(len(top))
            10
        """
        self.logger.info(f"Получение топ-{limit} постов по '{sort_by}'")

        all_posts = self.database.get_all_posts()

        if not all_posts:
            self.logger.warning("База данных пуста")
            return []

        # Определение ключа сортировки
        if sort_by == 'views':
            key_func = lambda p: p.get('post_views', 0)
        elif sort_by == 'er':
            key_func = lambda p: self.calculate_engagement_rate(p)
        elif sort_by == 'comments':
            key_func = lambda p: p.get('comments', 0)
        else:
            self.logger.warning(f"Неизвестный критерий '{sort_by}', использую 'views'")
            key_func = lambda p: p.get('post_views', 0)

        # Сортировка и выбор топ постов
        sorted_posts = sorted(all_posts, key=key_func, reverse=True)
        top_posts = sorted_posts[:limit]

        self.logger.info(f"Получено {len(top_posts)} постов в топе")
        return top_posts

    def get_daily_dynamics(self) -> List[Dict[str, Any]]:
        """
        Получает данные динамики по дням для графиков.

        Создаёт полный диапазон дат от START_DATE до сегодня,
        заполняя пропуски нулями для дней без постов.

        Returns:
            List[Dict]: Список с данными по каждому дню (включая дни без постов)

        Example:
            >>> dynamics = aggregator.get_daily_dynamics()
            >>> for day in dynamics:
            ...     print(day['date'], day['new_posts'])
        """
        self.logger.info("Расчёт ежедневной динамики")

        all_posts = self.database.get_all_posts()

        if not all_posts:
            self.logger.warning("База данных пуста")
            return []

        # Определение начальной даты
        start_date = None
        if Config.START_DATE:
            try:
                # Парсинг даты из формата YYYY-MM-DD
                start_date = datetime.strptime(Config.START_DATE, '%Y-%m-%d').date()
                self.logger.info(f"Используется START_DATE из конфига: {start_date}")
            except ValueError:
                self.logger.warning(
                    f"Неверный формат START_DATE: {Config.START_DATE}. "
                    f"Используется дата первого поста."
                )
                start_date = None

        # Если START_DATE не задан или неверный - использовать дату первого поста
        if start_date is None:
            first_post_timestamp = min(p.get('date_published', 0) for p in all_posts)
            start_date = datetime.fromtimestamp(first_post_timestamp).date()
            self.logger.info(f"Используется дата первого поста: {start_date}")

        # Конечная дата - сегодня
        end_date = datetime.now().date()

        # Группировка постов по датам
        daily_data = {}

        for post in all_posts:
            # Дата публикации (без времени)
            timestamp = post.get('date_published', 0)
            date = datetime.fromtimestamp(timestamp).date()
            date_str = date.strftime('%Y-%m-%d')

            if date_str not in daily_data:
                daily_data[date_str] = {
                    'date': date_str,
                    'new_posts': 0,
                    'views': 0,
                    'likes': 0,
                    'comments': 0,
                    'reposts': 0
                }

            daily_data[date_str]['new_posts'] += 1
            daily_data[date_str]['views'] += post.get('post_views', 0)
            daily_data[date_str]['likes'] += post.get('likes', 0)
            daily_data[date_str]['comments'] += post.get('comments', 0)
            daily_data[date_str]['reposts'] += post.get('reposts', 0)

        # Создание полного диапазона дат
        current_date = start_date
        full_data = []

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')

            if date_str in daily_data:
                # Есть данные за этот день
                full_data.append(daily_data[date_str])
            else:
                # Нет данных - заполняем нулями
                full_data.append({
                    'date': date_str,
                    'new_posts': 0,
                    'views': 0,
                    'likes': 0,
                    'comments': 0,
                    'reposts': 0
                })

            current_date += timedelta(days=1)

        # Добавление накопительного итога постов
        total_posts = 0
        for day in full_data:
            total_posts += day['new_posts']
            day['total_posts'] = total_posts

        self.logger.info(
            f"Динамика по {len(full_data)} дням "
            f"(с {start_date} по {end_date})"
        )
        return full_data

    def get_breakdown_by_type(self) -> Dict[str, Dict[str, int]]:
        """
        Получает разбивку постов по типам.

        Включает информацию о количестве постов по типам источников,
        наличию видео и количестве уникальных авторов.

        Returns:
            Dict: Словарь с разбивкой по типам источников, видео и авторам

        Example:
            >>> breakdown = aggregator.get_breakdown_by_type()
            >>> print(breakdown['by_source']['groups'])
            85
            >>> print(breakdown['unique_authors']['total'])
            45
        """
        self.logger.info("Расчёт разбивки по типам")

        all_posts = self.database.get_all_posts()

        if not all_posts:
            self.logger.warning("База данных пуста")
            return {
                'by_source': {'groups': 0, 'users': 0},
                'by_video': {'with_video': 0, 'without_video': 0},
                'unique_authors': {'total': 0, 'groups': 0, 'users': 0}
            }

        # Подсчёт по типам источников
        groups = sum(1 for p in all_posts if p.get('source_type') == 'group')
        users = sum(1 for p in all_posts if p.get('source_type') == 'user')

        # Подсчёт по наличию видео
        with_video = sum(1 for p in all_posts if p.get('has_video', 0) == 1)
        without_video = len(all_posts) - with_video

        # Получение информации об уникальных авторах
        unique_authors = self.get_unique_authors_count()

        breakdown = {
            'by_source': {
                'groups': groups,
                'users': users
            },
            'by_video': {
                'with_video': with_video,
                'without_video': without_video
            },
            'unique_authors': unique_authors
        }

        self.logger.info(f"Разбивка: группы={groups}, пользователи={users}")
        return breakdown

    def get_unique_authors_count(self) -> Dict[str, int]:
        """
        Получает количество уникальных авторов.

        Подсчитывает уникальные owner_id в базе данных
        как в общем, так и по типам источников.

        Returns:
            Dict: Словарь с количеством уникальных авторов

        Example:
            >>> authors = aggregator.get_unique_authors_count()
            >>> print(authors['total'], authors['groups'], authors['users'])
            45 30 15
        """
        self.logger.info("Подсчёт уникальных авторов")

        all_posts = self.database.get_all_posts()

        if not all_posts:
            self.logger.warning("База данных пуста")
            return {
                'total': 0,
                'groups': 0,
                'users': 0
            }

        # Множества для хранения уникальных owner_id
        all_authors = set()
        group_authors = set()
        user_authors = set()

        for post in all_posts:
            owner_id = post.get('owner_id')
            source_type = post.get('source_type')

            if owner_id is not None:
                all_authors.add(owner_id)

                if source_type == 'group':
                    group_authors.add(owner_id)
                elif source_type == 'user':
                    user_authors.add(owner_id)

        result = {
            'total': len(all_authors),
            'groups': len(group_authors),
            'users': len(user_authors)
        }

        self.logger.info(
            f"Уникальных авторов: всего={result['total']}, "
            f"групп={result['groups']}, пользователей={result['users']}"
        )
        return result
