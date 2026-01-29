// AG-Grid API
let gridApi;

// Функция для получения месяца из даты
function getMonthYear(dateStr) {
    if (!dateStr) return 'Без даты';
    const date = new Date(dateStr);
    const months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                    'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'];
    return `${months[date.getMonth()]} ${date.getFullYear()}`;
}

// Рендерер для файлов
function filesRenderer(params) {
    if (!params.data || params.data.isMonthSeparator) return '';
    const files = params.data.файлы || [];
    if (files.length === 0) {
        return '<span style="cursor: pointer; color: #999;" onclick="uploadFile(' + params.data.id + ')">📎 Загрузить</span>';
    }
    let html = '<div style="display: flex; gap: 5px; align-items: center;">';
    html += '<span style="cursor: pointer;" onclick="uploadFile(' + params.data.id + ')">📎' + files.length + '</span>';
    files.forEach(file => {
        html += '<a href="/api/tasks/' + params.data.id + '/files/' + file + '" target="_blank" title="' + file + '">📄</a>';
    });
    html += '</div>';
    return html;
}

// Рендерер для чекбокса активности
function activeCheckboxRenderer(params) {
    if (!params.data || params.data.isMonthSeparator) return '';
    const checked = params.data.флаг ? 'checked' : '';
    return `<input type="checkbox" ${checked} onchange="toggleFlag(${params.data.id})" style="cursor: pointer; width: 18px; height: 18px;">`;
}

// Рендерер для иконок действий
function actionsRenderer(params) {
    if (!params.data || params.data.isMonthSeparator) return '';
    const отправлено = params.data.отправлено ? '✅' : '❌';
    const hasChildren = params.data.родитель_id === null && params.data.повтор_тип !== 'none';
    const deleteTitle = hasChildren ? 'Удалить все повторы' : 'Удалить';
    return `
        <div style="display: flex; gap: 5px; justify-content: center; align-items: center;">
            <span title="Отправлено" style="font-size: 14px;">${отправлено}</span>
            <span title="${deleteTitle}" style="cursor: pointer; font-size: 14px; color: red;" onclick="deleteTask(${params.data.id})">${hasChildren ? '🗑️🗑️' : '🗑️'}</span>
        </div>
    `;
}

// Определение колонок
const columnDefs = [
    {
        headerName: 'ID',
        field: 'id',
        width: 60,
        editable: false,
        filter: 'agNumberColumnFilter',
        sortable: true,
        pinned: 'left',
        valueFormatter: params => {
            if (params.data && params.data.isMonthSeparator) {
                return '';
            }
            return params.value;
        }
    },
    {
        headerName: '№ ТСД/указания',
        field: 'номер_тсд',
        width: 130,
        editable: true,
        filter: 'agTextColumnFilter',
        sortable: true
    },
    {
        headerName: 'Наименование',
        field: 'название',
        flex: 2,
        editable: true,
        filter: 'agTextColumnFilter',
        sortable: true
    },
    {
        headerName: 'Кому представляется',
        field: 'кому_представляется',
        width: 150,
        editable: true,
        filter: 'agTextColumnFilter',
        sortable: true
    },
    {
        headerName: 'Срок представления',
        field: 'срок_представления',
        width: 140,
        editable: true,
        filter: 'agTextColumnFilter',
        sortable: true
    },
    {
        headerName: 'Примечания',
        field: 'примечания',
        flex: 1,
        editable: true,
        filter: 'agTextColumnFilter',
        sortable: true
    },
    {
        headerName: 'Дата доклада',
        field: 'дата_доклада',
        width: 120,
        editable: true,
        filter: 'agDateColumnFilter',
        sortable: true,
        cellEditor: 'agDateStringCellEditor'
    },
    {
        headerName: 'Повтор',
        field: 'повтор_тип',
        width: 110,
        editable: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: {
            values: ['none', 'daily', 'weekly', 'monthly', 'yearly']
        },
        valueFormatter: params => {
            const types = {
                'none': '-',
                'daily': 'Ежедневно',
                'weekly': 'Еженедельно',
                'monthly': 'Ежемесячно',
                'yearly': 'Ежегодно'
            };
            return types[params.value] || '-';
        },
        sortable: true
    },
    {
        headerName: 'Активна',
        field: 'флаг',
        width: 80,
        cellRenderer: activeCheckboxRenderer,
        sortable: true,
        filter: true,
        editable: false,
        suppressClickEdit: true,
        suppressNavigable: true
    },
    {
        headerName: 'Файлы',
        width: 100,
        cellRenderer: filesRenderer,
        sortable: false,
        filter: false,
        suppressClickEdit: true
    },
    {
        headerName: 'Действия',
        width: 80,
        cellRenderer: actionsRenderer,
        sortable: false,
        filter: false,
        pinned: 'right',
        suppressClickEdit: true
    }
];

