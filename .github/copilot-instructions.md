## Быстрый контекст для AI-агентов

**Обновлено:** 23 октября 2025  
**Версия:** 2.0  
**Статус:** ✅ Критический баг исправлен + рабочее веб-приложение

Цель репозитория: простая Python-библиотека для взаимодействия с клиентским API Авито (авторизация, информация о профиле, мессенджер, вакансии).

---

## 🐛 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ

**Баг OAuth2 token refresh (ИСПРАВЛЕН)**

**Файл:** `src/AvitoAPI/Profile.py`, строка 52

**Проблема:**
```python
# ❌ БЫЛО (НЕПРАВИЛЬНО):
def __UpdaterThread(self):
    while True:
        sleep(1380)  # 23 минуты вместо 23 часов!
        self.refresh_access_token()
```

**Решение:**
```python
# ✅ СТАЛО (ПРАВИЛЬНО):
def __UpdaterThread(self):
    while True:
        sleep(23 * 60 * 60)  # 82800 секунд = 23 часа
        self.refresh_access_token()
```

**Последствия бага:**
- Приложения переставали работать через 24 часа
- Ошибки 401 "Bad bearer token"
- Требовался ручной перезапуск

**Важность:** КРИТИЧНО для продакшен-окружения с `autorefresh=True`

---

## 📊 ПРАВИЛЬНАЯ СТРУКТУРА ДАННЫХ API

### ⚠️ Отклики на вакансии (Job API)

**ВАЖНО:** API возвращает `'applies'`, НЕ `'applications'`!

```python
# ✅ ПРАВИЛЬНО:
response = user.post("https://api.avito.ru/job/v1/applications/get_by_ids", json={"ids": ids})
data = response.json()
applications = data.get('applies')  # НЕ 'applications'!

# Структура данных:
for app in applications:
    name = app['applicant']['data']['name']  # НЕ app['candidate']['name']
    chat_id = app['contacts']['chat']['value']  # Для связи с чатом
    
# ❌ НЕПРАВИЛЬНО:
applications = data.get('applications')  # KeyError или None!
name = app['candidate']['name']  # KeyError!
```

**Ключевые поля:**
- `applies` - массив откликов (НЕ 'applications')
- `applicant.data.name` - имя соискателя
- `contacts.chat.value` - ID чата для связи
- `contacts.phone.value` - телефон (если есть)

---

## 🌐 ВЕБ-ПРИЛОЖЕНИЕ (НОВОЕ)

### Описание

На базе протестированных методов создано полнофункциональное Flask веб-приложение.

**Файл:** `messenger_app.py` (700+ строк)  
**Технологии:** Flask + Flask-SocketIO + SQLite + Bootstrap 5  
**URL:** http://localhost:5000

### Функционал

1. **Мессенджер:**
   - Просмотр всех чатов
   - Отправка/получение сообщений
   - История с визуальным разделением in/out

2. **Автоответы:**
   - Мониторинг каждые 10 секунд
   - Отправка только на первое сообщение
   - Включение/выключение через UI

3. **Отклики на вакансии:**
   - Список откликов за период
   - Детальная информация
   - Связь с чатами

4. **Dashboard:**
   - Статистика в реальном времени
   - WebSocket live обновления

### Запуск

```bash
pip install flask flask-socketio requests
python messenger_app.py
# Откройте http://localhost:5000
```

### API Endpoints

```
GET  /                              - главная страница
GET  /api/profile                   - информация о профиле
GET  /api/balance                   - баланс
GET  /api/chats?limit=50            - список чатов
GET  /api/chats/<id>/messages       - сообщения
POST /api/chats/<id>/send           - отправка
GET  /api/applications?days=30      - отклики
POST /api/applications/details      - детали откликов
POST /api/auto-reply/toggle         - вкл/выкл автоответы
```

---

## 🧪 ТЕСТЫ

### Комплексный мега-тест

**Файл:** `TRUE_METHODS_API/comprehensive_api_test.py` (700+ строк)

Объединяет 3 тестовых блока:
1. **Базовые методы:** Profile, Info, Job, Messenger
2. **Мессенджер:** чаты, сообщения, направление, прочтение
3. **Отклики:** детальная информация, связь с чатами

**Запуск:**
```bash
python TRUE_METHODS_API/comprehensive_api_test.py
# Результаты: comprehensive_test_results.txt (569 строк)
```

**Exit code 0** = все тесты пройдены ✅

---

## 📚 ДОКУМЕНТАЦИЯ

### Файлы документации

