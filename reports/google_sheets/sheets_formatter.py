"""
Форматирование данных для листов Google Sheets.

Модуль преобразует данные из БД в структуру,
подходящую для отображения в Google Sheets.
"""

from datetime import datetime
from typing import List, Dict, Any


class SheetsFormatter:
    """
    Класс для форматирования данных для листов Google Sheets.

    Отвечает ТОЛЬКО за подготовку данных для отображения.
    НЕ делает API запросы и не знает про БД.
    """

    @staticmethod
    def format_date(timestamp: int) -> str:
        """
        Форматирует UNIX timestamp в читаемую дату.

        Args:
            timestamp: UNIX timestamp

        Returns:
            str: Дата в формате DD.MM.YYYY HH:MM
        """
        return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")

    @staticmethod
    def format_number(number: int) -> str:
        """
        Форматирует число с пробелами для тысяч.

        Args:
            number: Число для форматирования

        Returns:
            str: Отформатированное число

        Example:
            >>> SheetsFormatter.format_number(1234567)
            '1 234 567'
        """
        return f"{number:,}".replace(',', ' ')

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """
        Обрезает длинный текст.

        Args:
            text: Текст для обрезки
            max_length: Максимальная длина

        Returns:
            str: Обрезанный текст
        """
        if len(text) <= max_length:
            return text
        return text[:max_length] + '...'

    def format_summary_sheet(
        self,
        total_stats: Dict[str, Any],
        last_24h_stats: Dict[str, Any],
        breakdown: Dict[str, Dict[str, int]]
    ) -> List[List[Any]]:
        """
        Форматирует данные для листа "Сводка".

        Args:
            total_stats: Общая статистика
            last_24h_stats: Статистика за 24 часа
            breakdown: Разбивка по типам

        Returns:
            List[List]: 2D массив для записи в Google Sheets
        """
        data = []

        # Заголовок секции
        data.append(['ОБЩАЯ СТАТИСТИКА', ''])
        data.append(['Метрика', 'Значение'])

        # Общая статистика
        data.append(['Всего постов', total_stats['total_posts']])
        data.append(['Всего просмотров', self.format_number(total_stats['total_views'])])
        data.append(['Всего лайков', self.format_number(total_stats['total_likes'])])
        data.append(['Всего комментариев', self.format_number(total_stats['total_comments'])])
        data.append(['Всего репостов', self.format_number(total_stats['total_reposts'])])
        data.append(['Средний ER', f"{total_stats['avg_er']}%"])

        # Пустая строка
        data.append(['', ''])

        # За последние 24 часа
        data.append(['ЗА ПОСЛЕДНИЕ 24 ЧАСА', ''])
        data.append(['Метрика', 'Значение'])
        data.append(['Новых постов', last_24h_stats['new_posts']])
        data.append(['Просмотров', self.format_number(last_24h_stats['views'])])
        data.append(['Лайков', self.format_number(last_24h_stats['likes'])])
        data.append(['Комментариев', self.format_number(last_24h_stats['comments'])])
        data.append(['Репостов', self.format_number(last_24h_stats['reposts'])])

        # Пустая строка
        data.append(['', ''])

        # Разбивка
        data.append(['РАЗБИВКА', ''])
        data.append(['Категория', 'Значение'])
        data.append(['Группы', breakdown['by_source']['groups']])
        data.append(['Личные страницы', breakdown['by_source']['users']])
        data.append(['С видео', breakdown['by_video']['with_video']])
        data.append(['Без видео', breakdown['by_video']['without_video']])

        # Уникальные авторы (если есть в breakdown)
        if 'unique_authors' in breakdown:
            unique_authors = breakdown['unique_authors']
            data.append(['', ''])
            data.append(['УНИКАЛЬНЫЕ АВТОРЫ', ''])
            data.append(['Всего авторов', unique_authors['total']])
            data.append(['Уникальных групп', unique_authors['groups']])
            data.append(['Уникальных пользователей', unique_authors['users']])

        return data

    def format_all_posts_sheet(self, posts: List[Dict[str, Any]]) -> List[List[Any]]:
        """
        Форматирует данные для листа "Все посты".

        Args:
            posts: Список всех постов

        Returns:
            List[List]: 2D массив для записи в Google Sheets
        """
        # Заголовки
        headers = [
            'Дата',
            'Автор',
            'Тип',
            'Ссылка',
            'Текст (начало)',
            'Просмотры поста',
            'Просмотры видео',
            'Лайки',
            'Комментарии',
            'Репосты',
            'ER%'
        ]

        data = [headers]

        # Данные постов
        for post in posts:
            # Расчёт ER
            views = post.get('post_views', 0)
            if views > 0:
                engagement = (
                    post.get('likes', 0) +
                    post.get('comments', 0) +
                    post.get('reposts', 0)
                )
                er = round((engagement / views) * 100, 2)
            else:
                er = 0.0

            row = [
                self.format_date(post.get('date_published', 0)),
                post.get('owner_name', 'Неизвестно'),
                'Группа' if post.get('source_type') == 'group' else 'Пользователь',
                post.get('post_url', ''),
                post.get('text', ''),
                post.get('post_views', 0),
                post.get('video_views', 0) if post.get('has_video') else 0,
                post.get('likes', 0),
                post.get('comments', 0),
                post.get('reposts', 0),
                er
            ]

            data.append(row)

        return data

    def format_top_posts_sheet(
        self,
        top_by_views: List[Dict[str, Any]],
        top_by_er: List[Dict[str, Any]],
        top_by_comments: List[Dict[str, Any]]
    ) -> List[List[Any]]:
        """
        Форматирует данные для листа "ТОП-10".

        Args:
            top_by_views: Топ по просмотрам
            top_by_er: Топ по ER
            top_by_comments: Топ по комментариям

        Returns:
            List[List]: 2D массив для записи в Google Sheets
        """
        data = []

        # Заголовки для таблицы топа
        top_headers = ['#', 'Автор', 'Ссылка', 'Просмотры', 'Лайки', 'Комментарии', 'ER%']

        # ТОП-10 по просмотрам
        data.append(['ТОП-10 ПО ПРОСМОТРАМ', '', '', '', '', '', ''])
        data.append(top_headers)

        for i, post in enumerate(top_by_views, 1):
            views = post.get('post_views', 0)
            engagement = (
                post.get('likes', 0) +
                post.get('comments', 0) +
                post.get('reposts', 0)
            )
            er = round((engagement / views) * 100, 2) if views > 0 else 0.0

            data.append([
                i,
                post.get('owner_name', 'Неизвестно'),
                post.get('post_url', ''),
                post.get('post_views', 0),
                post.get('likes', 0),
                post.get('comments', 0),
                er
            ])

        # Пустая строка
        data.append(['', '', '', '', '', '', ''])

        # ТОП-10 по ER
        data.append(['ТОП-10 ПО ВОВЛЕЧЁННОСТИ (ER)', '', '', '', '', '', ''])
        data.append(top_headers)

        for i, post in enumerate(top_by_er, 1):
            views = post.get('post_views', 0)
            engagement = (
                post.get('likes', 0) +
                post.get('comments', 0) +
                post.get('reposts', 0)
            )
            er = round((engagement / views) * 100, 2) if views > 0 else 0.0

            data.append([
                i,
                post.get('owner_name', 'Неизвестно'),
                post.get('post_url', ''),
                post.get('post_views', 0),
                post.get('likes', 0),
                post.get('comments', 0),
                er
            ])

        # Пустая строка
        data.append(['', '', '', '', '', '', ''])

        # ТОП-10 по комментариям
        data.append(['ТОП-10 ПО КОММЕНТАРИЯМ', '', '', '', '', '', ''])
        data.append(top_headers)

        for i, post in enumerate(top_by_comments, 1):
            views = post.get('post_views', 0)
            engagement = (
                post.get('likes', 0) +
                post.get('comments', 0) +
                post.get('reposts', 0)
            )
            er = round((engagement / views) * 100, 2) if views > 0 else 0.0

            data.append([
                i,
                post.get('owner_name', 'Неизвестно'),
                post.get('post_url', ''),
                post.get('post_views', 0),
                post.get('likes', 0),
                post.get('comments', 0),
                er
            ])

        return data

    def format_dynamics_sheet(self, daily_data: List[Dict[str, Any]]) -> List[List[Any]]:
        """
        Форматирует данные для листа "Динамика".

        Args:
            daily_data: Данные по дням

        Returns:
            List[List]: 2D массив для записи в Google Sheets
        """
        # Заголовки
        headers = [
            'Дата',
            'Новых постов',
            'Всего постов',
            'Просмотры',
            'Лайки',
            'Комментарии',
            'Репосты'
        ]

        data = [headers]

        # Данные по дням
        for day in daily_data:
            # Форматирование даты (только дата без времени)
            date_obj = datetime.strptime(day['date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d.%m.%Y')

            row = [
                formatted_date,
                day.get('new_posts', 0),
                day.get('total_posts', 0),
                day.get('views', 0),
                day.get('likes', 0),
                day.get('comments', 0),
                day.get('reposts', 0)
            ]

            data.append(row)

        return data