// Настройки AG-Grid
const gridOptions = {
    columnDefs: columnDefs,
    defaultColDef: {
        resizable: true,
        sortable: true,
        filter: true,
        wrapText: true,
        autoHeight: true,
        editable: params => {
            // Разделители месяцев нельзя редактировать
            return !params.data || !params.data.isMonthSeparator;
        }
    },
    suppressMovableColumns: true,
    rowData: [],
    animateRows: true,
    rowSelection: 'single',
    onCellValueChanged: onCellValueChanged,
    localeText: {
        noRowsToShow: 'Нет задач для отображения'
    },
    getRowStyle: params => {
        // Стиль для строк-разделителей месяцев
        if (params.data && params.data.isMonthSeparator) {
            return {
                fontWeight: 'bold',
                backgroundColor: '#1976d2',
                color: 'white',
                fontSize: '14px'
            };
        }
        return null;
    },
    isRowSelectable: params => {
        // Разделители месяцев нельзя выбрать
        return !params.data || !params.data.isMonthSeparator;
    }
};

// Инициализация AG-Grid
document.addEventListener('DOMContentLoaded', function() {
    const gridDiv = document.querySelector('#tasks-grid');
    gridApi = agGrid.createGrid(gridDiv, gridOptions);

    // Загрузка данных
    loadTasks();

    // Кнопки
    document.getElementById('btn-add').addEventListener('click', showTaskModal);
    document.getElementById('btn-refresh').addEventListener('click', loadTasks);
    document.getElementById('btn-export').addEventListener('click', exportCSV);
    document.getElementById('csv-import').addEventListener('change', importCSV);
    document.getElementById('btn-clear').addEventListener('click', clearAllTasks);
    document.getElementById('btn-test-notify').addEventListener('click', testNotify);

    // Модальное окно
    document.getElementById('modal-close').addEventListener('click', hideTaskModal);
    document.getElementById('modal-cancel').addEventListener('click', hideTaskModal);
    document.getElementById('modal-save').addEventListener('click', saveTask);
});

// Загрузка задач с сервера
function loadTasks() {
    fetch('/api/tasks')
        .then(response => {
            if (!response.ok) throw new Error('Ошибка загрузки');
            return response.json();
        })
        .then(data => {
            // Группируем задачи по месяцам и вставляем разделители
            const groupedData = groupTasksByMonth(data);

            // Очищаем сортировку перед загрузкой данных
            gridApi.applyColumnState({
                defaultState: { sort: null }
            });

            gridApi.setGridOption('rowData', groupedData);
            console.log('Загружено задач:', data.length);
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить задачи: ' + error.message);
        });
}

// Группировка задач по месяцам со вставкой разделителей
function groupTasksByMonth(tasks) {
    if (!tasks || tasks.length === 0) return [];

    // Сортируем по дате
    tasks.sort((a, b) => {
        const dateA = new Date(a.дата_доклада || '9999');
        const dateB = new Date(b.дата_доклада || '9999');
        return dateA - dateB;
    });

    const result = [];
    let currentMonth = null;

    tasks.forEach(task => {
        const month = getMonthYear(task.дата_доклада);

        if (month !== currentMonth) {
            // Вставляем строку-разделитель месяца
            result.push({
                id: 'month_' + month,
                isMonthSeparator: true,
                номер_тсд: month,
                название: '',
                кому_представляется: '',
                срок_представления: '',
                примечания: '',
                дата_доклада: '',
                повтор_тип: 'none',
                флаг: 0,
                отправлено: 0,
                файлы: []
            });
            currentMonth = month;
        }

        result.push(task);
    });

    return result;
}

