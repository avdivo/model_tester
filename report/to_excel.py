from openpyxl import load_workbook
from datetime import datetime
from pathlib import Path

def append_record_to_excel(
    model: str,
    test: str,
    median_latency,
    percent_correct,
    score: float,
    price: float,
    file_path: str = "report/report.xlsx"
) -> None:
    """
    Добавляет запись в конец существующей Excel-таблицы, не изменяя стили и формат столбцов.

    :param model: Название модели
    :param test: Название теста или его идентификатор
    :param median_latency: Медианная задержка
    :param percent_correct: Процент правильных ответов
    :param score: Числовой балл
    :param price: Цена за тест
    :param file_path: Путь к XLSX-файлу
    """
    file_path = Path(file_path)  # Загружаем существующий файл
    wb = load_workbook(file_path)
    ws = wb.active  # Если нужна конкретная вкладка — wb["ИмяЛиста"]

    # Формируем запись: дата/время, модель, тест, балл
    ws.append([
        datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        model,
        test,
        median_latency,
        percent_correct,
        score,
        price
    ])

    # Сохраняем файл
    wb.save(file_path)
