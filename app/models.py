import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager


class TaskDB:
    def __init__(self, db_path='/data/tasks.db'):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self):
        with self.get_conn() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    номер_тсд TEXT NOT NULL DEFAULT '',
                    название TEXT NOT NULL DEFAULT '',
                    исполнитель TEXT NOT NULL DEFAULT '',
                    дата_выполнения TEXT NOT NULL DEFAULT '',
                    флаг INTEGER NOT NULL DEFAULT 1,
                    отправлено INTEGER NOT NULL DEFAULT 0,
                    повтор_тип TEXT DEFAULT 'none',
                    повтор_интервал INTEGER DEFAULT 1,
                    повтор_до TEXT DEFAULT '',
                    родитель_id INTEGER DEFAULT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                )
            ''')

            # Миграция: добавляем новые колонки если их нет
            self._migrate_add_recurring_fields(conn)
            self._migrate_add_new_fields(conn)

    def _migrate_add_recurring_fields(self, conn):
        """Добавляет поля для повторяющихся задач если их нет"""
        try:
            # Проверяем существование колонок
            cursor = conn.execute('PRAGMA table_info(tasks)')
            columns = [row[1] for row in cursor.fetchall()]

            if 'повтор_тип' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN повтор_тип TEXT DEFAULT "none"')
            if 'повтор_интервал' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN повтор_интервал INTEGER DEFAULT 1')
            if 'повтор_до' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN повтор_до TEXT DEFAULT ""')
            if 'родитель_id' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN родитель_id INTEGER DEFAULT NULL')
        except Exception as e:
            print(f'[DB] Migration warning: {e}')

    def _migrate_add_new_fields(self, conn):
        """Добавляет новые поля: срок представления, примечания, файлы"""
        try:
            cursor = conn.execute('PRAGMA table_info(tasks)')
            columns = [row[1] for row in cursor.fetchall()]

            if 'срок_представления' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN срок_представления TEXT DEFAULT ""')
            if 'примечания' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN примечания TEXT DEFAULT ""')
            if 'файлы' not in columns:
                conn.execute('ALTER TABLE tasks ADD COLUMN файлы TEXT DEFAULT "[]"')
        except Exception as e:
            print(f'[DB] Migration warning: {e}')

    def _format_task(self, task):
        """Преобразует задачу из БД в формат API с переименованными полями"""
        if not task:
            return None
        # Переименовываем поля для фронтенда
        formatted = {
            'id': task['id'],
            'номер_тсд': task['номер_тсд'],
            'название': task['название'],
            'кому_представляется': task['исполнитель'],
            'срок_представления': task.get('срок_представления', ''),
            'примечания': task.get('примечания', ''),
            'дата_доклада': task['дата_выполнения'],
            'флаг': task['флаг'],
            'отправлено': task['отправлено'],
            'повтор_тип': task.get('повтор_тип', 'none'),
            'повтор_интервал': task.get('повтор_интервал', 1),
            'повтор_до': task.get('повтор_до', ''),
            'родитель_id': task.get('родитель_id'),
            'файлы': json.loads(task.get('файлы', '[]')) if isinstance(task.get('файлы'), str) else task.get('файлы', [])
        }
        return formatted

    def _unformat_task(self, data):
        """Преобразует данные из API в формат БД"""
        return {
            'номер_тсд': data.get('номер_тсд', ''),
            'название': data.get('название', ''),
            'исполнитель': data.get('кому_представляется', ''),
            'дата_выполнения': data.get('дата_доклада', ''),
            'срок_представления': data.get('срок_представления', ''),
            'примечания': data.get('примечания', ''),
            'флаг': data.get('флаг', 1),
            'повтор_тип': data.get('повтор_тип', 'none'),
            'повтор_интервал': data.get('повтор_интервал', 1),
            'повтор_до': data.get('повтор_до', ''),
            'родитель_id': data.get('родитель_id'),
            'файлы': json.dumps(data.get('файлы', [])) if isinstance(data.get('файлы'), list) else data.get('файлы', '[]')
        }

    def get_all(self):
        with self.get_conn() as conn:
            rows = conn.execute(
                '''SELECT id, номер_тсд, название, исполнитель, дата_выполнения, флаг, отправлено,
                   повтор_тип, повтор_интервал, повтор_до, родитель_id,
                   срок_представления, примечания, файлы FROM tasks ORDER BY дата_выполнения, id'''
            ).fetchall()
            return [self._format_task(dict(row)) for row in rows]

    def get_by_id(self, task_id):
        with self.get_conn() as conn:
            row = conn.execute(
                '''SELECT id, номер_тсд, название, исполнитель, дата_выполнения, флаг, отправлено,
                   повтор_тип, повтор_интервал, повтор_до, родитель_id,
                   срок_представления, примечания, файлы FROM tasks WHERE id = ?''',
                (task_id,)
            ).fetchone()
            return self._format_task(dict(row)) if row else None

    def create(self, data):
        # Преобразуем данные из API формата в формат БД
        db_data = self._unformat_task(data)

        with self.get_conn() as conn:
            cursor = conn.execute(
                '''INSERT INTO tasks (номер_тсд, название, исполнитель, дата_выполнения, флаг,
                   повтор_тип, повтор_интервал, повтор_до, родитель_id,
                   срок_представления, примечания, файлы)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    db_data.get('номер_тсд', ''),
                    db_data.get('название', ''),
                    db_data.get('исполнитель', ''),
                    db_data.get('дата_выполнения', ''),
                    db_data.get('флаг', 1),
                    db_data.get('повтор_тип', 'none'),
                    db_data.get('повтор_интервал', 1),
                    db_data.get('повтор_до', ''),
                    db_data.get('родитель_id', None),
                    db_data.get('срок_представления', ''),
                    db_data.get('примечания', ''),
                    db_data.get('файлы', '[]'),
                )
            )
            return self.get_by_id_conn(conn, cursor.lastrowid)

    def get_by_id_conn(self, conn, task_id):
        row = conn.execute(
            '''SELECT id, номер_тсд, название, исполнитель, дата_выполнения, флаг, отправлено,
               повтор_тип, повтор_интервал, повтор_до, родитель_id,
               срок_представления, примечания, файлы FROM tasks WHERE id = ?''',
            (task_id,)
        ).fetchone()
        return self._format_task(dict(row)) if row else None

    def update(self, task_id, data):
        # Преобразуем данные из API формата в формат БД
        db_data = self._unformat_task(data)

        fields = []
        values = []
        allowed = ['номер_тсд', 'название', 'исполнитель', 'дата_выполнения', 'флаг',
                   'повтор_тип', 'повтор_интервал', 'повтор_до', 'родитель_id',
                   'срок_представления', 'примечания', 'файлы']
        for field in allowed:
            if field in db_data and db_data[field] is not None:
                fields.append(f'{field} = ?')
                values.append(db_data[field])
        if not fields:
            return self.get_by_id(task_id)
        values.append(task_id)
        with self.get_conn() as conn:
            conn.execute(
                f'UPDATE tasks SET {", ".join(fields)} WHERE id = ?',
                values
            )
            return self.get_by_id_conn(conn, task_id)

    def delete(self, task_id):
        with self.get_conn() as conn:
            conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

    def delete_all(self):
        with self.get_conn() as conn:
            conn.execute('DELETE FROM tasks')

    def delete_with_children(self, task_id):
        """Удаляет задачу и все её дочерние повторы"""
        with self.get_conn() as conn:
            # Удаляем дочерние задачи
            result = conn.execute('DELETE FROM tasks WHERE родитель_id = ?', (task_id,))
            children_count = result.rowcount

            # Удаляем саму задачу
            conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))

            return children_count + 1

    def update_recurrence(self, task_id, new_data):
        """Обновляет задачу и пересоздаёт все повторы"""
        # Удаляем старые дочерние задачи
        with self.get_conn() as conn:
            conn.execute('DELETE FROM tasks WHERE родитель_id = ?', (task_id,))

        # Обновляем родительскую задачу (отдельная транзакция)
        self.update(task_id, new_data)

        # Если новый тип повтора - создаём новые дочерние
        if new_data.get('повтор_тип', 'none') != 'none':
            # Получаем обновлённую задачу
            parent_task = self.get_by_id(task_id)
            if not parent_task:
                return []

            # Создаём новые повторы
            return self._create_child_tasks(parent_task)
        else:
            return [self.get_by_id(task_id)]

    def _create_child_tasks(self, parent_task):
        """Создаёт дочерние задачи на основе родительской"""
        from dateutil import rrule
        from dateutil.parser import parse

        repeat_type = parent_task.get('повтор_тип', 'none')
        if repeat_type == 'none':
            return [parent_task]

        start_date = parse(parent_task['дата_доклада'])
        # Для упрощения создаём повторы на год вперёд
        end_date = parse(parent_task.get('повтор_до', '')) if parent_task.get('повтор_до') else (start_date + timedelta(days=365))
        interval = int(parent_task.get('повтор_интервал', 1))

        freq_map = {
            'daily': rrule.DAILY,
            'weekly': rrule.WEEKLY,
            'monthly': rrule.MONTHLY,
            'yearly': rrule.YEARLY
        }

        rule = rrule.rrule(
            freq_map.get(repeat_type, rrule.DAILY),
            dtstart=start_date,
            until=end_date,
            interval=interval
        )

        created_tasks = [parent_task]

        # Пропускаем первую дату (это родитель), создаём остальные
        for date in list(rule)[1:]:
            task_copy = parent_task.copy()
            task_copy['дата_доклада'] = date.strftime('%Y-%m-%d')
            task_copy['отправлено'] = 0
            task_copy['родитель_id'] = parent_task['id']

            # Удаляем id чтобы создать новую запись
            if 'id' in task_copy:
                del task_copy['id']

            created_tasks.append(self.create(task_copy))

        return created_tasks

    def get_tasks_for_notification(self):
        """Получает задачи для уведомлений: сегодня и завтра"""
        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        with self.get_conn() as conn:
            rows = conn.execute(
                '''SELECT id, номер_тсд, название, исполнитель, дата_выполнения, флаг, отправлено,
                   срок_представления, примечания, файлы, повтор_тип
                   FROM tasks
                   WHERE дата_выполнения IN (?, ?) AND флаг = 1 AND отправлено = 0''',
                (today, tomorrow)
            ).fetchall()

            result = []
            for row in rows:
                task = self._format_task(dict(row))
                # Добавляем метку "завтра" или "сегодня"
                if task['дата_доклада'] == tomorrow:
                    task['notification_label'] = 'завтра'
                else:
                    task['notification_label'] = 'сегодня'
                result.append(task)

            return result

    def mark_sent(self, task_ids):
        if not task_ids:
            return
        placeholders = ','.join('?' for _ in task_ids)
        with self.get_conn() as conn:
            conn.execute(
                f'UPDATE tasks SET отправлено = 1 WHERE id IN ({placeholders})',
                task_ids
            )

    def create_recurring_tasks(self, task_data):
        """Создает серию повторяющихся задач"""
        from dateutil import rrule
        from dateutil.parser import parse

        repeat_type = task_data.get('повтор_тип', 'none')
        if repeat_type == 'none':
            return [self.create(task_data)]

        # Используем новое имя поля дата_доклада, но проверяем оба варианта для совместимости
        date_field = task_data.get('дата_доклада') or task_data.get('дата_выполнения')
        if not date_field:
            return [self.create(task_data)]

        start_date = parse(date_field)
        end_date = parse(task_data.get('повтор_до', '')) if task_data.get('повтор_до') else None
        interval = int(task_data.get('повтор_интервал', 1))

        # Определяем частоту повторения
        freq_map = {
            'daily': rrule.DAILY,
            'weekly': rrule.WEEKLY,
            'monthly': rrule.MONTHLY,
            'yearly': rrule.YEARLY
        }

        if repeat_type not in freq_map:
            return [self.create(task_data)]

        # Генерируем даты
        rule = rrule.rrule(
            freq_map[repeat_type],
            dtstart=start_date,
            until=end_date,
            interval=interval,
            count=100 if not end_date else None  # Макс 100 задач если нет конечной даты
        )

        created_tasks = []
        parent_id = None

        for i, date in enumerate(rule):
            task_copy = task_data.copy()
            task_copy['дата_доклада'] = date.strftime('%Y-%m-%d')
            task_copy['отправлено'] = 0

            if i == 0:
                # Первая задача - родитель
                task_copy['родитель_id'] = None
                created_task = self.create(task_copy)
                parent_id = created_task['id']
                created_tasks.append(created_task)
            else:
                # Последующие задачи - дети
                task_copy['родитель_id'] = parent_id
                created_tasks.append(self.create(task_copy))

        return created_tasks

    def add_file(self, task_id, filename):
        """Добавляет файл к задаче"""
        task = self.get_by_id(task_id)
        if not task:
            return None

        files = task.get('файлы', [])
        if filename not in files:
            files.append(filename)

        with self.get_conn() as conn:
            conn.execute(
                'UPDATE tasks SET файлы = ? WHERE id = ?',
                (json.dumps(files), task_id)
            )
        return self.get_by_id(task_id)

    def remove_file(self, task_id, filename):
        """Удаляет файл из задачи"""
        task = self.get_by_id(task_id)
        if not task:
            return None

        files = task.get('файлы', [])
        if filename in files:
            files.remove(filename)

        with self.get_conn() as conn:
            conn.execute(
                'UPDATE tasks SET файлы = ? WHERE id = ?',
                (json.dumps(files), task_id)
            )
        return self.get_by_id(task_id)