1. **README.md** - общее описание проекта и установка
2. **WEB_APP_GUIDE.md** - полное руководство по веб-приложению (800+ строк)
3. **TRUE_METHODS_API/AVITO_API_GUIDE.md** - детальное API руководство (700+ строк)
4. **TRUE_METHODS_API/README.md** - описание тестов
5. **.github/copilot-instructions.md** - этот файл

### Swagger спецификации

Папка `Swaggers/` содержит:
- `swagger_avito_Authorization.txt` - OAuth2
- `swagger_avito_messages.txt` - Messenger API
- `swagger_avito_пользователи.txt` - User API
- `swagger_avito_Иерархия.txt` - Data structure

---

## Ключевые модули и где смотреть

### src/AvitoAPI/Profile.py

Основной обработчик профиля:
- Получает и обновляет access token
- Методы `get`, `post`, `request` с автоматическим Authorization
- Автообновление токена: `__UpdaterThread` (✅ исправлено: 23 часа)
- Опциональный наблюдатель: `__SupervisorThread`

**Критическая строка 52:** `sleep(23 * 60 * 60)` - обновление токена

### src/AvitoAPI/Modules.py

Высокоуровневые модули API:
- `Info` - информация о профиле, баланс
- `Messenger` - чаты, сообщения
- `Job` - отклики на вакансии
- `ShortTermRent` - краткосрочная аренда

Принимают `profile` и `session` (или `Profile.request`).

### src/AvitoAPI/Types/

DTO классы-обёртки:
- `Info.py` - Balance, ProfileInfo
- `ShortTermRent.py` - Booking, BookingsDates, Discounts, Instant, RentPeriods

Используются как простые DTO с геттерами.

---

## Архитектура и важные решения

### Авторизация

- Profile управляет авторизацией и сессией
- Другие модули получают ссылку на `Profile.request`
- Изменения в авторизации централизованы в `Profile`
- Token lifetime: 24 часа, refresh: 23 часа (82800 секунд)

### Возвращаемые типы

Модули возвращают:
- Объекты-DTO (когда нужно разобрать JSON)
- `requests.Response` для raw-обработки

Всегда проверяйте `Response.status_code == 200`!

### Многопоточность

1. **Main Thread:** основное приложение
2. **Token Updater Thread:** обновление токена каждые 23 часа
3. **Supervisor Thread:** опциональный мониторинг (если включен)
4. **Auto-reply Thread:** мониторинг сообщений (в веб-приложении)

---

## Проектные паттерны и соглашения

### Версия Python

- Python >= 3.10
- Аннотации типов с Union-операторами: `int | str`
- Сохраняйте совместимость с 3.10+

### HTTP вызовы

- Используется `requests` библиотека
- `Profile` создаёт `requests.Session()`
- Методы: `get/post/request`
- Проверяйте интерфейс использования session

### DTO классы

- Принимают словарь в конструкторе
- Реализуют свойства только для чтения
- Паттерн: принимать dict, предоставлять свойства

### Логирование

- `Profile` импортирует `Logger` из пакета
- `from . import Logger`
- Проверьте формат при модификации

---

## Рабочие сценарии и примеры

### Инициализация профиля

```python
from AvitoAPI.Profile import Profile

User = Profile(
    PROFILE_NUMBER,
    CLIENT_ID,
    CLIENT_SECRET,
    autorefresh=True  # ✅ Автообновление токена каждые 23 часа
)
```

### Получение чатов

```python
# Messenger модуль автоматически доступен через Profile
chats = User.messenger.get_chats(limit=50)
print(f"Найдено чатов: {len(chats)}")

for chat in chats:
    user_name = chat.get('context', {}).get('value', {}).get('user_name')
    print(f"Чат с {user_name}")
```

### Отклики на вакансии

```python
# ✅ ПРАВИЛЬНЫЙ СПОСОБ
from datetime import datetime, timedelta

# Получение ID откликов
date_from = (datetime.now() - timedelta(days=30)).isoformat()
response = User.job.get_application_ids(
    updated_at_from=date_from,
    limit=100
)

if response.status_code == 200:
    data = response.json()
    application_ids = data.get('result', {}).get('items', [])
    
    # Получение детальной информации
    body = {"ids": application_ids[:20]}  # Макс 20 за раз
    response = User.post(
        "https://api.avito.ru/job/v1/applications/get_by_ids",
        json=body
    )
    
    if response.status_code == 200:
        data = response.json()
        applications = data.get('applies')  # ✅ НЕ 'applications'!
        
        for app in applications:
            name = app['applicant']['data']['name']
            chat_id = app.get('contacts', {}).get('chat', {}).get('value')
            print(f"Соискатель: {name}, Chat ID: {chat_id}")
```

