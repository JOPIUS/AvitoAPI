# 🌐 Веб-приложение Avito Messenger

**Полнофункциональное Flask веб-приложение для работы с Avito API**

[![Status](https://img.shields.io/badge/status-working-brightgreen)]()
[![Flask](https://img.shields.io/badge/flask-3.0+-orange)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue)]()
[![WebSocket](https://img.shields.io/badge/websocket-enabled-green)]()

**Версия:** 2.0  
**Дата:** 23 октября 2025  
**Файл:** `messenger_app.py` (900+ строк)  
**Статус:** ✅ Полностью рабочее + Аналитика чатов

---

## 🆕 Новые возможности (Версия 2.0)

### 📊 Аналитика чатов (5 метрик)
- **Автоматический анализ всех 1100 чатов** при загрузке страницы
- **5 категорий метрик:**
  1. � Прочитал/Нет ответа - клиент прочитал ваше сообщение, но не ответил
  2. ⏳ Не читал - ваше сообщение еще не прочитано
  3. 🤐 Не писали - системные сообщения или чаты без переписки
  4. 📬 Ждут ответ - клиент написал, вы еще не ответили
  5. 🤖 Автоответ - отправлен автоматический ответ
- **Верхняя панель с real-time статистикой**
- **Endpoint:** `GET /api/chats/metrics`

### 🔄 Полная пагинация
- **Cursor-based пагинация** для откликов (макс 100 за запрос)
- **Offset-based пагинация** для чатов (макс 1100 доступно)
- **Автоматическая загрузка всех данных** при старте приложения

---

## �📋 Содержание

1. [Обзор](#обзор)
2. [Установка](#установка)
3. [Конфигурация](#конфигурация)
4. [Запуск](#запуск)
5. [Функциональность](#функциональность)
6. [API Endpoints](#api-endpoints)
7. [База данных](#база-данных)
8. [WebSocket](#websocket)
9. [Архитектура](#архитектура)
10. [Устранение проблем](#устранение-проблем)

---

## 🎯 Обзор

Веб-приложение предоставляет полный набор инструментов для работы с Avito через удобный веб-интерфейс:

### ✨ Ключевые возможности

- **💬 Мессенджер**
  - Просмотр ВСЕХ чатов (до 1100) с автозагрузкой
  - Отправка и получение сообщений в реальном времени
  - История переписки с визуальным разделением входящих/исходящих
  - Автообновление каждые 30 секунд

- **📊 Аналитика чатов (НОВОЕ!)**
  - Автоматический анализ всех чатов при загрузке страницы
  - 5 категорий метрик в верхней панели
  - Real-time обновление статистики
  - Детальная информация по каждой категории

- **🤖 Автоответы**
  - Автоматический мониторинг новых сообщений (каждые 10 секунд)
  - Умная отправка только на первое сообщение от пользователя
  - Включение/выключение через веб-интерфейс одной кнопкой
  - Настраиваемый шаблон ответа

- **💼 Управление откликами**
  - Список всех откликов на вакансии за последние 30 дней
  - Детальная информация: имя, текст отклика, дата
  - Прямой переход к чату с соискателем
  - Статистика по откликам

- **📊 Dashboard**
  - Статистика в реальном времени: чаты, баланс, отклики
  - Информация о профиле: ID, email, статус
  - Актуальный баланс счёта в рублях
  - WebSocket уведомления для live обновлений

### 🏗️ Технологический стек

- **Backend:** Flask 3.0+ (Python web framework)
- **Real-time:** Flask-SocketIO для WebSocket соединений
- **Database:** SQLite3 для хранения данных
- **HTTP Client:** Requests для API вызовов
- **Frontend:** Bootstrap 5 + Vanilla JavaScript
- **Icons:** Font Awesome 6
- **API:** AvitoAPI library (DUB1401/AvitoAPI)

---

## 🚀 Установка

### Предварительные требования

- Python 3.10 или новее
- pip (менеджер пакетов Python)
- Аккаунт Avito с API доступом

### Шаг 1: Установка AvitoAPI библиотеки

```bash
cd AvitoAPI
pip install -e .
cd ..
```

### Шаг 2: Установка зависимостей веб-приложения

```bash
pip install flask flask-socketio requests python-socketio
```

### Шаг 3: Проверка установки

```bash
python -c "import flask; import flask_socketio; import requests; print('✅ Все зависимости установлены')"
```

---

## ⚙️ Конфигурация

### Настройка учётных данных

Откройте `messenger_app.py` и укажите свои данные:

```python
# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
PROFILE_NUMBER = "316615541"  # ВАШ номер профиля Avito
CLIENT_ID = "Dm4ruLMEr9MFsV72dN95"  # ВАШ Client ID
CLIENT_SECRET = "f73lNoAJLzuqwoGtVaMnByhQfSlwcyIN_m7wyOeT"  # ВАШ Client Secret
```

### Получение API доступов

1. Войдите в аккаунт Avito
2. Перейдите на <https://www.avito.ru/professionals/api>
3. Создайте приложение и получите Client ID/Secret
4. Убедитесь, что есть права:
   - `messenger:read` - чтение сообщений
   - `messenger:write` - отправка сообщений
   - `job:applications` - отклики на вакансии
   - `user:read` - информация о пользователе

### Настройка автоответов

Измените текст автоответа в коде:

```python
def send_auto_reply(chat_id, user_name):
    """Отправка автоматического ответа"""
    message_text = f"Здравствуйте, {user_name}! Спасибо за ваш отклик. Я свяжусь с вами в ближайшее время."
    # Измените текст на свой
```

---

## 🎬 Запуск

### Запуск приложения

```bash
python messenger_app.py
```

### Вывод при успешном запуске

```
================================================================================
🚀 AVITO MESSENGER - ВЕБ-ПРИЛОЖЕНИЕ
================================================================================
👤 Profile: 316615541
🔑 Client ID: Dm4ruLMEr9MFsV72dN95
================================================================================
✅ База данных инициализирована
🔐 Инициализация профиля 316615541...
Статус ответа: 200
✅ Профиль успешно инициализирован!
✅ Профиль Авито готов

🌐 Запуск веб-сервера на http://localhost:5000
📝 Нажмите Ctrl+C для остановки

 * Running on http://127.0.0.1:5000
 * Running on http://10.2.0.2:5000
```

### Открытие в браузере

Перейдите по адресу: **<http://localhost:5000>**

---

## 🎨 Функциональность

### 1. Главная страница (Dashboard)

**URL:** `http://localhost:5000/`

**Элементы интерфейса:**

#### Верхняя панель со статистикой
- 💬 **Всего чатов** - количество активных диалогов
- 💰 **Баланс** - текущий баланс счёта в рублях
- 📝 **Отклики** - количество откликов на вакансии
- 🤖 **Авто-ответы** - статус (включено/выключено)

#### Левая панель - Чаты
- Список всех активных чатов
- Имя пользователя
- Последнее сообщение (превью)
- Клик по чату → загрузка истории сообщений

#### Центральная панель - Сообщения
- История переписки с выбранным пользователем
- Входящие сообщения (слева, серые)
- Исходящие сообщения (справа, синие)
- Поле ввода для отправки нового сообщения
- Кнопка "Отправить" или Enter для отправки

#### Правая панель - Отклики
- Список откликов на вакансии
- Для каждого отклика:
  - Имя соискателя
  - Дата отклика
  - Статус (просмотрено/не просмотрено)
  - Кнопка "Открыть чат" (если доступен)

### 2. Автоответы

**Как включить:**

1. Нажмите кнопку **"Включить автоответы"** в верхней части интерфейса
2. Статус изменится на зелёный: **"Включено"**
3. Система начнёт мониторинг каждые 10 секунд

**Как работает:**

- Система проверяет все чаты на наличие новых сообщений
- Если находит первое сообщение от пользователя → отправляет автоответ
- Сохраняет информацию в БД, чтобы не отправлять повторно
- Уведомляет через WebSocket о каждом отправленном автоответе

**Как отключить:**

1. Нажмите кнопку **"Отключить автоответы"**
2. Мониторинг останавливается

### 3. Отправка сообщений

**Способ 1: Через интерфейс**

1. Выберите чат в левой панели
2. Введите текст в поле внизу
3. Нажмите Enter или кнопку "Отправить"
4. Сообщение появится в истории справа (синее)

**Способ 2: Через API**

```bash
curl -X POST http://localhost:5000/api/chats/CHAT_ID/send \
  -H "Content-Type: application/json" \
  -d '{"text": "Привет!"}'
```

### 4. Просмотр откликов

**Автоматическая загрузка:**

- При открытии страницы загружаются отклики за последние 30 дней
- Обновляются автоматически каждые 30 секунд

**Переход к чату:**

1. Найдите отклик в правой панели
2. Если есть значок 💬 - нажмите "Открыть чат"
3. Автоматически откроется чат с этим соискателем

---

## 🔌 API Endpoints

### REST API

#### Профиль и баланс

**GET /api/profile**
```json
{
  "id": 316615541,
  "email": "user@example.com",
  "name": "Имя пользователя"
}
```

**GET /api/balance**
```json
{
  "real": 1500.50,
  "bonus": 0
}
```

#### Чаты и сообщения

**GET /api/chats?limit=50**

Получение списка чатов

Parameters:
- `limit` (optional) - количество чатов (default: 50, max: 100)

Response:
```json
[
  {
    "id": "chat_id_123",
    "context": {
      "value": {
        "user_name": "Иван Иванов"
      }
    },
    "last_message": {
      "content": {
        "text": "Здравствуйте!"
      }
    }
  }
]
```

**GET /api/chats/<chat_id>/messages?limit=100**

Получение сообщений из чата

Parameters:
- `limit` (optional) - количество сообщений (default: 100)

Response:
```json
{
  "messages": [
    {
      "id": "msg_123",
      "direction": "in",
      "content": {"text": "Привет"},
      "created": "2025-10-23T10:00:00Z",
      "read": null
    }
  ]
}
```

**POST /api/chats/<chat_id>/send**

Отправка сообщения

Body:
```json
{
  "text": "Текст сообщения"
}
```

Response:
```json
{
  "success": true,
  "message_id": "msg_456"
}
```

#### Отклики на вакансии

**GET /api/applications?days=30**

Получение откликов

Parameters:
- `days` (optional) - за сколько дней (default: 30)

Response:
```json
{
  "applications": [
    {
      "id": "app_123",
      "applicant_name": "Петр Петров",
      "created_at": "2025-10-20T15:30:00Z",
      "status": "new",
      "chat_id": "chat_789"
    }
  ]
}
```

**POST /api/applications/details**

Детальная информация по откликам

Body:
```json
{
  "application_ids": ["id1", "id2", "id3"]
}
```

Response:
```json
{
  "applies": [
    {
      "id": "id1",
      "applicant": {
        "data": {
          "name": "Имя"
        }
      },
      "contacts": {
        "chat": {
          "value": "chat_id"
        }
      }
    }
  ]
}
```

**GET /api/applications/stats**

Статистика по откликам

Response:
```json
{
  "total": 50,
  "with_chat": 35,
  "without_chat": 15,
  "percentage_with_chat": 70
}
```

**GET /api/chats/all** ⭐ НОВОЕ

Получение ВСЕХ чатов через автоматическую пагинацию (до 1100 чатов)

Response:
```json
{
  "chats": [...],  // массив всех чатов
  "total": 1100
}
```

**GET /api/chats/metrics** ⭐ НОВОЕ

Аналитика по всем чатам - 5 категорий метрик

Response:
```json
{
  "total_chats": 1100,
  "metrics": {
    "wrote_read_no_reply": 432,  // Написали, прочитал, не ответил
    "wrote_unread": 224,          // Написали, не читал
    "not_wrote": 334,             // Не писали (системные)
    "waiting_reply": 85,          // Ждут ответ
    "auto_reply_sent": 25         // Отправлен автоответ
  },
  "details": {
    "wrote_read_no_reply": [
      {
        "chat_id": "u2i-xxx",
        "user_name": "Иван",
        "read_at": 1761143729
      }
    ],
    // ... детали по каждой категории
  }
}
```

**GET /api/applications/all?days=30** ⭐ НОВОЕ

Получение ВСЕХ откликов через cursor-based пагинацию

Parameters:
- `days` (optional) - за сколько дней (default: 30)

Response:
```json
{
  "total": 643,
  "ids": ["id1", "id2", ...],  // все ID откликов
  "applications": [...]         // детальная информация
}
```

#### Автоответы

**POST /api/auto-reply/toggle**

Включение/выключение автоответов

Body:
```json
{
  "enabled": true
}
```

Response:
```json
{
  "success": true,
  "enabled": true
}
```

**GET /api/auto-reply/status**

Статус автоответов

Response:
```json
{
  "enabled": true
}
```

---

## 💾 База данных

### Структура SQLite

Файл: `messenger.db`

#### Таблица: messages_status

Отслеживание статусов отправленных сообщений

```sql
CREATE TABLE messages_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    message_id TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    UNIQUE(chat_id, message_id)
);
```

**Использование:**
- Хранит информацию о каждом отправленном сообщении
- Позволяет отслеживать статус доставки
- Используется для статистики

#### Таблица: auto_replies

История автоматических ответов

```sql
CREATE TABLE auto_replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    user_id TEXT,
    replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_text TEXT,
    UNIQUE(chat_id)
);
```

**Использование:**
- Предотвращает повторную отправку автоответа
- Хранит историю всех автоответов
- `UNIQUE(chat_id)` - один автоответ на чат

#### Таблица: applications

Кэш откликов на вакансии

```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT UNIQUE NOT NULL,
    applicant_name TEXT,
    created_at TIMESTAMP,
    status TEXT,
    chat_id TEXT
);
```

**Использование:**
- Кэширует информацию об откликах
- Ускоряет загрузку данных
- Связывает отклики с чатами

### Операции с БД

#### Инициализация

```python
def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('messenger.db')
    cursor = conn.cursor()
    
    # Создание таблиц
    cursor.execute('''CREATE TABLE IF NOT EXISTS ...''')
    
    conn.commit()
    conn.close()
```

#### Добавление автоответа

```python
def save_auto_reply(chat_id, user_id, message_text):
    """Сохранение автоответа в БД"""
    conn = sqlite3.connect('messenger.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR IGNORE INTO auto_replies 
        (chat_id, user_id, message_text)
        VALUES (?, ?, ?)
    ''', (chat_id, user_id, message_text))
    
    conn.commit()
    conn.close()
```

#### Проверка автоответа

```python
def has_auto_reply(chat_id):
    """Проверка, был ли отправлен автоответ"""
    conn = sqlite3.connect('messenger.db')
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT COUNT(*) FROM auto_replies WHERE chat_id = ?',
        (chat_id,)
    )
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0
```

---

## 🔌 WebSocket (Socket.IO)

### События

#### Client → Server

**connect**

Клиент подключается к серверу

```javascript
socket = io.connect('http://localhost:5000');
```

#### Server → Client

**new_message**

Новое сообщение получено

```javascript
socket.on('new_message', function(data) {
    console.log('Новое сообщение:', data);
    // data = {chat_id, message_id, text, direction}
});
```

**auto_reply_sent**

Автоответ отправлен

```javascript
socket.on('auto_reply_sent', function(data) {
    console.log('Автоответ отправлен:', data);
    // data = {chat_id, user_name, message_text}
});
```

### Пример использования в JavaScript

```javascript
// Подключение к WebSocket
const socket = io.connect('http://localhost:5000');

// Обработка подключения
socket.on('connect', function() {
    console.log('✅ WebSocket подключен');
});

// Обработка новых сообщений
socket.on('new_message', function(data) {
    // Обновить интерфейс с новым сообщением
    addMessageToChat(data.chat_id, data.text, data.direction);
});

// Обработка автоответов
socket.on('auto_reply_sent', function(data) {
    // Показать уведомление
    showNotification('Автоответ отправлен: ' + data.user_name);
});

// Обработка отключения
socket.on('disconnect', function() {
    console.log('❌ WebSocket отключен');
});
```

---

## 🏛️ Архитектура

### Структура приложения

```
messenger_app.py (700+ строк)
├── Импорты и зависимости
├── Конфигурация (Profile, Client ID/Secret)
├── Инициализация Flask + SocketIO
├── Инициализация базы данных
├── Инициализация AvitoAPI Profile
├── Вспомогательные функции
│   ├── get_chats_list()
│   ├── get_chat_messages()
│   ├── send_message_to_chat()
│   ├── get_profile_info()
│   ├── get_balance()
│   ├── get_job_applications()
│   └── get_applications_details()
├── Фоновые процессы
│   └── auto_reply_monitor_thread()
├── API Routes
│   ├── GET /
│   ├── GET /api/profile
│   ├── GET /api/balance
│   ├── GET /api/chats
│   ├── GET /api/chats/<id>/messages
│   ├── POST /api/chats/<id>/send
│   ├── GET /api/applications
│   ├── POST /api/applications/details
│   ├── GET /api/applications/stats
│   ├── POST /api/auto-reply/toggle
│   └── GET /api/auto-reply/status
└── WebSocket Handlers
    ├── on('connect')
    └── on('disconnect')
```

### Поток данных

```
Browser
   ↓
   ├─→ HTTP Request → Flask Route → AvitoAPI → Avito Server
   │                      ↓
   │                  Response
   │                      ↓
   ├─→ WebSocket ← SocketIO ← Background Thread
   │
   └─→ SQLite Database (Cache/History)
```

### Многопоточность

1. **Main Thread (Flask)**: обработка HTTP запросов
2. **SocketIO Thread**: WebSocket соединения
3. **Auto-reply Thread**: мониторинг новых сообщений (каждые 10 сек)
4. **Token Updater Thread**: обновление OAuth2 токена (каждые 23 часа)

---

## 🐛 Устранение проблем

### Ошибка: 401 Bad bearer token

**Причина:** Неверный или устаревший токен

**Решение:**

1. Проверьте CLIENT_ID и CLIENT_SECRET
2. Убедитесь, что исправлен баг token refresh:
   ```python
   # AvitoAPI/src/AvitoAPI/Profile.py, строка 52
   sleep(23 * 60 * 60)  # Должно быть 82800 секунд
   ```
3. Перезапустите приложение

### Ошибка: No module named 'flask_socketio'

**Причина:** Не установлен Flask-SocketIO

**Решение:**

```bash
pip install flask-socketio python-socketio
```

### Ошибка: Address already in use (port 5000)

**Причина:** Порт 5000 занят другим процессом

**Решение 1:** Освободить порт

```bash
# Windows
netstat -ano | findstr :5000
taskkill /F /PID <PID>

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

**Решение 2:** Изменить порт в коде

```python
socketio.run(app, host='0.0.0.0', port=8000, debug=True)
```

### WebSocket не работает

**Причина:** Проблемы с совместимостью версий

**Решение:**

```bash
pip install --upgrade flask-socketio python-socketio
```

### Автоответы не отправляются

**Причина:** Мониторинг не запущен или ошибка в логике

**Диагностика:**

1. Проверьте статус автоответов: GET `/api/auto-reply/status`
2. Проверьте логи в терминале
3. Проверьте БД: `SELECT * FROM auto_replies;`

**Решение:**

```python
# Убедитесь, что auto_reply_enabled = True
# И поток запущен: auto_reply_thread.start()
```

### Чаты не загружаются

**Причина:** Ошибка API или нет чатов

**Диагностика:**

```bash
curl http://localhost:5000/api/chats
```

**Решение:**

1. Проверьте, что есть хотя бы один чат на Avito
2. Проверьте scope: `messenger:read`
3. Проверьте логи ошибок в терминале

### База данных повреждена

**Причина:** Некорректное завершение приложения

**Решение:**

```bash
# Удалить и пересоздать БД
del messenger.db
python messenger_app.py
```

---

## 📊 Производительность

### Рекомендации

- **Rate Limiting:** Пауза 1 секунда между API запросами
- **Кэширование:** Используйте БД для кэширования данных
- **Пагинация:** Загружайте не более 50-100 элементов за раз
- **WebSocket:** Используйте для real-time, избегайте polling

### Лимиты Avito API

- **Длина сообщения:** максимум 4096 символов
- **Чаты:** рекомендуется limit=50
- **Отклики:** загружаются за последние 90 дней (рекомендуется 30)
- **Token lifetime:** 24 часа (обновляется автоматически через 23 часа)

---

## 📝 Changelog

### Version 1.0 (23 октября 2025)

- ✅ Первый рабочий релиз
- ✅ Полный функционал мессенджера
- ✅ Автоответы с мониторингом
- ✅ Управление откликами
- ✅ WebSocket real-time
- ✅ SQLite база данных
- ✅ Bootstrap 5 интерфейс
- ✅ Исправлен баг OAuth2 token refresh

---

## 📞 Поддержка

**Документация:**
- README.md - общее описание проекта
- AVITO_API_GUIDE.md - руководство по API
- WEB_APP_GUIDE.md - этот файл

**Тесты:**
- TRUE_METHODS_API/comprehensive_api_test.py

**Проблемы и вопросы:**
- Создайте issue в GitHub репозитории
- Проверьте логи в терминале при запуске

---

**Автор:** Создано на базе AvitoAPI library (DUB1401/AvitoAPI)  
**Лицензия:** MIT  
**Версия:** 1.0  
**Дата:** 23 октября 2025

✅ **Статус:** Полностью рабочее приложение, протестировано и готово к использованию!
