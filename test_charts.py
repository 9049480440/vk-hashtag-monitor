#!/usr/bin/env python3
"""
Тестовый скрипт для проверки генерации графиков.

Проверяет создание PNG графиков на основе данных из БД.
"""

import sys
import time
import os
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
    from reports.charts import ChartBuilder
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


def format_file_size(size_bytes: int) -> str:
    """
    Форматирует размер файла.

    Args:
        size_bytes: Размер в байтах

    Returns:
        str: Отформатированный размер
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def test_charts() -> bool:
    """
    Тестирует генерацию графиков.

    Returns:
        bool: True если тест успешен
    """
    print_header("ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ ГРАФИКОВ")

    # 1. Проверка конфигурации
    print_info("Загрузка конфигурации...")

    try:
        Config.load_from_env()
        print_success("Конфигурация загружена")
    except Exception as e:
        print_error(f"Ошибка загрузки конфигурации: {e}")
        return False

    # 2. Настройка логирования
    logger = setup_logger("test_charts", Config.LOG_PATH)

    # 3. Подключение к БД
    print_info("Подключение к базе данных...")

    try:
        db = Database(Config.DB_PATH, logger)
        db.init_db()
        print_success(f"База данных: {Config.DB_PATH}")
    except Exception as e:
        print_error(f"Ошибка подключения к БД: {e}")
        return False

    # 4. Проверка наличия данных
    post_count = db.get_post_count()
    print_info(f"Постов в базе данных: {Fore.YELLOW}{post_count}{Style.RESET_ALL}")

    if post_count == 0:
        print_warning("База данных пуста!")
        print_info("Сначала соберите данные через test_collector.py")
        db.close()
        return False

    # Получение данных для проверки
    all_posts = db.get_all_posts()
    unique_dates = set(
        post.get('date_published', 0) for post in all_posts
        if post.get('date_published', 0) > 0
    )

    if len(unique_dates) < 1:
        print_warning(f"Недостаточно данных для графиков!")
        print_info(f"Найдено {len(unique_dates)} уникальных дат (минимум 1)")
        print_info("Соберите больше данных")
        db.close()
        return False

    print_success(f"Данных достаточно: {len(unique_dates)} уникальных дат")

    # 5. Создание строителя графиков
    print_info("Инициализация Chart Builder...")

    try:
        builder = ChartBuilder(
            database=db,
            logger=logger,
            output_dir='temp_charts'
        )
        print_success("Chart Builder инициализирован")
    except Exception as e:
        print_error(f"Ошибка инициализации: {e}")
        db.close()
        return False

    # 6. Генерация графиков
    print_header("ГЕНЕРАЦИЯ ГРАФИКОВ")
    print_info("Создание графиков (это может занять время)...")

    start_time = time.time()

    try:
        chart_files = builder.build_all_charts()
        elapsed = time.time() - start_time

        if chart_files:
            print_success(f"Графики созданы успешно! ({elapsed:.2f} сек)")
            print()
            print(f"{Fore.GREEN}{Style.BRIGHT}{'=' * 70}")
            print(f"ГРАФИКИ ГОТОВЫ!")
            print(f"{'=' * 70}{Style.RESET_ALL}")
            print()

            # Информация о файлах
            print(f"Создано графиков: {Fore.YELLOW}{len(chart_files)}{Style.RESET_ALL}")
            print()

            for i, file_path in enumerate(chart_files, 1):
                path = Path(file_path)
                if path.exists():
                    file_size = path.stat().st_size
                    file_name = path.name

                    # Определение типа графика
                    if 'publications' in file_name:
                        chart_type = "Динамика публикаций"
                    elif 'reach' in file_name:
                        chart_type = "Рост охвата"
                    elif 'engagement' in file_name:
                        chart_type = "Вовлечённость аудитории"
                    else:
                        chart_type = "График"

                    print(f"{Fore.MAGENTA}График {i}:{Style.RESET_ALL} {chart_type}")
                    print(f"   Файл: {file_path}")
                    print(f"   Размер: {format_file_size(file_size)}")
                    print()

            # Попытка открыть графики
            print_info("Хотите открыть графики в просмотрщике? (y/n): ", end='')
            try:
                answer = input().strip().lower()
                if answer == 'y':
                    for file_path in chart_files:
                        try:
                            if sys.platform == 'darwin':  # macOS
                                os.system(f'open "{file_path}"')
                            elif sys.platform == 'win32':  # Windows
                                os.system(f'start "" "{file_path}"')
                            else:  # Linux
                                os.system(f'xdg-open "{file_path}"')
                        except Exception as e:
                            print_warning(f"Не удалось открыть {file_path}: {e}")
            except EOFError:
                pass

            print()

            # Вопрос об удалении
            print_info("Удалить временные файлы графиков? (y/n): ", end='')
            try:
                answer = input().strip().lower()
                if answer == 'y':
                    builder.cleanup_charts(chart_files)
                    print_success("Временные файлы удалены")
                else:
                    print_info(f"Файлы сохранены в папке: {Fore.CYAN}temp_charts/{Style.RESET_ALL}")
            except EOFError:
                print_info(f"Файлы сохранены в папке: {Fore.CYAN}temp_charts/{Style.RESET_ALL}")

        else:
            print_error("Не удалось создать графики")
            db.close()
            return False

    except Exception as e:
        elapsed = time.time() - start_time
        print_error(f"Ошибка при генерации графиков ({elapsed:.2f} сек)")
        import traceback
        print(f"\n{Fore.RED}{traceback.format_exc()}{Style.RESET_ALL}")
        db.close()
        return False

    # 7. Закрытие БД
    db.close()
    return True


def main() -> None:
    """Основная функция тестирования."""
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║       ТЕСТИРОВАНИЕ ГРАФИКОВ - МЕДИАСТАНЦИЯ СНЕЖИНСК               ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")

    total_start = time.time()

    # Запуск теста
    success = test_charts()

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