---

## Что важно при правках кода

### Контракт Profile.request

**НЕ ИЗМЕНЯЙТЕ** сигнатуру:
```python
Profile.request(method, url, headers=None, params=None, json=None)
```

Многие места завязаны на этом интерфейсе!

### Обновление токена

`refresh_access_token()` должен:
- Быть безопасным для многопоточного использования
- Документировать блокировки/синхронизацию
- Сохранять интервал 23 часа (82800 секунд)

### Тестирование

- Используйте патчинг `requests.Session`
- Или передавайте mock `session` в модули
- Избегайте реальных HTTP-вызовов в тестах

---

## Интеграции и внешние зависимости

### Зависимости

- `requests` - HTTP клиент (см. `pyproject.toml`)
- `flask` - веб-фреймворк (для приложения)
- `flask-socketio` - WebSocket (для приложения)

### API Endpoints

- Авторизация: `https://api.avito.ru/token/`
- Профиль: `https://api.avito.ru/core/v1/accounts/self`
- Мессенджер: `https://api.avito.ru/messenger/v2/`
- Вакансии: `https://api.avito.ru/job/v1/`

---

## Короткие советы для PR/добавления фич

### Добавление новых методов API

1. Создайте DTO в `Types/` (если нужно)
2. Добавьте метод в `Modules.py`
3. Возвращайте `requests.Response` или DTO
4. Следуйте существующей структуре
5. Документируйте параметры и return type

### Тестирование

1. Создайте unit-тесты с моками
2. Мокайте `Profile.__Session.post/get/request`
3. Проверьте exit code = 0
4. Добавьте в `comprehensive_api_test.py`

### Документация

1. Обновите соответствующий .md файл
2. Добавьте примеры кода
3. Опишите структуру данных
4. Укажите возможные ошибки

---

## Файлы для ориентирования

### Основные файлы

- `src/AvitoAPI/Profile.py` - авторизация, сессия, HTTP
- `src/AvitoAPI/Modules.py` - реализация API методов
- `src/AvitoAPI/Types/*.py` - DTO паттерн
- `pyproject.toml` - зависимости, версия Python

### Документация

- `README.md` - использование библиотеки
- `WEB_APP_GUIDE.md` - руководство по веб-приложению
- `TRUE_METHODS_API/AVITO_API_GUIDE.md` - полное API руководство
- `.github/copilot-instructions.md` - этот файл

### Тесты

- `TRUE_METHODS_API/comprehensive_api_test.py` - мега-тест
- `TRUE_METHODS_API/comprehensive_test_results.txt` - результаты

### Веб-приложение

- `messenger_app.py` - Flask приложение (700+ строк)
- `templates/index.html` - Bootstrap 5 интерфейс
- `messenger.db` - SQLite база (создаётся автоматически)

---

## 🚨 Критические моменты

### 1. Token Refresh (КРИТИЧНО!)

**Файл:** `src/AvitoAPI/Profile.py`, строка 52

```python
sleep(23 * 60 * 60)  # ✅ ДОЛЖНО БЫТЬ ТАК
# НЕ sleep(1380)!    # ❌ 23 минуты - НЕПРАВИЛЬНО
```

### 2. Структура откликов

```python
data.get('applies')              # ✅ ПРАВИЛЬНО
data.get('applications')         # ❌ НЕПРАВИЛЬНО

app['applicant']['data']['name'] # ✅ ПРАВИЛЬНО
app['candidate']['name']         # ❌ НЕПРАВИЛЬНО
```

### 3. Chat ID в откликах

```python
chat_id = app['contacts']['chat']['value']  # ✅ ПРАВИЛЬНО
chat_id = app['chat_id']                     # ❌ НЕПРАВИЛЬНО
```

---

## 📞 Поддержка и вопросы

### Если что-то неясно

1. Проверьте документацию в соответствующем .md
2. Запустите `comprehensive_api_test.py`
3. Проверьте swagger спецификации в `Swaggers/`
4. Создайте issue в GitHub

### Области для уточнения

- Retry-политика при ошибках API
- Формат Logger (если меняете логирование)
- Thread safety для новых методов
- Rate limiting стратегии

---

**Версия инструкций:** 2.0  
**Дата обновления:** 23 октября 2025  
**Статус:** ✅ Все критические баги исправлены, документация актуальна

