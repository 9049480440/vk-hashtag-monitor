#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки отчёта в Telegram.

Проверяет подключение к Telegram Bot API и отправку
текстового отчёта с графиками.
"""

import sys
import time

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
    from reports.telegram import TelegramReporter
    from reports.google_sheets import GoogleSheetsReporter
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


def test_telegram() -> bool:
    """
    Тестирует отправку отчёта в Telegram.

    Returns:
        bool: True если тест успешен
    """
    print_header("ТЕСТИРОВАНИЕ TELEGRAM ОТЧЁТА")

    # 1. Проверка конфигурации
    print_info("Проверка конфигурации...")

    try:
        Config.load_from_env()
        print_success("Конфигурация загружена")
    except Exception as e:
        print_error(f"Ошибка загрузки конфигурации: {e}")
        return False

    # 2. Проверка TELEGRAM_BOT_TOKEN
    if not Config.TELEGRAM_BOT_TOKEN:
        print_error("TELEGRAM_BOT_TOKEN не заполнен в .env!")
        print_info("Получите токен у @BotFather в Telegram:")
        print("   1. Напишите @BotFather в Telegram")
        print("   2. Отправьте команду /newbot")
        print("   3. Следуйте инструкциям")
        print("   4. Скопируйте токен в .env")
        return False

    print_success(f"Telegram Bot Token: {'*' * 20}...{Config.TELEGRAM_BOT_TOKEN[-10:]}")

    # 3. Проверка TELEGRAM_CHAT_ID
    if not Config.TELEGRAM_CHAT_ID:
        print_error("TELEGRAM_CHAT_ID не заполнен в .env!")
        print_info("Узнайте ID чата:")
        print("   1. Напишите @userinfobot в Telegram")
        print("   2. Отправьте любое сообщение")
        print("   3. Скопируйте 'Id' в .env как TELEGRAM_CHAT_ID")
        return False

    print_success(f"Telegram Chat ID: {Config.TELEGRAM_CHAT_ID}")

    # 4. Настройка логирования
    logger = setup_logger("test_telegram", Config.LOG_PATH)

    # 5. Подключение к БД
    print_info("Подключение к базе данных...")

    try:
        db = Database(Config.DB_PATH, logger)
        db.init_db()
        print_success(f"База данных: {Config.DB_PATH}")
    except Exception as e:
        print_error(f"Ошибка подключения к БД: {e}")
        return False

    # 6. Проверка наличия данных
    post_count = db.get_post_count()
    print_info(f"Постов в базе данных: {Fore.YELLOW}{post_count}{Style.RESET_ALL}")

    if post_count == 0:
        print_warning("База данных пуста!")
        print_info("Сначала соберите данные через test_collector.py")
        db.close()
        return False

    # 7. Проверка Google Sheets URL (опционально)
    sheet_url = None
    if Config.GOOGLE_SHEET_ID:
        sheet_url = f"https://docs.google.com/spreadsheets/d/{Config.GOOGLE_SHEET_ID}/edit"
        print_info(f"Google Sheets URL будет добавлен в отчёт")

    # 8. Создание репортера
    print_info("Инициализация Telegram Reporter...")

    try:
        reporter = TelegramReporter(
            config=Config,
            database=db,
            logger=logger,
            sheet_url=sheet_url
        )
        print_success("Telegram Reporter инициализирован")
    except Exception as e:
        print_error(f"Ошибка инициализации: {e}")
        db.close()
        return False

    # 9. Генерация и отправка отчёта
    print_header("ОТПРАВКА ОТЧЁТА В TELEGRAM")
    print_info("Генерация отчёта и отправка (это может занять время)...")

    start_time = time.time()

    try:
        result = reporter.generate_report()
        elapsed = time.time() - start_time

        if result:
            print_success(f"Отчёт отправлен успешно! ({elapsed:.2f} сек)")
            print()
            print(f"{Fore.GREEN}{Style.BRIGHT}{'=' * 70}")
            print(f"ОТЧЁТ ОТПРАВЛЕН В TELEGRAM!")
            print(f"{'=' * 70}{Style.RESET_ALL}")
            print()
            print(f"Проверьте Telegram чат: {Fore.CYAN}{Config.TELEGRAM_CHAT_ID}{Style.RESET_ALL}")
            print()
            print(f"Отправлено:")
            print(f"   📝 Текстовое сообщение со статистикой")
            print(f"   📊 Графики (publications, reach, engagement)")
            if sheet_url:
                print(f"   🔗 Ссылка на Google Sheets")
            print()

        else:
            print_error("Не удалось отправить отчёт")
            db.close()
            return False

    except Exception as e:
        elapsed = time.time() - start_time
        print_error(f"Ошибка при отправке отчёта ({elapsed:.2f} сек)")

        # Детальная обработка ошибок
        error_message = str(e).lower()

        if 'unauthorized' in error_message or 'token' in error_message:
            print_info("Проблема с токеном бота:")
            print("   Проверьте правильность TELEGRAM_BOT_TOKEN в .env")

        elif 'chat not found' in error_message or 'chat_id' in error_message:
            print_info("Проблема с Chat ID:")
            print("   1. Убедитесь что TELEGRAM_CHAT_ID правильный")
            print("   2. Напишите боту первым (начните диалог)")
            print("   3. Для групп - добавьте бота в группу")

        elif 'forbidden' in error_message:
            print_info("Бот не имеет прав на отправку:")
            print("   1. Убедитесь что вы начали диалог с ботом")
            print("   2. Для групп - дайте боту права администратора")

        else:
            import traceback
            print(f"\n{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")

        db.close()
        return False

    # 10. Закрытие БД
    db.close()
    return True


def main() -> None:
    """Основная функция тестирования."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         ТЕСТИРОВАНИЕ TELEGRAM - МЕДИАСТАНЦИЯ СНЕЖИНСК             ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")

    total_start = time.time()

    # Запуск теста
    success = test_telegram()

    # Итоговое время
    total_elapsed = time.time() - total_start

    if success:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}{'=' * 70}")
        print(f"ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО")
        print(f"Общее время выполнения: {total_elapsed:.2f} секунд")
        print(f"{'=' * 70}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.RED}{Style.BRIGHT}{'=' * 70}")
        print(f"ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
        print(f"Время выполнения: {total_elapsed:.2f} секунд")
        print(f"{'=' * 70}{Style.RESET_ALL}\n")
        sys.exit(1)


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
