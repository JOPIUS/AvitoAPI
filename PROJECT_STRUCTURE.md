# 📁 Структура проекта Avito Messenger

**Дата:** 23 октября 2025  
**Версия:** 2.0  
**Статус:** ✅ Очищено от дубликатов, готово к работе

---

## 🗂️ Полная структура

```
Avito_messenger/
│
├── 📄 README.md                          # Главное руководство по проекту
├── 📄 WEB_APP_GUIDE.md                   # Полное руководство по веб-приложению (800+ строк)
├── 📄 PROJECT_STRUCTURE.md               # Этот файл - структура проекта
├── 📄 messenger_app.py                   # Flask веб-приложение (700+ строк)
├── 📄 comprehensive_test_results.txt     # Результаты комплексного теста (569 строк)
├── 🗄️ messenger.db                       # SQLite база данных (создаётся автоматически)
│
├── 📂 templates/                         # HTML шаблоны для веб-приложения
│   └── 📄 index.html                     # Dashboard интерфейс с Bootstrap 5
│
├── 📂 TRUE_METHODS_API/                  # Тесты и документация API
│   ├── 📄 README.md                      # Описание тестов и результатов
│   ├── 📄 AVITO_API_GUIDE.md            # Полное API руководство (900+ строк)
│   └── 📄 comprehensive_api_test.py     # Комплексный мега-тест (754 строки)
│
├── 📂 Swaggers/                          # Swagger спецификации Avito API
│   ├── 📄 swagger_avito_Authorization.txt          # OAuth2 авторизация
│   ├── 📄 swagger_avito_CallTracking.txt           # Call Tracking API
│   ├── 📄 swagger_avito_messages.txt               # Messenger API
│   ├── 📄 swagger_avito_rabota_обновленная.txt     # Job API (актуальная версия)
│   ├── 📄 swagger_avito_Иерархия.txt               # Структура данных
│   └── 📄 swagger_avito_пользователи{.txt          # User API
│
└── 📂 AvitoAPI/                          # Библиотека для работы с Avito API
    ├── 📄 README.md                      # Документация библиотеки
    ├── 📄 pyproject.toml                 # Конфигурация проекта и зависимости
    ├── 📄 LICENSE                        # MIT License
    ├── 📄 .gitignore                     # Git ignore правила
    │
    ├── 📂 .github/
    │   └── 📄 copilot-instructions.md    # Инструкции для AI-агентов (версия 2.0)
    │
    └── 📂 src/
        └── 📂 AvitoAPI/
            ├── 📄 __init__.py            # Инициализация пакета
            ├── 📄 Profile.py             # OAuth2 авторизация и управление токенами
            ├── 📄 Modules.py             # Модули API: Messenger, Job, Info
            └── 📂 Types/
                ├── 📄 Info.py            # DTO классы для Info API
                └── 📄 ShortTermRent.py   # DTO классы для аренды
```

---

## 📊 Статистика файлов

### Документация
- **README.md** - главное руководство (360+ строк)
- **WEB_APP_GUIDE.md** - руководство по веб-приложению (800+ строк)
- **TRUE_METHODS_API/AVITO_API_GUIDE.md** - API reference (900+ строк)
- **TRUE_METHODS_API/README.md** - описание тестов (150+ строк)
- **AvitoAPI/.github/copilot-instructions.md** - контекст для AI (400+ строк)

**Итого документации:** ~2600+ строк

### Код приложения
- **messenger_app.py** - Flask приложение (700+ строк)
- **templates/index.html** - Dashboard UI (450+ строк)

**Итого код приложения:** ~1150+ строк

### Тесты
- **TRUE_METHODS_API/comprehensive_api_test.py** - мега-тест (754 строки)
- **comprehensive_test_results.txt** - результаты (569 строк)

**Итого тесты:** ~1323 строки

