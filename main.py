#!/usr/bin/env python3
"""
Главный скрипт-оркестратор VK Hashtag Monitor.

Обеспечивает два режима работы:
- Сбор данных из VK (--collect)
- Генерация и отправка отчётов (--report)
"""

import sys
import time
import argparse
import traceback
from typing import Optional, Tuple

from config import Config
from database import Database
from logger import setup_logger
from collectors.vk import VKCollector
from reports.google_sheets import GoogleSheetsReporter
from reports.telegram import TelegramReporter


# ANSI цветовые коды
class Colors:
    """ANSI коды для цветного вывода в консоль."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text: str) -> None:
    """
    Выводит заголовок раздела.

    Args:
        text: Текст заголовка
    """
    separator = "=" * 70
    print(f"\n{Colors.CYAN}{separator}")
    print(f"{text.center(70)}")
    print(f"{separator}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """
    Выводит сообщение об успехе.

    Args:
        text: Текст сообщения
    """
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """
    Выводит сообщение об ошибке.

    Args:
        text: Текст сообщения
    """
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """
    Выводит информационное сообщение.

    Args:
        text: Текст сообщения
    """
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")


def run_collect_mode(database: Database, logger) -> bool:
    """
    Выполняет режим сбора данных из VK.

    Args:
        database: Экземпляр базы данных
        logger: Logger для логирования

    Returns:
        bool: True если сбор успешен
    """
    print_header("РЕЖИМ: СБОР ДАННЫХ")

    try:
        # Инициализация VK коллектора
        print_info("Инициализация VK коллектора...")
        collector = VKCollector(
            config=Config,
            database=database,
            logger=logger
        )
        print_success("VK коллектор готов")

        # Сбор новых постов
        print_info(f"Поиск новых постов по хештегу: {Config.HASHTAG}")
        start_time = time.time()

        new_posts_count = collector.collect_new_posts(Config.HASHTAG)

        print_success(f"Добавлено новых постов: {new_posts_count}")

        # Обновление метрик существующих постов
        print_info("Обновление метрик существующих постов...")
        updated_count, failed_count = collector.update_all_posts()

        print_success(f"Обновлено метрик: {updated_count}")
        if failed_count > 0:
            print_error(f"Не удалось обновить: {failed_count}")

        # Вывод времени выполнения
        elapsed = time.time() - start_time
        print(f"\n{Colors.YELLOW}⏱  Сбор данных завершён за {elapsed:.1f} сек{Colors.RESET}")

        return True

    except Exception as e:
        logger.error(f"Ошибка при сборе данных: {e}", exc_info=True)
        print_error(f"Ошибка при сборе данных: {e}")
        print(f"\n{Colors.RED}{traceback.format_exc()}{Colors.RESET}")
        return False


def run_report_mode(database: Database, logger) -> bool:
    """
    Выполняет режим генерации и отправки отчётов.

    Args:
        database: Экземпляр базы данных
        logger: Logger для логирования

    Returns:
        bool: True если отчёты успешно сгенерированы
    """
    print_header("РЕЖИМ: ГЕНЕРАЦИЯ ОТЧЁТОВ")

    try:
        # Проверка наличия данных
        post_count = database.get_post_count()
        print_info(f"Постов в базе данных: {post_count}")

        if post_count == 0:
            print_error("База данных пуста! Сначала соберите данные через --collect")
            return False

        start_time = time.time()

        # Генерация Google Sheets отчёта
        print_info("Создание отчёта Google Sheets...")
        sheets_reporter = GoogleSheetsReporter(
            config=Config,
            database=database,
            logger=logger
        )

        sheet_url = sheets_reporter.generate_report()

        if sheet_url:
            print_success(f"Отчёт создан: {sheet_url}")
        else:
            print_error("Не удалось создать Google Sheets отчёт")
            sheet_url = None

        # Генерация и отправка Telegram отчёта
        print_info("Отправка отчёта в Telegram...")
        telegram_reporter = TelegramReporter(
            config=Config,
            database=database,
            logger=logger,
            sheet_url=sheet_url
        )

        telegram_result = telegram_reporter.generate_report()

        if telegram_result:
            print_success("Отчёт отправлен в Telegram")
        else:
            print_error("Не удалось отправить отчёт в Telegram")
            return False

        # Вывод времени выполнения
        elapsed = time.time() - start_time
        print(f"\n{Colors.YELLOW}⏱  Генерация отчётов завершена за {elapsed:.1f} сек{Colors.RESET}")

        return True

    except Exception as e:
        logger.error(f"Ошибка при генерации отчётов: {e}", exc_info=True)
        print_error(f"Ошибка при генерации отчётов: {e}")
        print(f"\n{Colors.RED}{traceback.format_exc()}{Colors.RESET}")
        return False


def main() -> int:
    """
    Главная функция - точка входа в приложение.

    Парсит аргументы командной строки и запускает соответствующие режимы.

    Returns:
        int: Код возврата (0 = успех, 1 = ошибка)
    """
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(
        description='VK Hashtag Monitor - система мониторинга постов ВКонтакте',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры использования:
  %(prog)s --collect              Только сбор данных
  %(prog)s --report               Только генерация отчётов
  %(prog)s --collect --report     Сбор данных + отчёты (полный цикл)
        '''
    )

    parser.add_argument(
        '--collect',
        action='store_true',
        help='Режим сбора данных из VK'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Режим генерации и отправки отчётов'
    )

    args = parser.parse_args()

    # Валидация аргументов
    if not args.collect and not args.report:
        parser.print_help()
        print(f"\n{Colors.RED}Ошибка: Укажите хотя бы один режим (--collect или --report){Colors.RESET}\n")
        return 1

    # Вывод заголовка приложения
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         VK HASHTAG MONITOR - МЕДИАСТАНЦИЯ СНЕЖИНСК                ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

    total_start = time.time()
    database = None
    logger = None

    try:
        # Инициализация конфигурации
        print_info("Загрузка конфигурации...")
        Config.load_from_env()
        print_success("Конфигурация загружена")

        # Инициализация логгера
        logger = setup_logger("main", Config.LOG_PATH)

        # Инициализация базы данных
        print_info("Подключение к базе данных...")
        database = Database(Config.DB_PATH, logger)
        database.init_db()
        print_success(f"База данных: {Config.DB_PATH}")

        # Выполнение режимов
        success = True

        if args.collect:
            if not run_collect_mode(database, logger):
                success = False

        if args.report:
            if not run_report_mode(database, logger):
                success = False

        # Итоговое время
        total_elapsed = time.time() - total_start

        # Вывод итога
        if success:
            print(f"\n{Colors.GREEN}{Colors.BOLD}{'=' * 70}")
            print(f"✓ ВСЕ ЗАДАЧИ ВЫПОЛНЕНЫ УСПЕШНО")
            print(f"Общее время выполнения: {total_elapsed:.1f} сек")
            print(f"{'=' * 70}{Colors.RESET}\n")
            return 0
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}{'=' * 70}")
            print(f"✗ ВЫПОЛНЕНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
            print(f"Время выполнения: {total_elapsed:.1f} сек")
            print(f"{'=' * 70}{Colors.RESET}\n")
            return 1

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        print_info("Убедитесь что файл .env создан на основе .env.example")
        return 1

    except ValueError as e:
        print_error(f"Ошибка конфигурации: {e}")
        print_info("Проверьте правильность заполнения .env файла")
        return 1

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Работа прервана пользователем{Colors.RESET}\n")
        return 0

    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        print(f"\n{Colors.RED}{traceback.format_exc()}{Colors.RESET}")
        return 1

    finally:
        # Закрытие ресурсов
        if database is not None:
            database.close()
            if logger:
                logger.info("База данных закрыта")


if __name__ == "__main__":
    sys.exit(main())
