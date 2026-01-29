1) будет 1 страничный сайт с интегрированной таблицей, которую сможет редактировать любой пользователь
2) я запущу контейнер с ботом и этим сайтом, и он будет ежедневно проверять сайт и слать в tg сообщения
как такой вариант?

Отличный вариант! Это более автономное и гибкое решение. Давай продумаем архитектуру:[^1][^2][^3]

## Рекомендуемый стек

### Backend

**Flask** (легковесный, знаком тебе по опыту):[^4]

- REST API для CRUD операций с задачами
- Scheduler для периодических проверок
- Telegram bot интеграция


### Frontend

**Tabulator.js** - мощная библиотека для редактируемых таблиц:[^1]

- Inline редактирование ячеек
- Фильтрация и сортировка
- Экспорт в CSV/JSON
- Работает из коробки


### Хранилище

**SQLite** - идеально для такого кейса:[^2]

- Легкий, без отдельного сервера
- Поддержка транзакций
- Простой backup (один файл)


### Планировщик

**APScheduler** для ежедневных проверок

## Архитектура решения

```
┌─────────────────────────────────────┐
│   Docker Container                  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Flask App (port 5000)       │  │
│  │  ├─ Web UI (HTML/JS)         │  │
│  │  ├─ REST API                 │  │
│  │  └─ Static files             │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Telegram Bot Service        │  │
│  │  ├─ APScheduler (cron)       │  │
│  │  ├─ Check tasks daily        │  │
│  │  └─ Send messages            │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  SQLite Database             │  │
│  │  /data/tasks.db              │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
         │
         └─ Volume mount: ./data:/data
```


## Структура проекта

```
telegram-tasks-manager/
├── app/
│   ├── __init__.py
│   ├── models.py          # SQLite models
│   ├── routes.py          # Flask routes (API)
│   ├── bot.py             # Telegram bot logic
│   ├── scheduler.py       # APScheduler tasks
│   └── templates/
│       └── index.html     # Одностраничное приложение
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js         # Tabulator + AJAX
├── data/                  # Volume mount
│   └── tasks.db
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── config.py
```


## Ключевые компоненты

### 1. База данных (models.py)

```python
import sqlite3
from datetime import datetime

class TaskDB:
    def __init__(self, db_path='/data/tasks.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                номер_тсд TEXT,
                название TEXT,
                исполнитель TEXT,
                дата_выполнения TEXT,
                флаг INTEGER DEFAULT 1,
                отправлено INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
```


### 2. Flask API (routes.py)

```python
from flask import Flask, jsonify, request

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    # Получить все задачи
    
@app.route('/api/tasks', methods=['POST'])
def create_task():
    # Создать задачу
    
@app.route('/api/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    # Обновить задачу
```


### 3. Telegram Bot (bot.py)

```python
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

def check_and_send_notifications():
    # Проверка задач с флагом=1 и сегодняшней датой
    # Отправка в Telegram
    # Пометка отправлено=1
    
scheduler = BackgroundScheduler()
scheduler.add_job(
    check_and_send_notifications, 
    'cron', 
    hour=9, 
    minute=0
)
```


### 4. Frontend (index.html + app.js)

```javascript
// Tabulator для редактируемой таблицы
var table = new Tabulator("#tasks-table", {
    ajaxURL: "/api/tasks",
    layout: "fitColumns",
    columns: [
        {title: "№ ТСД", field: "номер_тсд", editor: "input"},
        {title: "Название", field: "название", editor: "input"},
        {title: "Исполнитель", field: "исполнитель", editor: "input"},
        {title: "Дата", field: "дата_выполнения", editor: "date"},
        {title: "Флаг", field: "флаг", editor: "tickCross"}
    ],
    cellEdited: function(cell) {
        // Автосохранение при изменении
        updateTask(cell.getRow().getData());
    }
});
```


## Docker setup

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```


### docker-compose.yml

```yaml
version: '3.8'
services:
  telegram-tasks:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/data
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
    restart: unless-stopped
```


