"""
Слой работы с SQLite базой данных.

Модуль предоставляет класс Database для хранения и получения
информации о постах из ВКонтакте.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class Database:
    """
    Класс для работы с SQLite базой данных постов.

    Предоставляет методы для создания таблиц, добавления, обновления
    и получения информации о постах.
    """

    def __init__(self, db_path: str, logger: Optional[logging.Logger] = None):
        """
        Инициализирует подключение к базе данных.

        Args:
            db_path: Путь к файлу базы данных SQLite
            logger: Объект логгера (опционально)
        """
        self.db_path = Path(db_path)
        self.logger = logger or logging.getLogger(__name__)

        # Создание директории для БД, если её нет
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Создание подключения
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()

        self.logger.info(f"Подключение к базе данных: {self.db_path}")

    def _connect(self) -> None:
        """
        Создает подключение к базе данных.
        """
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            self.logger.debug("Соединение с БД установлено")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка подключения к БД: {e}")
            raise

    @contextmanager
    def _get_cursor(self):
        """
        Контекстный менеджер для получения курсора БД.

        Yields:
            sqlite3.Cursor: Курсор для выполнения SQL запросов
        """
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except sqlite3.Error as e:
            self.connection.rollback()
            self.logger.error(f"Ошибка выполнения SQL запроса: {e}")
            raise
        finally:
            cursor.close()

    def init_db(self) -> None:
        """
        Создает таблицу posts если её нет.

        Структура таблицы включает поля для хранения метаданных поста,
        метрик просмотров, реакций и информации о видео.
        """
        create_table_query = """
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            owner_name TEXT,
            post_url TEXT,
            text TEXT,
            date_published INTEGER,
            post_views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            reposts INTEGER DEFAULT 0,
            has_video INTEGER DEFAULT 0,
            video_views INTEGER DEFAULT 0,
            video_duration INTEGER,
            video_title TEXT,
            first_collected INTEGER,
            last_updated INTEGER,
            hashtag TEXT
        );
        """

        create_date_index = """
        CREATE INDEX IF NOT EXISTS idx_date_published ON posts(date_published);
        """

        create_updated_index = """
        CREATE INDEX IF NOT EXISTS idx_last_updated ON posts(last_updated);
        """

        try:
            with self._get_cursor() as cursor:
                cursor.execute(create_table_query)
                cursor.execute(create_date_index)
                cursor.execute(create_updated_index)

            self.logger.info("Таблица posts успешно инициализирована")
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка инициализации таблицы: {e}")
            raise

    def add_post(self, post_data: Dict[str, Any]) -> bool:
        """
        Добавляет новый пост в базу данных.

        Args:
            post_data: Словарь с данными поста (должен содержать post_id)

        Returns:
            bool: True если пост успешно добавлен, False в противном случае

        Example:
            >>> db.add_post({
            ...     'post_id': '12345_67890',
            ...     'source_type': 'wall',
            ...     'owner_id': 12345,
            ...     'text': 'Пример поста'
            ... })
        """
        insert_query = """
        INSERT INTO posts (
            post_id, source_type, owner_id, owner_name, post_url, text,
            date_published, post_views, likes, comments, reposts,
            has_video, video_views, video_duration, video_title,
            first_collected, last_updated, hashtag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            with self._get_cursor() as cursor:
                cursor.execute(insert_query, (
                    post_data.get('post_id'),
                    post_data.get('source_type'),
                    post_data.get('owner_id'),
                    post_data.get('owner_name'),
                    post_data.get('post_url'),
                    post_data.get('text'),
                    post_data.get('date_published'),
                    post_data.get('post_views', 0),
                    post_data.get('likes', 0),
                    post_data.get('comments', 0),
                    post_data.get('reposts', 0),
                    post_data.get('has_video', 0),
                    post_data.get('video_views', 0),
                    post_data.get('video_duration'),
                    post_data.get('video_title'),
                    post_data.get('first_collected'),
                    post_data.get('last_updated'),
                    post_data.get('hashtag')
                ))

            self.logger.debug(f"Пост {post_data.get('post_id')} добавлен в БД")
            return True

        except sqlite3.IntegrityError:
            self.logger.warning(f"Пост {post_data.get('post_id')} уже существует в БД")
            return False
        except sqlite3.Error as e:
            self.logger.error(f"Ошибка добавления поста: {e}")
            return False

    def update_post(self, post_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Обновляет метрики существующего поста.

        Args:
            post_id: Идентификатор поста
            metrics: Словарь с обновляемыми метриками

        Returns:
            bool: True если пост успешно обновлен, False в противном случае

        Example:
            >>> db.update_post('12345_67890', {
            ...     'likes': 100,
            ...     'comments': 25,
            ...     'last_updated': 1699999999
            ... })
        """
        # Формируем SET часть запроса на основе переданных метрик
        set_clause = ", ".join([f"{key} = ?" for key in metrics.keys()])
        update_query = f"UPDATE posts SET {set_clause} WHERE post_id = ?"

        try:
            with self._get_cursor() as cursor:
                values = list(metrics.values()) + [post_id]
                cursor.execute(update_query, values)

                if cursor.rowcount > 0:
                    self.logger.debug(f"Пост {post_id} обновлен в БД")
                    return True
                else:
                    self.logger.warning(f"Пост {post_id} не найден для обновления")
                    return False

        except sqlite3.Error as e:
            self.logger.error(f"Ошибка обновления поста: {e}")
            return False

    def get_all_posts(self) -> List[Dict[str, Any]]:
        """
        Получает все посты из базы данных.

        Returns:
            List[Dict]: Список словарей с данными всех постов

        Example:
            >>> posts = db.get_all_posts()
            >>> for post in posts:
            ...     print(post['post_id'], post['likes'])
        """
        select_query = "SELECT * FROM posts ORDER BY date_published DESC"

        try:
            with self._get_cursor() as cursor:
                cursor.execute(select_query)
                rows = cursor.fetchall()

            posts = [dict(row) for row in rows]
            self.logger.debug(f"Получено {len(posts)} постов из БД")
            return posts

        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения постов: {e}")
            return []

    def get_posts_by_date_range(
        self,
        start_date: int,
        end_date: int
    ) -> List[Dict[str, Any]]:
        """
        Получает посты за указанный период времени.

        Args:
            start_date: Начальная дата (UNIX timestamp)
            end_date: Конечная дата (UNIX timestamp)

        Returns:
            List[Dict]: Список словарей с данными постов за период

        Example:
            >>> posts = db.get_posts_by_date_range(1699000000, 1699999999)
        """
        select_query = """
        SELECT * FROM posts
        WHERE date_published BETWEEN ? AND ?
        ORDER BY date_published DESC
        """

        try:
            with self._get_cursor() as cursor:
                cursor.execute(select_query, (start_date, end_date))
                rows = cursor.fetchall()

            posts = [dict(row) for row in rows]
            self.logger.debug(
                f"Получено {len(posts)} постов за период "
                f"{start_date} - {end_date}"
            )
            return posts

        except sqlite3.Error as e:
            self.logger.error(f"Ошибка получения постов по дате: {e}")
            return []

    def post_exists(self, post_id: str) -> bool:
        """
        Проверяет существование поста в базе данных.

        Args:
            post_id: Идентификатор поста

        Returns:
            bool: True если пост существует, False в противном случае

        Example:
            >>> if db.post_exists('12345_67890'):
            ...     print("Пост уже в базе")
        """
        check_query = "SELECT 1 FROM posts WHERE post_id = ? LIMIT 1"

        try:
            with self._get_cursor() as cursor:
                cursor.execute(check_query, (post_id,))
                result = cursor.fetchone()

            exists = result is not None
            self.logger.debug(f"Пост {post_id} {'найден' if exists else 'не найден'} в БД")
            return exists

        except sqlite3.Error as e:
            self.logger.error(f"Ошибка проверки существования поста: {e}")
            return False

    def get_post_count(self) -> int:
        """
        Возвращает общее количество постов в базе данных.

        Returns:
            int: Количество постов
        """
        count_query = "SELECT COUNT(*) FROM posts"

        try:
            with self._get_cursor() as cursor:
                cursor.execute(count_query)
                result = cursor.fetchone()

            count = result[0] if result else 0
            self.logger.debug(f"Всего постов в БД: {count}")
            return count

        except sqlite3.Error as e:
            self.logger.error(f"Ошибка подсчета постов: {e}")
            return 0

    def close(self) -> None:
        """
        Закрывает соединение с базой данных.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Соединение с БД закрыто")

    def __enter__(self):
        """
        Поддержка context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Закрытие соединения при выходе из context manager.
        """
        self.close()

    def __del__(self):
        """
        Деструктор для закрытия соединения.
        """
        self.close()