// Обработчик изменения ячейки
function onCellValueChanged(event) {
    if (event.data.isMonthSeparator) return; // Игнорируем разделители

    const updatedData = event.data;
    const changedColumn = event.column.getColId();

    console.log('Ячейка изменена:', changedColumn, updatedData);

    // Если изменили повтор - используем специальный endpoint
    if (changedColumn === 'повтор_тип') {
        updateTaskWithRecurrence(updatedData);
    } else {
        updateTask(updatedData);
    }
}

// Обновление задачи с пересозданием повторов
function updateTaskWithRecurrence(task) {
    if (!confirm('Изменить тип повтора? Это пересоздаст все повторяющиеся задачи.')) {
        loadTasks();
        return;
    }

    fetch('/api/tasks/' + task.id + '/update-recurrence', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task)
    })
    .then(response => {
        if (!response.ok) throw new Error('Ошибка сохранения');
        return response.json();
    })
    .then(data => {
        const count = data.count || 1;
        console.log('Задачи обновлены:', count);
        alert(`✅ Обновлено задач: ${count}`);
        loadTasks();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Не удалось обновить повтор: ' + error.message);
        loadTasks();
    });
}

// Обновление задачи на сервере
function updateTask(task) {
    fetch('/api/tasks/' + task.id, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(task)
    })
    .then(response => {
        if (!response.ok) throw new Error('Ошибка сохранения');
        return response.json();
    })
    .then(data => {
        console.log('Задача обновлена:', data);
        loadTasks(); // Перезагружаем для обновления группировки
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Не удалось сохранить изменения: ' + error.message);
        loadTasks();
    });
}

// Переключение флага
function toggleFlag(id) {
    if (typeof id === 'string' && id.startsWith('month_')) {
        return; // Игнорируем клики по разделителям месяцев
    }
    fetch('/api/tasks/' + id)
        .then(response => {
            if (!response.ok) throw new Error('Task not found');
            return response.json();
        })
        .then(task => {
            task.флаг = task.флаг ? 0 : 1;
            // Обновляем только флаг, не трогая повтор
            fetch('/api/tasks/' + task.id, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(task)
            })
            .then(response => {
                if (!response.ok) throw new Error('Ошибка сохранения');
                return response.json();
            })
            .then(() => {
                console.log('Флаг обновлен:', task.id);
                loadTasks();
            })
            .catch(error => {
                console.error('Ошибка:', error);
                loadTasks();
            });
        })
        .catch(error => {
            console.error('Ошибка переключения флага:', error);
        });
}

// Удаление задачи
function deleteTask(id) {
    // Получаем информацию о задаче чтобы узнать есть ли дочерние
    fetch('/api/tasks/' + id)
        .then(response => response.json())
        .then(task => {
            const hasChildren = task.родитель_id === null && task.повтор_тип !== 'none';
            const confirmMsg = hasChildren
                ? `Удалить задачу #${id} и ВСЕ её повторы?`
                : `Удалить задачу #${id}?`;

            if (!confirm(confirmMsg)) {
                return;
            }

            // Используем специальный endpoint для удаления с дочерними
            const endpoint = hasChildren ? `/api/tasks/${id}/with-children` : `/api/tasks/${id}`;

            fetch(endpoint, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) throw new Error('Ошибка удаления');
                return response.json();
            })
            .then((data) => {
                const count = data.deleted || 1;
                console.log('Удалено задач:', count);
                alert(`✅ Удалено задач: ${count}`);
                loadTasks();
            })
            .catch(error => {
                console.error('Ошибка:', error);
                alert('Не удалось удалить задачу: ' + error.message);
            });
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Не удалось получить информацию о задаче: ' + error.message);
        });
}

// Показать модальное окно для создания задачи
function showTaskModal() {
    document.getElementById('task-modal').style.display = 'flex';
}

// Скрыть модальное окно
function hideTaskModal() {
    document.getElementById('task-modal').style.display = 'none';
    document.getElementById('task-form').reset();
}

