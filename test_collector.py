#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы VK коллектора.

Проверяет конфигурацию, подключение к VK API, сбор постов,
обновление метрик и корректность сохранения в БД.
"""

import sys
import time
from datetime import datetime
from typing import Optional, Tuple

# Цветной вывод в консоль
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # Заглушки если colorama не установлена
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""

# Импорт модулей проекта
try:
    from config import Config
    from database import Database
    from logger import setup_logger
    from collectors import VKCollector
except ImportError as e:
    print(f"{Fore.RED}Ошибка импорта модулей проекта: {e}")
    print("Убедитесь что вы запускаете скрипт из корневой директории проекта")
    sys.exit(1)


def print_header(text: str) -> None:
    """Выводит заголовок раздела."""
    separator = "=" * 70
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{separator}")
    print(f"{text.center(70)}")
    print(f"{separator}{Style.RESET_ALL}\n")


def print_success(text: str) -> None:
    """Выводит сообщение об успехе."""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text: str) -> None:
    """Выводит сообщение об ошибке."""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")


def print_warning(text: str) -> None:
    """Выводит предупреждение."""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")


def print_info(text: str) -> None:
    """Выводит информационное сообщение."""
    print(f"{Fore.CYAN}ℹ {text}{Style.RESET_ALL}")


def format_timestamp(timestamp: int) -> str:
    """Форматирует UNIX timestamp в читаемую дату."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def test_configuration() -> bool:
    """
    Проверяет загрузку и валидность конфигурации.

    Returns:
        bool: True если конфигурация валидна
    """
    print_header("1. ПРОВЕРКА КОНФИГУРАЦИИ")

    try:
        start_time = time.time()
        Config.load_from_env()
        elapsed = time.time() - start_time

        print_success(f"Конфигурация загружена ({elapsed:.2f} сек)")
        print(f"   Хештег: {Fore.MAGENTA}{Config.HASHTAG}{Style.RESET_ALL}")
        print(f"   Дата начала: {Config.START_DATE}")
        print(f"   VK токен: {'*' * 20}...{Config.VK_TOKEN[-10:]}")
        print(f"   Задержка API: {Config.VK_API_DELAY} сек")

        return True

    except FileNotFoundError:
        print_error("Файл .env не найден!")
        print_info("Создайте файл .env на основе .env.example:")
        print("   cp .env.example .env")
        print("   # Затем заполните переменные в .env")
        return False

    except ValueError as e:
        print_error(f"Ошибка конфигурации: {e}")
        print_info("Проверьте что все обязательные переменные заполнены в .env")
        return False

    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        return False


def test_database(logger) -> Optional[Database]:
    """
    Проверяет создание и подключение к базе данных.

    Args:
        logger: Logger для логирования

    Returns:
        Optional[Database]: Объект базы данных или None
    """
    print_header("2. ПРОВЕРКА БАЗЫ ДАННЫХ")

    try:
        start_time = time.time()

        # Создание БД
        db = Database(Config.DB_PATH, logger)
        db.init_db()

        elapsed = time.time() - start_time

        print_success(f"База данных инициализирована ({elapsed:.2f} сек)")
        print(f"   Путь: {Config.DB_PATH}")

        # Получение статистики
        total_posts = db.get_post_count()
        print(f"   Постов в БД: {Fore.YELLOW}{total_posts}{Style.RESET_ALL}")

        return db

    except Exception as e:
        print_error(f"Ошибка работы с БД: {e}")
        print_info("Проверьте права доступа к папке data/")
        return None


def test_vk_collector(db: Database, logger) -> Optional[VKCollector]:
    """
    Проверяет создание и подключение VK коллектора.

    Args:
        db: База данных
        logger: Logger для логирования

    Returns:
        Optional[VKCollector]: Объект коллектора или None
    """
    print_header("3. ПРОВЕРКА VK КОЛЛЕКТОРА")

    try:
        start_time = time.time()

        # Создание коллектора
        collector = VKCollector(Config, db, logger)

        elapsed = time.time() - start_time

        print_success(f"VK коллектор инициализирован ({elapsed:.2f} сек)")
        print_success("Подключение к VK API успешно")

        return collector

    except Exception as e:
        print_error(f"Ошибка подключения к VK API: {e}")
        print_info("Возможные причины:")
        print("   - Неверный VK токен")
        print("   - Нет доступа к интернету")
        print("   - VK API временно недоступен")
        print_info("Получить новый токен: https://vk.com/dev")
        return None


