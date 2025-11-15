"""
Модуль генерации отчётов в различных форматах.

Предоставляет базовый класс BaseReporter и реализации
для различных форматов (Google Sheets, PDF, Excel и т.д.).
"""

from reports.google_sheets.sheets_reporter import GoogleSheetsReporter

__all__ = ['GoogleSheetsReporter']
