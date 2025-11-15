"""
Клиент для работы с Google Sheets API.

Модуль инкапсулирует все операции с Google Sheets:
подключение, запись данных, форматирование.
"""

import logging
from typing import Optional, List, Any
from pathlib import Path

import gspread
from oauth2client.service_account import ServiceAccountCredentials


class GoogleSheetsClient:
    """
    Клиент для работы с Google Sheets API.

    Отвечает ТОЛЬКО за взаимодействие с Google Sheets API.
    НЕ знает про структуру отчётов или бизнес-логику.
    """

    def __init__(
        self,
        credentials_file: str,
        sheet_id: str,
        logger: logging.Logger
    ):
        """
        Инициализирует клиент Google Sheets.

        Args:
            credentials_file: Путь к файлу с учётными данными Google API
            sheet_id: ID таблицы Google Sheets
            logger: Logger для логирования операций
        """
        self.credentials_file = Path(credentials_file)
        self.sheet_id = sheet_id
        self.logger = logger
        self.client: Optional[gspread.Client] = None
        self.spreadsheet: Optional[gspread.Spreadsheet] = None

    def connect(self) -> bool:
        """
        Подключается к Google Sheets через gspread.

        Returns:
            bool: True если подключение успешно

        Raises:
            FileNotFoundError: Если файл credentials не найден
            Exception: При ошибках подключения к Google API
        """
        self.logger.info("Подключение к Google Sheets API")

        try:
            # Проверка наличия файла credentials
            if not self.credentials_file.exists():
                raise FileNotFoundError(
                    f"Файл credentials не найден: {self.credentials_file}"
                )

            # Настройка аутентификации
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                str(self.credentials_file),
                scope
            )

            # Создание клиента
            self.client = gspread.authorize(credentials)

            # Открытие таблицы
            self.spreadsheet = self.client.open_by_key(self.sheet_id)

            self.logger.info(
                f"Подключение успешно: {self.spreadsheet.title}"
            )
            return True

        except FileNotFoundError as e:
            self.logger.error(f"Файл credentials не найден: {e}")
            raise
        except gspread.exceptions.SpreadsheetNotFound:
            self.logger.error(f"Таблица с ID {self.sheet_id} не найдена")
            raise
        except Exception as e:
            self.logger.error(f"Ошибка подключения к Google Sheets: {e}")
            raise

    def create_or_get_worksheet(self, title: str) -> gspread.Worksheet:
        """
        Создаёт новый лист или получает существующий.

        Args:
            title: Название листа

        Returns:
            gspread.Worksheet: Объект листа

        Raises:
            ValueError: Если нет подключения к таблице
        """
        if not self.spreadsheet:
            raise ValueError("Нет подключения к таблице. Вызовите connect() сначала")

        try:
            # Попытка получить существующий лист
            worksheet = self.spreadsheet.worksheet(title)
            self.logger.debug(f"Лист '{title}' уже существует")
            return worksheet

        except gspread.exceptions.WorksheetNotFound:
            # Создание нового листа
            worksheet = self.spreadsheet.add_worksheet(
                title=title,
                rows=1000,
                cols=20
            )
            self.logger.info(f"Создан новый лист '{title}'")
            return worksheet

    def clear_worksheet(self, worksheet: gspread.Worksheet) -> None:
        """
        Очищает содержимое листа.

        Args:
            worksheet: Объект листа для очистки
        """
        try:
            worksheet.clear()
            self.logger.debug(f"Лист '{worksheet.title}' очищен")

        except Exception as e:
            self.logger.error(f"Ошибка очистки листа: {e}")
            raise

    def write_data(
        self,
        worksheet: gspread.Worksheet,
        data: List[List[Any]],
        start_cell: str = 'A1'
    ) -> None:
        """
        Записывает данные на лист.

        Args:
            worksheet: Объект листа
            data: 2D массив данных для записи
            start_cell: Начальная ячейка (по умолчанию 'A1')

        Example:
            >>> data = [['Name', 'Age'], ['Alice', 30], ['Bob', 25]]
            >>> client.write_data(worksheet, data, 'A1')
        """
        try:
            if not data:
                self.logger.warning("Нет данных для записи")
                return

            worksheet.update(start_cell, data)
            self.logger.debug(
                f"Записано {len(data)} строк на лист '{worksheet.title}'"
            )

        except Exception as e:
            self.logger.error(f"Ошибка записи данных: {e}")
            raise

    def format_header(
        self,
        worksheet: gspread.Worksheet,
        row: int = 1
    ) -> None:
        """
        Форматирует заголовок (жирный текст, серый фон).

        Args:
            worksheet: Объект листа
            row: Номер строки заголовка (по умолчанию 1)
        """
        try:
            # Форматирование заголовка
            worksheet.format(f'{row}:{row}', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })

            self.logger.debug(f"Заголовок отформатирован (строка {row})")

        except Exception as e:
            self.logger.error(f"Ошибка форматирования заголовка: {e}")
            # Не критично, продолжаем

    def auto_resize_columns(self, worksheet: gspread.Worksheet) -> None:
        """
        Автоматически подбирает ширину колонок.

        Args:
            worksheet: Объект листа
        """
        try:
            # Получение количества колонок
            col_count = worksheet.col_count

            # Запрос на автоматическую ширину
            body = {
                'requests': [
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': worksheet.id,
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': col_count
                            }
                        }
                    }
                ]
            }

            self.spreadsheet.batch_update(body)
            self.logger.debug(f"Колонки листа '{worksheet.title}' изменены")

        except Exception as e:
            self.logger.error(f"Ошибка изменения ширины колонок: {e}")
            # Не критично, продолжаем

    def set_number_format(
        self,
        worksheet: gspread.Worksheet,
        range_name: str,
        format_type: str
    ) -> None:
        """
        Устанавливает формат чисел для диапазона ячеек.

        Args:
            worksheet: Объект листа
            range_name: Диапазон ячеек (например, 'B2:B100')
            format_type: Тип формата ('percent', 'number', 'date')

        Example:
            >>> client.set_number_format(worksheet, 'K2:K100', 'percent')
        """
        try:
            # Определение паттерна формата
            if format_type == 'percent':
                pattern = '0.00%'
            elif format_type == 'number':
                pattern = '#,##0'
            elif format_type == 'date':
                pattern = 'dd.mm.yyyy hh:mm'
            else:
                self.logger.warning(f"Неизвестный тип формата: {format_type}")
                return

            # Применение формата
            worksheet.format(range_name, {
                'numberFormat': {
                    'type': 'NUMBER',
                    'pattern': pattern
                }
            })

            self.logger.debug(
                f"Формат '{format_type}' применён к '{range_name}'"
            )

        except Exception as e:
            self.logger.error(f"Ошибка установки формата чисел: {e}")
            # Не критично, продолжаем

    def get_spreadsheet_url(self) -> Optional[str]:
        """
        Возвращает URL таблицы.

        Returns:
            Optional[str]: URL таблицы или None если нет подключения
        """
        if not self.spreadsheet:
            return None

        return self.spreadsheet.url
