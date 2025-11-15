#!/usr/bin/env python3
"""
Тестовый скрипт для проверки выгрузки отчёта в Google Sheets.

Проверяет подключение к Google Sheets API, генерацию отчёта
и корректность выгрузки данных.
"""

import sys
import time
from pathlib import Path

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
    from reports import GoogleSheetsReporter
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


def check_credentials_file(credentials_file: str) -> bool:
    """
    Проверяет наличие файла credentials.json.

    Args:
        credentials_file: Путь к файлу credentials

    Returns:
        bool: True если файл существует
    """
    credentials_path = Path(credentials_file)

    if not credentials_path.exists():
        print_error(f"Файл {credentials_file} не найден!")
        print_info("Инструкция по получению credentials.json:")
        print("   1. Перейдите в Google Cloud Console:")
        print("      https://console.cloud.google.com/")
        print("   2. Создайте проект или выберите существующий")
        print("   3. Включите Google Sheets API")
        print("   4. Создайте Service Account")
        print("   5. Скачайте JSON ключ и сохраните как credentials.json")
        print("   6. Дайте доступ к таблице для email из credentials.json")
        return False

    print_success(f"Файл {credentials_file} найден")
    return True


def test_google_sheets() -> bool:
    """
    Тестирует выгрузку отчёта в Google Sheets.

    Returns:
        bool: True если тест успешен
    """
    print_header("ТЕСТИРОВАНИЕ GOOGLE SHEETS ОТЧЁТА")

    # 1. Проверка конфигурации
    print_info("Проверка конфигурации...")

    try:
        Config.load_from_env()
        print_success("Конфигурация загружена")
    except Exception as e:
        print_error(f"Ошибка загрузки конфигурации: {e}")
        return False

    # 2. Проверка credentials.json
    print_info("Проверка файла credentials...")

    if not check_credentials_file(Config.GOOGLE_CREDENTIALS_FILE):
        return False

    # 3. Проверка GOOGLE_SHEET_ID
    if not Config.GOOGLE_SHEET_ID:
        print_error("GOOGLE_SHEET_ID не заполнен в .env!")
        print_info("Создайте новую таблицу в Google Sheets и скопируйте ID из URL:")
        print("   https://docs.google.com/spreadsheets/d/[THIS_IS_SHEET_ID]/edit")
        return False

    print_success(f"Google Sheet ID: {Config.GOOGLE_SHEET_ID[:20]}...")

    # 4. Настройка логирования
    logger = setup_logger("test_sheets", Config.LOG_PATH)

    # 5. Подключение к БД
    print_info("Подключение к базе данных...")

    try:
        db = Database(Config.DB_PATH, logger)
        db.init_db()
        print_success(f"База данных: {Config.DB_PATH}")
    except Exception as e:
        print_error(f"Ошибка подключения к БД: {e}")
        return False

    # 6. Проверка наличия постов
    post_count = db.get_post_count()
    print_info(f"Постов в базе данных: {Fore.YELLOW}{post_count}{Style.RESET_ALL}")

    if post_count == 0:
        print_warning("База данных пуста!")
        print_info("Сначала соберите данные через test_collector.py")
        db.close()
        return False

    # 7. Создание репортера
    print_info("Инициализация Google Sheets Reporter...")

    try:
        reporter = GoogleSheetsReporter(Config, db, logger)
        print_success("Репортер инициализирован")
    except Exception as e:
        print_error(f"Ошибка инициализации репортера: {e}")
        db.close()
        return False

    # 8. Генерация отчёта
    print_header("ГЕНЕРАЦИЯ ОТЧЁТА")
    print_info("Создание отчёта в Google Sheets (это может занять время)...")

    start_time = time.time()

    try:
        url = reporter.generate_report()
        elapsed = time.time() - start_time

        if url:
            print_success(f"Отчёт создан успешно! ({elapsed:.2f} сек)")
            print()
            print(f"{Fore.GREEN}{Style.BRIGHT}{'=' * 70}")
            print(f"ОТЧЁТ ГОТОВ!")
            print(f"{'=' * 70}{Style.RESET_ALL}")
            print()
            print(f"Ссылка на таблицу:")
            print(f"{Fore.CYAN}{Style.BRIGHT}{url}{Style.RESET_ALL}")
            print()
            print(f"Листы в отчёте:")
            print(f"   1. {Fore.MAGENTA}Сводка{Style.RESET_ALL} - общая статистика")
            print(f"   2. {Fore.MAGENTA}Все посты{Style.RESET_ALL} - детальная таблица ({post_count} постов)")
            print(f"   3. {Fore.MAGENTA}ТОП-10{Style.RESET_ALL} - топ постов по разным метрикам")
            print(f"   4. {Fore.MAGENTA}Динамика{Style.RESET_ALL} - ежедневная статистика")
            print()

        else:
            print_error("Не удалось создать отчёт")
            db.close()
            return False

    except FileNotFoundError as e:
        print_error(f"Файл не найден: {e}")
        db.close()
        return False

    except Exception as e:
        elapsed = time.time() - start_time
        print_error(f"Ошибка при генерации отчёта ({elapsed:.2f} сек)")

        # Детальная обработка ошибок Google API
        error_message = str(e).lower()

        if 'permission' in error_message or 'forbidden' in error_message:
            print_info("Проблема с доступом к таблице:")
            print("   1. Откройте таблицу в Google Sheets")
            print("   2. Нажмите 'Настройки доступа'")
            print("   3. Добавьте email из credentials.json с правами 'Редактор'")

        elif 'quota' in error_message or 'rate limit' in error_message:
            print_info("Превышена квота Google API:")
            print("   Подождите несколько минут и попробуйте снова")

        elif 'spreadsheet not found' in error_message:
            print_info("Таблица не найдена:")
            print("   Проверьте правильность GOOGLE_SHEET_ID в .env")

        else:
            import traceback
            print(f"\n{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")

        db.close()
        return False

    # 9. Закрытие БД
    db.close()
    return True


def main() -> None:
    """Основная функция тестирования."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║        ТЕСТИРОВАНИЕ GOOGLE SHEETS - МЕДИАСТАНЦИЯ СНЕЖИНСК         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")

    total_start = time.time()

    # Запуск теста
    success = test_google_sheets()

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