### Библиотека AvitoAPI
- **Profile.py** - авторизация (~300+ строк)
- **Modules.py** - API модули (~400+ строк)
- **Types/** - DTO классы (~200+ строк)

**Итого библиотека:** ~900+ строк

### Swagger спецификации
- 6 файлов с API спецификациями (~3000+ строк)

---

## 🎯 Назначение основных файлов

### 🌐 Веб-приложение

**messenger_app.py**
- Flask веб-сервер на порту 5000
- REST API endpoints для чатов, сообщений, откликов
- WebSocket (Socket.IO) для real-time обновлений
- Автоответы с мониторингом каждые 10 секунд
- SQLite база данных для хранения истории

**templates/index.html**
- Bootstrap 5 интерфейс
- Dashboard со статистикой
- Панель чатов
- Панель сообщений
- Панель откликов на вакансии
- Кнопка автоответов

**messenger.db**
- SQLite база данных (создаётся автоматически)
- Таблицы: messages_status, auto_replies, applications

### 🧪 Тесты и документация

**TRUE_METHODS_API/comprehensive_api_test.py**
- Комплексный тест всех API методов
- Блок 1: Базовые методы (Profile, Info, Job, Messenger)
- Блок 2: Функции мессенджера (чаты, сообщения, статусы)
- Блок 3: Отклики на вакансии (детальная информация)
- Сохраняет результаты в файл

**comprehensive_test_results.txt**
- Результаты последнего запуска тестов
- 569 строк детальной информации
- Все API responses в JSON формате
- Статистика по каждому блоку

**TRUE_METHODS_API/AVITO_API_GUIDE.md**
- Полное руководство по Avito API (900+ строк)
- Примеры кода для всех методов
- Структура данных с JSON examples
- Исправленные баги и best practices
- Описание веб-приложения

**TRUE_METHODS_API/README.md**
- Описание тестов и их результатов
- Инструкции по запуску
- Что протестировано

### 📚 Общая документация

**README.md**
- Главное руководство по проекту
- Установка и настройка
- Функциональность веб-приложения
- API endpoints
- Устранение проблем
- Технические детали

**WEB_APP_GUIDE.md**
- Детальное руководство по веб-приложению (800+ строк)
- Установка и конфигурация
- Все функции подробно
- REST API endpoints с примерами
- Структура базы данных
- WebSocket events
- Архитектура приложения
- Troubleshooting

### 🔧 Библиотека AvitoAPI

**AvitoAPI/src/AvitoAPI/Profile.py**
- OAuth2 Client Credentials авторизация
- Автообновление токена каждые 23 часа (82800 секунд)
- Методы get(), post(), request() с автоматическим Authorization
- ✅ ИСПРАВЛЕН критический баг: sleep(23 * 60 * 60) вместо sleep(1380)

**AvitoAPI/src/AvitoAPI/Modules.py**
- Модуль **Info**: get_balance(), профиль
- Модуль **Messenger**: get_chats(), get_messages(), send_message()
- Модуль **Job**: get_application_ids(), детали откликов
- Модуль **ShortTermRent**: краткосрочная аренда

**AvitoAPI/src/AvitoAPI/Types/**
- DTO классы для данных API
- Balance, ProfileInfo
- Booking, Discounts, RentPeriods

**AvitoAPI/.github/copilot-instructions.md**
- Контекст для AI-агентов (версия 2.0)
- Критическое исправление token refresh
- Правильная структура данных API
- Описание веб-приложения
- Рабочие примеры кода

### 📋 Swagger спецификации

**Swaggers/**
- Официальные API спецификации от Avito
- Используются для reference при разработке
- Содержат все endpoints, параметры, responses

---

## 🔄 Поток работы

### 1. Разработка
```
1. Изучить документацию в README.md
2. Настроить credentials в messenger_app.py
3. Установить зависимости: pip install flask flask-socketio requests
4. Запустить: python messenger_app.py
5. Открыть: http://localhost:5000
```

### 2. Тестирование
```
1. Перейти в TRUE_METHODS_API/
2. Запустить: python comprehensive_api_test.py
3. Проверить результаты в comprehensive_test_results.txt
4. Убедиться что exit code = 0
```

### 3. Изучение API
```
1. Открыть TRUE_METHODS_API/AVITO_API_GUIDE.md
2. Найти нужный метод
3. Скопировать пример кода
4. Адаптировать под свои нужды
```

### 4. Устранение проблем
```
1. Проверить WEB_APP_GUIDE.md раздел "Устранение проблем"
2. Проверить логи в консоли
3. Запустить тесты для диагностики
4. Проверить .github/copilot-instructions.md для контекста
```

---

## 🚨 Важные моменты

### Критическое исправление
**Файл:** AvitoAPI/src/AvitoAPI/Profile.py, строка 52
```python
sleep(23 * 60 * 60)  # ✅ 82800 секунд = 23 часа (ПРАВИЛЬНО)
# НЕ sleep(1380)     # ❌ 23 минуты (НЕПРАВИЛЬНО, БЫЛ БАГ)
```

### Правильная структура данных
```python
# ✅ ПРАВИЛЬНО:
data.get('applies')              # Отклики на вакансии
app['applicant']['data']['name'] # Имя соискателя
app['contacts']['chat']['value'] # Chat ID

# ❌ НЕПРАВИЛЬНО:
data.get('applications')         # KeyError!
app['candidate']['name']         # KeyError!
app['chat_id']                   # KeyError!
```

### Файлы для модификации
- **Изменить credentials:** `messenger_app.py` (строки 20-22)
- **Изменить автоответ:** `messenger_app.py` (функция send_auto_reply)
- **Изменить интервалы:** `messenger_app.py` (AUTO_REPLY_CHECK_INTERVAL)

### Файлы только для чтения
- ❌ Не изменять: `AvitoAPI/src/AvitoAPI/Profile.py` (кроме фикса)
- ❌ Не изменять: `comprehensive_test_results.txt` (генерируется автоматически)
- ❌ Не изменять: `messenger.db` (SQLite база, управляется приложением)

---

## 📦 Зависимости

### Python пакеты
```bash
# Для веб-приложения
flask>=3.0
flask-socketio>=5.3
requests>=2.31

# Для библиотеки (в AvitoAPI/pyproject.toml)
requests>=2.31
```

### Системные требования
- Python >= 3.10
- pip (менеджер пакетов)
- Браузер для веб-интерфейса
- Интернет-соединение для API

---

## 🎨 Визуальная структура

```
📁 Avito_messenger (корень проекта)
│
├── 🌐 Веб-приложение
│   ├── messenger_app.py        → Flask сервер
│   ├── templates/index.html    → UI интерфейс
│   └── messenger.db            → База данных
│
├── 🧪 Тесты и API документация
│   └── TRUE_METHODS_API/
│       ├── comprehensive_api_test.py  → Мега-тест
│       ├── AVITO_API_GUIDE.md        → API reference
│       └── README.md                  → Описание тестов
│
├── 📚 Документация проекта
│   ├── README.md              → Главное руководство
│   ├── WEB_APP_GUIDE.md       → Руководство по приложению
│   ├── PROJECT_STRUCTURE.md   → Структура проекта
│   └── comprehensive_test_results.txt → Результаты тестов
│
├── 📋 Swagger спецификации
│   └── Swaggers/
│       ├── swagger_avito_Authorization.txt
│       ├── swagger_avito_messages.txt
│       └── ... (6 файлов)
│
└── 🔧 Библиотека AvitoAPI
    └── AvitoAPI/
        ├── src/AvitoAPI/
        │   ├── Profile.py        → OAuth2 авторизация
        │   ├── Modules.py        → API модули
        │   └── Types/            → DTO классы
        ├── .github/
        │   └── copilot-instructions.md → AI контекст
        └── pyproject.toml        → Конфигурация
```

---

## 🔍 Быстрый поиск

### Нужно найти информацию о...

**Установке и запуске**
→ README.md, раздел "Установка и запуск"

**Веб-приложении**
→ WEB_APP_GUIDE.md

**API методах**
→ TRUE_METHODS_API/AVITO_API_GUIDE.md

**Тестах**
→ TRUE_METHODS_API/README.md

**Структуре проекта**
→ PROJECT_STRUCTURE.md (этот файл)

**Контексте для AI**
→ AvitoAPI/.github/copilot-instructions.md

**Устранении проблем**
→ WEB_APP_GUIDE.md, раздел "Устранение проблем"

**Swagger спецификациях**
→ Swaggers/ (6 файлов)

---

## 📈 История версий

### Версия 2.0 (23 октября 2025)
- ✅ Исправлен критический баг OAuth2 token refresh
- ✅ Создано веб-приложение на Flask (700+ строк)
- ✅ Комплексный мега-тест (754 строки)
- ✅ Обновлена вся документация (2600+ строк)
- ✅ Очищена структура проекта от дубликатов
- ✅ Удалено 17 лишних файлов и папок

### Версия 1.0 (22 октября 2025)
- Начальная версия с тестами
- Базовая документация
- Библиотека AvitoAPI

---

**Автор документа:** GitHub Copilot  
**Дата создания:** 23 октября 2025  
**Статус:** ✅ Актуально

---

_Этот файл автоматически генерируется и поддерживается в актуальном состоянии._