// Сохранить задачу
function saveTask() {
    const form = document.getElementById('task-form');
    const formData = new FormData(form);

    const taskData = {
        номер_тсд: formData.get('номер_тсд'),
        название: formData.get('название'),
        кому_представляется: formData.get('кому_представляется'),
        срок_представления: formData.get('срок_представления'),
        примечания: formData.get('примечания'),
        дата_доклада: formData.get('дата_доклада'),
        флаг: 1,
        повтор_тип: formData.get('повтор_тип'),
        повтор_интервал: parseInt(formData.get('повтор_интервал')) || 1,
        повтор_до: formData.get('повтор_до')
    };

    if (!taskData.название) {
        alert('Укажите наименование');
        return;
    }

    if (!taskData.дата_доклада) {
        alert('Укажите дату доклада');
        return;
    }

    if (taskData.повтор_тип !== 'none' && !taskData.повтор_до) {
        alert('Укажите дату окончания повторений');
        return;
    }

    // Если повтор, используем эндпоинт recurring
    const endpoint = taskData.повтор_тип !== 'none' ? '/api/tasks/recurring' : '/api/tasks';

    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
    })
    .then(response => {
        if (!response.ok) throw new Error('Ошибка создания');
        return response.json();
    })
    .then(data => {
        const count = data.count || 1;
        console.log('Создано задач:', count);
        alert(`✅ Создано задач: ${count}`);
        hideTaskModal();
        loadTasks();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('❌ Не удалось создать задачу: ' + error.message);
    });
}

// Загрузка файла
function uploadFile(taskId) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.doc,.docx,.txt,.xlsx,.xls,.png,.jpg,.jpeg,.gif';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/tasks/' + taskId + '/files', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) throw new Error('Ошибка загрузки');
            return response.json();
        })
        .then(data => {
            console.log('Файл загружен:', data.filename);
            alert('✅ Файл загружен: ' + data.filename);
            loadTasks();
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('❌ Не удалось загрузить файл: ' + error.message);
        });
    };
    input.click();
}

// Экспорт в CSV
function exportCSV() {
    // Фильтруем разделители месяцев перед экспортом
    const allData = [];
    gridApi.forEachNode(node => {
        if (node.data && !node.data.isMonthSeparator) {
            allData.push(node.data);
        }
    });

    // Создаем временную таблицу для экспорта
    const tempGrid = document.createElement('div');
    const tempGridApi = agGrid.createGrid(tempGrid, {
        columnDefs: columnDefs.filter(col => col.headerName !== 'Файлы' && col.headerName !== 'Действия'),
        rowData: allData
    });

    tempGridApi.exportDataAsCsv({
        fileName: 'tasks_' + new Date().toISOString().split('T')[0] + '.csv',
        skipColumnGroupHeaders: true
    });

    tempGridApi.destroy();
    console.log('CSV экспортирован');
}

// Импорт из CSV
function importCSV(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        const lines = text.split('\n');

        const tasks = [];
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;

            const parts = line.split(',');
            if (parts.length < 5) continue;

            tasks.push({
                номер_тсд: parts[1] || '',
                название: parts[2] || '',
                кому_представляется: parts[3] || '',
                дата_доклада: parts[4] || '',
                срок_представления: parts[5] || '',
                примечания: parts[6] || '',
                флаг: parseInt(parts[7]) || 1,
                повтор_тип: parts[8] || 'none'
            });
        }

        let created = 0;
        tasks.forEach(task => {
            fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(task)
            })
            .then(response => response.json())
            .then(() => {
                created++;
                if (created === tasks.length) {
                    loadTasks();
                    alert('Импортировано задач: ' + created);
                }
            });
        });
    };

    reader.readAsText(file);
    event.target.value = '';
}

// Тестовое уведомление
function testNotify() {
    if (!confirm('Отправить тестовое уведомление в Telegram?')) {
        return;
    }

    fetch('/api/test-notify', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) throw new Error('Ошибка отправки');
        return response.json();
    })
    .then(data => {
        console.log('Уведомление отправлено:', data);
        alert('✅ Уведомление отправлено! Проверь Telegram.');
        loadTasks();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('❌ Не удалось отправить уведомление: ' + error.message);
    });
}

// Очистить все задачи
function clearAllTasks() {
    if (!confirm('⚠️ ВНИМАНИЕ! Это удалит ВСЕ задачи без возможности восстановления. Продолжить?')) {
        return;
    }

    fetch('/api/tasks/clear', {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) throw new Error('Ошибка удаления');
        return response.json();
    })
    .then(() => {
        console.log('Все задачи удалены');
        alert('✅ Все задачи удалены');
        loadTasks();
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('❌ Не удалось удалить задачи: ' + error.message);
    });
}
