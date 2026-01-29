#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для импорта задач из CSV файла
"""
import csv
import sys
from datetime import datetime
from app.models import TaskDB
import config

def parse_date(date_str):
    """Парсит дату из различных форматов"""
    if not date_str or date_str.strip() == '':
        return None

    date_str = date_str.strip()

    # Формат DD.MM.YYYY
    if '.' in date_str:
        parts = date_str.split('.')
        if len(parts) == 3:
            try:
                day, month, year = parts
                return f"{year}-{int(month):02d}-{int(day):02d}"
            except:
                return None
        # Формат DD.MM (без года)
        elif len(parts) == 2:
            day, month = parts
            year = datetime.now().year
            try:
                return f"{year}-{int(month):02d}-{int(day):02d}"
            except:
                return None

    # Формат YYYY-MM-DD
    if '-' in date_str and len(date_str.split('-')) == 3:
        return date_str

    return None

def import_csv(csv_path):
    """Импортирует задачи из CSV файла"""
    db = TaskDB(config.DATABASE_PATH)

    imported = 0
    skipped = 0
    errors = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        # Читаем CSV, разделитель - точка с запятой
        reader = csv.reader(f, delimiter=';')

        # Пропускаем заголовок если есть
        first_row = next(reader, None)
        if not first_row:
            print("❌ Файл пуст")
            return

        # Обрабатываем строки
        for row_num, row in enumerate(reader, start=2):
            # Пропускаем пустые строки
            if not row or all(cell.strip() == '' for cell in row):
                continue

            try:
                # Парсим данные из CSV
                # Структура: номер_тсд;название;кому_представляется;срок_представления;примечания;дата_доклада;флаг;???
                номер_тсд = row[0].strip() if len(row) > 0 else ''
                название = row[1].strip() if len(row) > 1 else ''
                кому_представляется = row[2].strip() if len(row) > 2 else ''
                срок_представления = row[3].strip() if len(row) > 3 else ''
                примечания = row[4].strip() if len(row) > 4 else ''
                дата_доклада_raw = row[5].strip() if len(row) > 5 else ''
                флаг = int(row[6].strip()) if len(row) > 6 and row[6].strip().isdigit() else 1

                # Парсим дату
                дата_доклада = parse_date(дата_доклада_raw)

                # Если нет названия или даты - пропускаем
                if not название or not дата_доклада:
                    skipped += 1
                    continue

                # Создаем задачу
                task_data = {
                    'номер_тсд': номер_тсд,
                    'название': название,
                    'кому_представляется': кому_представляется,
                    'срок_представления': срок_представления,
                    'примечания': примечания,
                    'дата_доклада': дата_доклада,
                    'флаг': флаг,
                    'повтор_тип': 'none',
                    'файлы': []
                }

                db.create(task_data)
                imported += 1

                if imported % 10 == 0:
                    print(f"Импортировано {imported} задач...")

            except Exception as e:
                error_msg = f"Строка {row_num}: {str(e)}"
                errors.append(error_msg)
                print(f"⚠️  {error_msg}")

    print("\n" + "="*50)
    print(f"✅ Импорт завершен!")
    print(f"   Импортировано: {imported}")
    print(f"   Пропущено: {skipped}")
    if errors:
        print(f"   Ошибок: {len(errors)}")
        print("\nОшибки:")
        for err in errors[:10]:  # Показываем первые 10 ошибок
            print(f"   - {err}")
    print("="*50)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python import_csv.py <путь_к_csv_файлу>")
        sys.exit(1)

    csv_path = sys.argv[1]
    import_csv(csv_path)
