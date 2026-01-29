from flask import Blueprint, jsonify, request, render_template, current_app, send_from_directory
from werkzeug.utils import secure_filename
import os
from app.bot import notify_today_tasks

UPLOAD_FOLDER = '/data/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = current_app.db.get_all()
    return jsonify(tasks)


@bp.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    task = current_app.db.create(data)
    return jsonify(task), 201


@bp.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = current_app.db.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)


@bp.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    task = current_app.db.update(task_id, data)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)


@bp.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    existing = current_app.db.get_by_id(task_id)
    if not existing:
        return jsonify({'error': 'Task not found'}), 404
    current_app.db.delete(task_id)
    return jsonify({'ok': True})


@bp.route('/api/tasks/<int:task_id>/with-children', methods=['DELETE'])
def delete_task_with_children(task_id):
    """Удаляет задачу и все её дочерние повторы"""
    existing = current_app.db.get_by_id(task_id)
    if not existing:
        return jsonify({'error': 'Task not found'}), 404

    deleted_count = current_app.db.delete_with_children(task_id)
    return jsonify({'ok': True, 'deleted': deleted_count})


@bp.route('/api/tasks/<int:task_id>/update-recurrence', methods=['PUT'])
def update_task_recurrence(task_id):
    """Обновляет задачу и пересоздаёт все повторы"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    existing = current_app.db.get_by_id(task_id)
    if not existing:
        return jsonify({'error': 'Task not found'}), 404

    # Пересоздаём повторы
    updated_tasks = current_app.db.update_recurrence(task_id, data)
    return jsonify({
        'ok': True,
        'count': len(updated_tasks),
        'tasks': updated_tasks
    })


@bp.route('/api/test-notify', methods=['POST'])
def test_notify():
    notify_today_tasks(current_app.db)
    return jsonify({'ok': True, 'message': 'Notification triggered'})


@bp.route('/api/tasks/recurring', methods=['POST'])
def create_recurring_tasks():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        tasks = current_app.db.create_recurring_tasks(data)
        return jsonify({
            'ok': True,
            'count': len(tasks),
            'tasks': tasks
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/api/tasks/clear', methods=['DELETE'])
def clear_all_tasks():
    try:
        current_app.db.delete_all()
        return jsonify({'ok': True, 'message': 'All tasks deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@bp.route('/api/tasks/<int:task_id>/files', methods=['POST'])
def upload_file(task_id):
    """Загружает файл для задачи"""
    task = current_app.db.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Создаем уникальное имя файла с ID задачи
    filename = secure_filename(file.filename)
    unique_filename = f"{task_id}_{filename}"

    # Создаем папку если не существует
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Сохраняем файл
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    # Добавляем файл в задачу
    updated_task = current_app.db.add_file(task_id, unique_filename)

    return jsonify({
        'ok': True,
        'filename': unique_filename,
        'task': updated_task
    }), 201


@bp.route('/api/tasks/<int:task_id>/files/<filename>', methods=['GET'])
def download_file(task_id, filename):
    """Скачивает файл задачи"""
    task = current_app.db.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if filename not in task.get('файлы', []):
        return jsonify({'error': 'File not found in task'}), 404

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@bp.route('/api/tasks/<int:task_id>/files/<filename>', methods=['DELETE'])
def delete_file(task_id, filename):
    """Удаляет файл задачи"""
    task = current_app.db.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    if filename not in task.get('файлы', []):
        return jsonify({'error': 'File not found in task'}), 404

    # Удаляем файл с диска
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Удаляем из БД
    updated_task = current_app.db.remove_file(task_id, filename)

    return jsonify({
        'ok': True,
        'task': updated_task
    })
