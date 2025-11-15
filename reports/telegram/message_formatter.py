"""
Форматирование текстовых сообщений для Telegram.

Модуль создаёт красиво отформатированные текстовые отчёты
с использованием Markdown и эмодзи.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List


class MessageFormatter:
    """
    Форматтер сообщений для Telegram.

    Отвечает ТОЛЬКО за создание текста сообщений.
    НЕ отправляет сообщения, только форматирует текст.
    """

    # Лимит длины сообщения в Telegram
    MAX_LENGTH = 4096

    @staticmethod
    def _format_number(value: int) -> str:
        """
        Форматирует число с пробелами для тысяч.

        Args:
            value: Число для форматирования

        Returns:
            str: Отформатированное число

        Example:
            >>> MessageFormatter._format_number(1234567)
            '1 234 567'
        """
        return f"{value:,}".replace(',', ' ')

    @staticmethod
    def _format_percentage(value: float) -> str:
        """
        Форматирует процент.

        Args:
            value: Значение процента

        Returns:
            str: Отформатированный процент

        Example:
            >>> MessageFormatter._format_percentage(5.56)
            '5.56%'
        """
        return f"{value:.2f}%"

    @staticmethod
    def _format_stat_line(label: str, value: Any) -> str:
        """
        Форматирует одну строку статистики.

        Args:
            label: Название метрики
            value: Значение метрики

        Returns:
            str: Отформатированная строка

        Example:
            >>> MessageFormatter._format_stat_line("Постов", 150)
            'Постов: `150`'
        """
        return f"{label}: `{value}`"

    def format_report_message(
        self,
        total_stats: Dict[str, Any],
        last_24h_stats: Dict[str, Any],
        breakdown: Dict[str, Dict[str, int]],
        top_posts: Optional[List[Dict[str, Any]]] = None,
        sheet_url: Optional[str] = None,
        unique_authors: Optional[Dict[str, int]] = None
    ) -> str:
        """
        Создаёт полное текстовое сообщение отчёта.

        Args:
            total_stats: Общая статистика
            last_24h_stats: Статистика за 24 часа
            breakdown: Разбивка по типам
            top_posts: ТОП-3 самых популярных постов (опционально)
            sheet_url: Ссылка на Google Sheets (опционально)
            unique_authors: Количество уникальных авторов (опционально)

        Returns:
            str: Отформатированное сообщение в Markdown

        Example:
            >>> message = formatter.format_report_message(stats, h24, breakdown, top_posts)
            >>> print(len(message))
            1024
        """
        # Заголовок с датой
        current_date = datetime.now().strftime('%d.%m.%Y')

        lines = [
            "📊 *ОТЧЁТ ПО МОНИТОРИНГУ #Снежинск*",
            f"📅 {current_date}",
            ""
        ]

        # Блок общей статистики
        lines.extend([
            "📈 *ОБЩАЯ СТАТИСТИКА*",
            self._format_stat_line(
                "Всего постов",
                self._format_number(total_stats['total_posts'])
            ),
            self._format_stat_line(
                "Просмотры",
                self._format_number(total_stats['total_views'])
            ),
            self._format_stat_line(
                "Лайки",
                self._format_number(total_stats['total_likes'])
            ),
            self._format_stat_line(
                "Комментарии",
                self._format_number(total_stats['total_comments'])
            ),
            self._format_stat_line(
                "Репосты",
                self._format_number(total_stats['total_reposts'])
            ),
            self._format_stat_line(
                "Средний ER",
                self._format_percentage(total_stats['avg_er'])
            ),
            ""
        ])

        # Блок за последние 24 часа
        lines.extend([
            "🔥 *ЗА ПОСЛЕДНИЕ 24 ЧАСА*",
            self._format_stat_line(
                "Новых постов",
                self._format_number(last_24h_stats['new_posts'])
            ),
            self._format_stat_line(
                "Просмотры",
                self._format_number(last_24h_stats['views'])
            ),
            self._format_stat_line(
                "Лайки",
                self._format_number(last_24h_stats['likes'])
            ),
            self._format_stat_line(
                "Комментарии",
                self._format_number(last_24h_stats['comments'])
            ),
            self._format_stat_line(
                "Репосты",
                self._format_number(last_24h_stats['reposts'])
            ),
            ""
        ])

        # Блок разбивки
        by_source = breakdown['by_source']
        by_video = breakdown['by_video']

        lines.extend([
            "📋 *РАЗБИВКА*",
            f"👥 Группы: `{by_source['groups']}` | Личные: `{by_source['users']}`",
            f"🎬 С видео: `{by_video['with_video']}` | Без видео: `{by_video['without_video']}`",
            ""
        ])

        # Блок уникальных авторов (если предоставлен)
        if unique_authors:
            lines.extend([
                "👤 *УНИКАЛЬНЫЕ АВТОРЫ*",
                f"Всего: `{unique_authors['total']}`",
                f"Группы: `{unique_authors['groups']}` | Пользователи: `{unique_authors['users']}`",
                ""
            ])

        # ТОП-3 самых популярных постов (если есть)
        if top_posts and len(top_posts) > 0:
            lines.extend([
                "🏆 *ТОП-3 ПОСТА*",
                ""
            ])

            # Медали для топ-3
            medals = ['🥇', '🥈', '🥉']

            for i, post in enumerate(top_posts[:3]):  # Ограничение до 3 постов
                # Определение типа источника
                source_type = post.get('source_type', '')
                source_label = 'Группа' if source_type == 'group' else 'Пользователь'

                # Форматирование данных поста
                author_name = post.get('owner_name', 'Неизвестно')
                views = self._format_number(post.get('post_views', 0))
                likes = self._format_number(post.get('likes', 0))
                comments = self._format_number(post.get('comments', 0))
                post_url = post.get('post_url', '')

                lines.extend([
                    f"{medals[i]} {i + 1}. {author_name} ({source_label})",
                    f"📊 {views} просмотров | ❤️ {likes} лайков | 💬 {comments} комментариев",
                    f"[🔗 Смотреть пост]({post_url})",
                    ""
                ])

        # Ссылка на Google Sheets (если есть)
        if sheet_url:
            lines.extend([
                "📑 [Полный отчёт в Google Sheets](" + sheet_url + ")",
                ""
            ])

        # Сборка сообщения
        message = "\n".join(lines)

        # Проверка длины
        if len(message) > self.MAX_LENGTH:
            # Обрезка если превышает лимит
            message = message[:self.MAX_LENGTH - 50]
            message += "\n\n_Сообщение обрезано из-за лимита Telegram_"

        return message