def test_collect_new(collector: VKCollector, db: Database) -> int:
    """
    Тестирует сбор новых постов.

    Args:
        collector: VK коллектор
        db: База данных

    Returns:
        int: Количество добавленных постов
    """
    print_header("4. СБОР НОВЫХ ПОСТОВ")

    try:
        print_info(f"Поиск постов по хештегу: {Config.HASHTAG}")

        start_time = time.time()
        new_count = collector.collect_new_posts(Config.HASHTAG)
        elapsed = time.time() - start_time

        print_success(f"Сбор завершён ({elapsed:.2f} сек)")
        print(f"   Добавлено новых постов: {Fore.GREEN}{new_count}{Style.RESET_ALL}")

        # Показать примеры постов
        if new_count > 0:
            print_info("\nПримеры найденных постов (первые 3):")
            all_posts = db.get_all_posts()

            for i, post in enumerate(all_posts[:3], 1):
                print(f"\n   {Fore.YELLOW}Пост #{i}:{Style.RESET_ALL}")
                print(f"   └─ Автор: {post['owner_name']} ({post['source_type']})")
                print(f"   └─ Дата: {format_timestamp(post['date_published'])}")

                # Текст поста (первые 100 символов)
                text = post['text'][:100]
                if len(post['text']) > 100:
                    text += "..."
                print(f"   └─ Текст: {text.replace(chr(10), ' ')}")

                print(f"   └─ URL: {Fore.CYAN}{post['post_url']}{Style.RESET_ALL}")
                print(f"   └─ Метрики: 👁 {post['post_views']} | "
                      f"❤ {post['likes']} | "
                      f"💬 {post['comments']} | "
                      f"↗ {post['reposts']}")

                if post['has_video']:
                    print(f"   └─ Видео: {post['video_title']} "
                          f"({post['video_views']} просмотров)")

        return new_count

    except Exception as e:
        print_error(f"Ошибка при сборе постов: {e}")
        import traceback
        print(f"\n{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
        return 0


def test_update_metrics(collector: VKCollector, db: Database) -> Tuple[int, int]:
    """
    Тестирует обновление метрик постов.

    Args:
        collector: VK коллектор
        db: База данных

    Returns:
        Tuple[int, int]: (успешно_обновлено, ошибок)
    """
    print_header("5. ОБНОВЛЕНИЕ МЕТРИК")

    all_posts = db.get_all_posts()

    if not all_posts:
        print_warning("В БД нет постов для обновления")
        return (0, 0)

    print_info(f"Постов для обновления: {len(all_posts)}")

    # Сохранить метрики первого поста для сравнения
    example_post = all_posts[0]
    old_metrics = {
        'post_id': example_post['post_id'],
        'views': example_post['post_views'],
        'likes': example_post['likes'],
        'comments': example_post['comments'],
        'reposts': example_post['reposts']
    }

    try:
        start_time = time.time()
        updated, errors = collector.update_all_posts()
        elapsed = time.time() - start_time

        print_success(f"Обновление завершено ({elapsed:.2f} сек)")
        print(f"   Успешно обновлено: {Fore.GREEN}{updated}{Style.RESET_ALL}")
        print(f"   Ошибок: {Fore.RED}{errors}{Style.RESET_ALL}")

        # Показать изменения на примере
        if updated > 0:
            # Получить обновлённые данные
            updated_posts = db.get_all_posts()
            new_post = next(
                (p for p in updated_posts if p['post_id'] == old_metrics['post_id']),
                None
            )

            if new_post:
                print_info("\nПример обновления метрик:")
                print(f"   Пост: {new_post['post_url']}")
                print(f"   Просмотры: {old_metrics['views']} → "
                      f"{Fore.GREEN}{new_post['post_views']}{Style.RESET_ALL}")
                print(f"   Лайки: {old_metrics['likes']} → "
                      f"{Fore.GREEN}{new_post['likes']}{Style.RESET_ALL}")
                print(f"   Комментарии: {old_metrics['comments']} → "
                      f"{Fore.GREEN}{new_post['comments']}{Style.RESET_ALL}")
                print(f"   Репосты: {old_metrics['reposts']} → "
                      f"{Fore.GREEN}{new_post['reposts']}{Style.RESET_ALL}")

        return (updated, errors)

    except Exception as e:
        print_error(f"Ошибка при обновлении метрик: {e}")
        import traceback
        print(f"\n{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
        return (0, 0)


def print_summary(db: Database) -> None:
    """
    Выводит итоговую статистику по базе данных.

    Args:
        db: База данных
    """
    print_header("6. ИТОГОВАЯ СТАТИСТИКА")

    all_posts = db.get_all_posts()

    if not all_posts:
        print_warning("База данных пуста")
        return

    # Общее количество
    total = len(all_posts)
    print(f"Всего постов в БД: {Fore.YELLOW}{total}{Style.RESET_ALL}")

    # Диапазон дат
    dates = [p['date_published'] for p in all_posts if p['date_published']]
    if dates:
        min_date = format_timestamp(min(dates))
        max_date = format_timestamp(max(dates))
        print(f"Диапазон дат: {min_date} → {max_date}")

    # Посты с видео
    with_video = sum(1 for p in all_posts if p['has_video'])
    without_video = total - with_video
    print(f"С видео: {Fore.GREEN}{with_video}{Style.RESET_ALL} | "
          f"Без видео: {Fore.CYAN}{without_video}{Style.RESET_ALL}")

    # Типы источников
    groups = sum(1 for p in all_posts if p['source_type'] == 'group')
    users = sum(1 for p in all_posts if p['source_type'] == 'user')
    print(f"Группы: {Fore.MAGENTA}{groups}{Style.RESET_ALL} | "
          f"Пользователи: {Fore.CYAN}{users}{Style.RESET_ALL}")

    # Топ по просмотрам
    top_post = max(all_posts, key=lambda p: p['post_views'])
    print(f"\nСамый популярный пост:")
    print(f"   URL: {Fore.CYAN}{top_post['post_url']}{Style.RESET_ALL}")
    print(f"   Просмотров: {Fore.GREEN}{top_post['post_views']}{Style.RESET_ALL}")
    print(f"   Лайков: {top_post['likes']}")


def main() -> None:
    """Основная функция тестирования."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         ТЕСТИРОВАНИЕ VK КОЛЛЕКТОРА - МЕДИАСТАНЦИЯ СНЕЖИНСК        ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")

    total_start = time.time()

    # 1. Проверка конфигурации
    if not test_configuration():
        print_error("\nТестирование прервано из-за ошибок конфигурации")
        sys.exit(1)

    # 2. Настройка логирования
    logger = setup_logger("test_collector", Config.LOG_PATH)
    logger.info("Запуск тестирования VK коллектора")

    # 3. Проверка БД
    db = test_database(logger)
    if not db:
        print_error("\nТестирование прервано из-за ошибок БД")
        sys.exit(1)

    # 4. Проверка VK коллектора
    collector = test_vk_collector(db, logger)
    if not collector:
        print_error("\nТестирование прервано из-за ошибок VK API")
        sys.exit(1)

    # 5. Сбор новых постов
    new_posts = test_collect_new(collector, db)

    # 6. Обновление метрик (если есть посты)
    if db.get_post_count() > 0:
        test_update_metrics(collector, db)
    else:
        print_warning("\nОбновление метрик пропущено - в БД нет постов")

    # 7. Итоговая статистика
    print_summary(db)

    # Закрытие БД
    db.close()

    # Итоговое время
    total_elapsed = time.time() - total_start
    print(f"\n{Fore.GREEN}{Style.BRIGHT}{'=' * 70}")
    print(f"ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
    print(f"Общее время выполнения: {total_elapsed:.2f} секунд")
    print(f"{'=' * 70}{Style.RESET_ALL}\n")

    logger.info(f"Тестирование завершено за {total_elapsed:.2f} сек")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Тестирование прервано пользователем{Style.RESET_ALL}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}КРИТИЧЕСКАЯ ОШИБКА: {e}{Style.RESET_ALL}\n")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
