import requests
import config


def send_telegram_message(text):
    """Отправляет сообщение во все указанные чаты"""
    token = config.TELEGRAM_BOT_TOKEN
    chat_ids = config.TELEGRAM_CHAT_IDS

    if not token or not chat_ids:
        print('[BOT] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_IDS not set, skipping')
        return False

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    success_count = 0

    for chat_id in chat_ids:
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            print(f'[BOT] Message sent to chat {chat_id}')
            success_count += 1
        except requests.RequestException as e:
            print(f'[BOT] Failed to send message to chat {chat_id}: {e}')

    return success_count > 0


def format_tasks_message(tasks):
    """Форматирует красивое сообщение с задачами"""
    if not tasks:
        return None

    # Группируем по дате (сегодня/завтра)
    today_tasks = [t for t in tasks if t.get('notification_label') == 'сегодня']
    tomorrow_tasks = [t for t in tasks if t.get('notification_label') == 'завтра']

    lines = []

    # Задачи на сегодня
    if today_tasks:
        lines.append('🔔 <b>Задачи на СЕГОДНЯ:</b>')
        lines.append('')
        for t in today_tasks:
            flag = '✅' if t['флаг'] else '❌'
            повтор = ''
            if t.get('повтор_тип') and t['повтор_тип'] != 'none':
                повтор_map = {'daily': '🔄 ежедневно', 'weekly': '🔄 еженедельно',
                             'monthly': '🔄 ежемесячно', 'yearly': '🔄 ежегодно'}
                повтор = f"\n   {повтор_map.get(t['повтор_тип'], '🔄 повтор')}"

            срок = f"\n   📝 Срок: {t['срок_представления']}" if t.get('срок_представления') else ''
            примечания = f"\n   💬 {t['примечания']}" if t.get('примечания') else ''
            файлы = f"\n   📎 Файлов: {len(t.get('файлы', []))}" if t.get('файлы') else ''

            lines.append(
                f"{flag} <b>№{t['номер_тсд']}</b> — {t['название']}\n"
                f"   👤 Кому: {t['кому_представляется']}\n"
                f"   📅 Дата доклада: {t['дата_доклада']}"
                f"{срок}{примечания}{файлы}{повтор}"
            )
            lines.append('')

    # Задачи на завтра
    if tomorrow_tasks:
        if today_tasks:
            lines.append('━━━━━━━━━━━━━━━━━━━')
            lines.append('')
        lines.append('⏰ <b>Напоминание: задачи на ЗАВТРА:</b>')
        lines.append('')
        for t in tomorrow_tasks:
            flag = '✅' if t['флаг'] else '❌'
            повтор = ''
            if t.get('повтор_тип') and t['повтор_тип'] != 'none':
                повтор_map = {'daily': '🔄 ежедневно', 'weekly': '🔄 еженедельно',
                             'monthly': '🔄 ежемесячно', 'yearly': '🔄 ежегодно'}
                повтор = f"\n   {повтор_map.get(t['повтор_тип'], '🔄 повтор')}"

            срок = f"\n   📝 Срок: {t['срок_представления']}" if t.get('срок_представления') else ''
            примечания = f"\n   💬 {t['примечания']}" if t.get('примечания') else ''
            файлы = f"\n   📎 Файлов: {len(t.get('файлы', []))}" if t.get('файлы') else ''

            lines.append(
                f"{flag} <b>№{t['номер_тсд']}</b> — {t['название']}\n"
                f"   👤 Кому: {t['кому_представляется']}\n"
                f"   📅 Дата доклада: {t['дата_доклада']}"
                f"{срок}{примечания}{файлы}{повтор}"
            )
            lines.append('')

    return '\n'.join(lines)


def notify_today_tasks(db):
    """Отправляет уведомления о задачах на сегодня и завтра"""
    tasks = db.get_tasks_for_notification()
    if not tasks:
        print('[BOT] No tasks for notification')
        return

    message = format_tasks_message(tasks)
    if message and send_telegram_message(message):
        # Отмечаем как отправленные только задачи на сегодня
        today_task_ids = [t['id'] for t in tasks if t.get('notification_label') == 'сегодня']
        if today_task_ids:
            db.mark_sent(today_task_ids)
            print(f'[BOT] Marked {len(today_task_ids)} tasks as sent')
        print(f'[BOT] Sent notification for {len(tasks)} tasks (today + tomorrow)')
