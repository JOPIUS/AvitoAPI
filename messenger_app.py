#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AVITO MESSENGER - ВЕБ-ПРИЛОЖЕНИЕ
Использует проверенные endpoint'ы из comprehensive_api_test.py
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import sqlite3
import json
import threading
import time
from datetime import datetime, timedelta
import sys
import os
import logging
import traceback
from logging.handlers import RotatingFileHandler

# Настройка ротации логов (максимум 3 запуска по 10MB каждый)
log_handler = RotatingFileHandler(
    'messenger_app.log', 
    maxBytes=10*1024*1024,  # 10MB
    backupCount=2,  # Хранить 2 старых файла (всего 3 файла)
    encoding='utf-8'
)
log_handler.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s')
log_handler.setFormatter(log_formatter)

# Консольный хендлер с цветами
class ColoredConsoleHandler(logging.StreamHandler):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def emit(self, record):
        try:
            msg = self.format(record)
            color = self.COLORS.get(record.levelname, self.RESET)
            print(f"{color}{msg}{self.RESET}")
        except Exception:
            self.handleError(record)

console_handler = ColoredConsoleHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        log_handler,
        console_handler
    ]
)
logger = logging.getLogger(__name__)

# Логируем старт
logger.info("="*60)
logger.info("🚀 AVITO MESSENGER - ЗАПУСК")
logger.info("="*60)

# Добавляем путь к AvitoAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AvitoAPI', 'src'))

from AvitoAPI.Profile import Profile

app = Flask(__name__)
app.secret_key = 'avito-messenger-secret-key-2025-very-secure'
app.config['SESSION_PERMANENT'] = True

# Middleware для логирования всех запросов
import time as time_module

@app.before_request
def log_request():
    """Логируем каждый входящий запрос"""
    request.start_time = time_module.time()
    logger.info(f"🌐 [{request.method}] {request.path} | Query: {dict(request.args)} | IP: {request.remote_addr}")

@app.after_request
def log_response(response):
    """Логируем каждый ответ с временем выполнения"""
    if hasattr(request, 'start_time'):
        duration = (time_module.time() - request.start_time) * 1000
        logger.info(f"✅ [{request.method}] {request.path} → {response.status_code} | {duration:.2f}ms")
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Логируем все необработанные исключения"""
    logger.error(f"💥 ОШИБКА в {request.path}: {str(e)}")
    logger.error(traceback.format_exc())
    return jsonify({"error": str(e), "path": request.path}), 500
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 час
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Отключаем кэширование статических файлов
socketio = SocketIO(app, cors_allowed_origins="*")

# Отключаем кэширование для всех запросов
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROFILE_NUMBER = "316615541"
CLIENT_ID = "Dm4ruLMEr9MFsV72dN95"
CLIENT_SECRET = "f73lNoAJLzuqwoGtVaMnByhQfSlwcyIN_m7wyOeT"
AUTO_REPLY_TEXT = 'Спасибо, что откликнулись! Чтобы более подробно узнать о текущей вакансии и других предложениях, пожалуйста, напишите на whatsapp по номеру 79890443897 или дождитесь звонка рекрутера.'

# Глобальные переменные
avito_profile = None
auto_reply_active = True  # ВКЛЮЧЕН по умолчанию — пользователь просил автоответчик активным при запуске
monitoring_thread = None
monitoring_active = False

# ============================================================================
# БАЗА ДАННЫХ
# ============================================================================

def get_db_connection(timeout=60):  # Увеличил до 60 секунд
    """
    Создает подключение к БД с увеличенным timeout для предотвращения блокировок.
    WAL mode устанавливается один раз и сохраняется в БД.
    """
    conn = sqlite3.connect('messenger.db', timeout=timeout, isolation_level=None)  # isolation_level=None для autocommit в WAL
    # Проверяем и устанавливаем WAL mode (делается один раз, сохраняется в БД)
    cursor = conn.execute('PRAGMA journal_mode')
    current_mode = cursor.fetchone()[0]
    if current_mode != 'wal':
        conn.execute('PRAGMA journal_mode=WAL')
        logger.info("✅ WAL mode установлен для БД")
    return conn

def execute_db_with_retry(func, max_retries=3, retry_delay=0.5):
    """
    Выполняет функцию работы с БД с повторными попытками при блокировке.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                logger.warning(f"БД заблокирована, попытка {attempt + 1}/{max_retries}, ждём {retry_delay}с...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Экспоненциальная задержка
            else:
                raise

def init_database():
    """Инициализация базы данных с retry механизмом."""
    def _init():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Таблица для отслеживания статусов сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                message_id TEXT UNIQUE,
                user_id INTEGER,
                vacancy_id INTEGER,
                sent_at DATETIME,
                read_at DATETIME,
                is_auto_reply BOOLEAN DEFAULT FALSE,
                message_text TEXT
            )
        ''')
        
        # Таблица для автоответов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE,
                user_name TEXT,
                sent_at DATETIME,
                message_text TEXT
            )
        ''')
        
        # Таблица для кандидатов (полная информация из откликов)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT UNIQUE,
                chat_id TEXT,
                candidate_name TEXT,
                candidate_phone TEXT,
                candidate_email TEXT,
                vacancy_id TEXT,
                vacancy_title TEXT,
                applied_at DATETIME,
                cover_letter TEXT,
                resume_url TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_candidates_chat_id ON candidates(chat_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(candidate_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_candidates_phone ON candidates(candidate_phone)')
        
        # Таблица для хранения всех телефонов кандидатов (может быть несколько на одного)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidate_phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT,
                phone TEXT NOT NULL,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES candidates(application_id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_candidate_phones_phone ON candidate_phones(phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_candidate_phones_app_id ON candidate_phones(application_id)')
        
        # Таблица для метрик чатов (для отслеживания статусов)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE,
                user_name TEXT,
                metric_type TEXT,
                last_message_direction TEXT,
                last_message_text TEXT,
                last_message_time DATETIME,
                is_read BOOLEAN,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_metrics_type ON chat_metrics(metric_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_metrics_chat_id ON chat_metrics(chat_id)')
        
        # Таблица для откликов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT UNIQUE,
                vacancy_id INTEGER,
                candidate_name TEXT,
                candidate_phone TEXT,
                chat_id TEXT,
                is_viewed BOOLEAN,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')
        
        # Таблица для кампаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_sent BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Таблица для сообщений кампаний
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaign_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                message_order INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        ''')
        
        # Таблица для отслеживания отправленных кампаний в чаты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                campaign_id INTEGER NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'sent',
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            )
        ''')
        
        # Таблица для настроек (включая текст автоответчика)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица для истории всех сообщений (для фильтра "Не писали")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                message_id TEXT UNIQUE,
                direction TEXT NOT NULL,
                author_id INTEGER,
                content_text TEXT,
                message_type TEXT,
                created_at DATETIME,
                read_at DATETIME,
                is_system BOOLEAN DEFAULT FALSE,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_history_chat_id ON message_history(chat_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_history_direction ON message_history(direction)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_history_author ON message_history(author_id)')
        
        # Таблица для отслеживания прочитанных чатов (помечаем вручную)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS read_chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE NOT NULL,
                marked_read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_read_chats_chat_id ON read_chats(chat_id)')
        
        # Таблица для хранения телефонов из чатов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                phone TEXT NOT NULL,
                user_name TEXT,
                phone_status TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chat_id, phone)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_phones_phone ON chat_phones(phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_phones_chat_id ON chat_phones(chat_id)')
        
        # Инициализируем текст автоответчика по умолчанию (если не существует)
        cursor.execute('SELECT value FROM settings WHERE key = ?', ('auto_reply_text',))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO settings (key, value) VALUES (?, ?)
            ''', ('auto_reply_text', AUTO_REPLY_TEXT))
        
        # Индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_campaigns_chat ON chat_campaigns(chat_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_campaigns_campaign ON chat_campaigns(campaign_id)')
        
        conn.commit()
        conn.close()
        return True
    
    # Вызываем внутреннюю функцию с retry механизмом
    execute_db_with_retry(_init)

def load_auto_reply_text():
    """Загружает текст автоответчика из БД."""
    global AUTO_REPLY_TEXT
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', ('auto_reply_text',))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            AUTO_REPLY_TEXT = result[0]
            print(f"✅ Текст автоответчика загружен из БД ({len(AUTO_REPLY_TEXT)} символов)")
        else:
            print("⚠️ Текст автоответчика не найден в БД, используется значение по умолчанию")
    except Exception as e:
        print(f"❌ Ошибка загрузки текста автоответчика: {e}")

# ============================================================================
# AVITO API - ПРАВИЛЬНЫЕ МЕТОДЫ ИЗ ТЕСТОВ
# ============================================================================

def init_avito_profile():
    """Инициализация профиля Авито с правильными параметрами."""
    global avito_profile
    try:
        print(f"🔐 Инициализация профиля {PROFILE_NUMBER}...")
        # БЕЗ автообновления токена для стабильности веб-приложения
        avito_profile = Profile(
            PROFILE_NUMBER, 
            CLIENT_ID, 
            CLIENT_SECRET, 
            autorefresh=True,  # Включаем автообновление для веб-приложения
            use_supervisor=False, 
            logging=True
        )
        print("✅ Профиль успешно инициализирован!")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации профиля: {e}")
        return False

def get_chats_list(limit=100, offset=0):
    """
    ПРАВИЛЬНЫЙ МЕТОД: Получение списка чатов
    Из comprehensive_api_test.py -> test_get_chats()
    Максимальный лимит API: 100 (согласно swagger документации)
    """
    try:
        if not avito_profile:
            return {"error": "Профиль не инициализирован"}, 500
        
        # Используем messenger.get_chats как в рабочем тесте
        chats = avito_profile.messenger.get_chats(limit=limit, offset=offset)
        
        if isinstance(chats, list):
            return {"chats": chats, "total": len(chats)}, 200
        else:
            return {"error": "Неожиданный формат ответа"}, 500
            
    except Exception as e:
        return {"error": str(e)}, 500

def get_all_chats():
    """
    НОВЫЙ МЕТОД: Получение ВСЕХ чатов через автоматическую пагинацию
    Максимум offset = 1000 согласно API лимитам
    """
    all_chats = []
    offset = 0
    max_offset = 1000  # Максимальный offset согласно swagger
    
    try:
        while offset <= max_offset:
            data, status = get_chats_list(limit=100, offset=offset)
            
            if status != 200:
                break
                
            chats = data.get('chats', [])
            if not chats:  # Если чатов больше нет
                break
                
            all_chats.extend(chats)
            
            # Если получили меньше чем лимит, значит это последняя страница
            if len(chats) < 100:
                break
                
            offset += 100
            
        return {"chats": all_chats, "total": len(all_chats)}, 200
        
    except Exception as e:
        return {"error": str(e)}, 500

def get_chat_messages(chat_id, limit=100, offset=0):
    """
    ПРАВИЛЬНЫЙ МЕТОД: Получение сообщений из чата
    Из comprehensive_api_test.py -> test_get_messages()
    Максимальный лимит API: 100 (согласно swagger документации)
    """
    try:
        if not avito_profile:
            return {"error": "Профиль не инициализирован"}, 500
        
        # Используем messenger.get_messages как в рабочем тесте
        response = avito_profile.messenger.get_messages(chat_id, limit=limit, offset=offset)
        
        # get_messages возвращает dict с ключом 'messages'
        if isinstance(response, dict) and 'messages' in response:
            return {"messages": response['messages'], "total": len(response['messages'])}, 200
        elif hasattr(response, 'status_code'):
            if response.status_code == 200:
                data = response.json()
                return {"messages": data.get('messages', [])}, 200
            else:
                return {"error": f"API вернул код {response.status_code}"}, response.status_code
        else:
            return {"error": "Неожиданный формат ответа"}, 500
            
    except Exception as e:
        return {"error": str(e)}, 500

def save_messages_to_history(chat_id, messages):
    """
    Сохранение сообщений в таблицу message_history для отслеживания истории переписки.
    ОПТИМИЗАЦИЯ: Сохраняем только НОВЫЕ сообщения (проверка по message_id).
    Используется для фильтра "Не писали" и полной истории чата.
    """
    if not messages:
        return
    
    def save_batch():
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Получаем существующие message_id одним запросом
            message_ids = [msg.get('id', '') for msg in messages if msg.get('id')]
            if not message_ids:
                return True
            
            placeholders = ','.join('?' * len(message_ids))
            cursor.execute(f'''
                SELECT message_id FROM message_history 
                WHERE message_id IN ({placeholders})
            ''', message_ids)
            existing_ids = {row[0] for row in cursor.fetchall()}
            
            # Фильтруем только НОВЫЕ сообщения
            new_messages = [msg for msg in messages if msg.get('id', '') not in existing_ids]
            
            if not new_messages:
                logger.debug(f"Чат {chat_id}: все {len(messages)} сообщений уже сохранены")
                return True
            
            # Сохраняем только новые
            for msg in new_messages:
                message_id = msg.get('id', '')
                direction = msg.get('direction', '')
                author_id = msg.get('author_id', 0)
                content = msg.get('content', {})
                text = content.get('text', '')
                msg_type = msg.get('type', '')
                created_at = msg.get('created', '')
                read_at = msg.get('read', None)
                is_system = (author_id == 0)
                
                cursor.execute('''
                    INSERT INTO message_history 
                    (chat_id, message_id, direction, author_id, content_text, 
                     message_type, created_at, read_at, is_system, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (chat_id, message_id, direction, author_id, text, 
                      msg_type, created_at, read_at, is_system, datetime.now().isoformat()))
            
            conn.commit()
            logger.info(f"✅ Чат {chat_id}: сохранено {len(new_messages)} новых из {len(messages)} сообщений")
            return True
        except sqlite3.OperationalError as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    try:
        execute_db_with_retry(save_batch)
    except Exception as e:
        logger.error(f"Ошибка сохранения истории сообщений после retry: {e}")

def load_all_messages_history():
    """
    Загружает историю сообщений из всех чатов для формирования полной истории переписки.
    Используется для точного определения фильтра "Не писали".
    """
    try:
        logger.info("🔄 Загрузка истории сообщений из всех чатов...")
        
        # Получаем все чаты
        chats_data, status = get_all_chats()
        if status != 200:
            logger.error("Не удалось получить список чатов")
            return
        
        chats = chats_data.get('chats', [])
        logger.info(f"Получено чатов для загрузки истории: {len(chats)}")
        
        processed = 0
        for chat in chats:
            chat_id = chat.get('id')
            
            # Получаем все сообщения из чата (максимум 100)
            messages_data, msg_status = get_chat_messages(chat_id, limit=100, offset=0)
            
            if msg_status == 200 and 'messages' in messages_data:
                messages = messages_data['messages']
                save_messages_to_history(chat_id, messages)
                processed += 1
                
                if processed % 50 == 0:
                    logger.info(f"Обработано чатов: {processed}/{len(chats)}")
        
        logger.info(f"✅ История сообщений загружена из {processed} чатов")
        
    except Exception as e:
        logger.error(f"Ошибка загрузки истории сообщений: {e}")
        logger.error(traceback.format_exc())

def send_message_to_chat(chat_id, message_text):
    """
    ПРАВИЛЬНЫЙ МЕТОД: Отправка сообщения в чат
    Использует messenger.send_message
    """
    try:
        if not avito_profile:
            return {"error": "Профиль не инициализирован"}, 500
        
        # Используем messenger.send_message
        response = avito_profile.messenger.send_message(chat_id, message_text)
        
        if hasattr(response, 'status_code'):
            if response.status_code == 200:
                # Сохраняем в БД
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages_status (chat_id, sent_at, is_auto_reply, message_text)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, datetime.now().isoformat(), False, message_text))
                conn.commit()
                conn.close()
                
                return {"success": True, "message": "Сообщение отправлено"}, 200
            else:
                return {"error": f"Ошибка отправки: {response.status_code}"}, response.status_code
        else:
            return {"error": "Неожиданный формат ответа"}, 500
            
    except Exception as e:
        return {"error": str(e)}, 500

def get_profile_info():
    """
    ПРАВИЛЬНЫЙ МЕТОД: Получение информации о профиле
    Из comprehensive_api_test.py -> Profile.get
    """
    try:
        if not avito_profile:
            return {"error": "Профиль не инициализирован"}, 500
        
        # Используем прямой GET запрос как в тесте
        response = avito_profile.get("https://api.avito.ru/core/v1/accounts/self")
        
        if response.status_code == 200:
            return response.json(), 200
        else:
            return {"error": f"API вернул код {response.status_code}"}, response.status_code
            
    except Exception as e:
        return {"error": str(e)}, 500

def get_balance():
    """
    ПРАВИЛЬНЫЙ МЕТОД: Получение баланса
    Из comprehensive_api_test.py -> Info.get_balance
    """
    try:
        if not avito_profile:
            return {"error": "Профиль не инициализирован"}, 500
        
        # Используем info.get_balance как в тесте
        balance = avito_profile.info.get_balance()
        
        if balance:
            return {
                "bonus": balance._Balance__Bonus,
                "real": balance._Balance__Real,
                "total": balance._Balance__Bonus + balance._Balance__Real
            }, 200
        else:
            return {"error": "Не удалось получить баланс"}, 500
            
    except Exception as e:
        return {"error": str(e)}, 500

def get_job_applications(days=30, limit=100):
    """
    ПРАВИЛЬНЫЙ МЕТОД: Получение ID откликов
    Из comprehensive_api_test.py -> test_get_application_ids()
    """
    try:
        logger.info(f"=== get_job_applications: days={days}, limit={limit} ===")
        
        if not avito_profile:
            logger.error("Профиль не инициализирован")
            return {"error": "Профиль не инициализирован"}, 500
        
        # Используем job.get_application_ids как в тесте
        updated_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        logger.info(f"Запрос откликов с датой: {updated_from}")
        
        response = avito_profile.job.get_application_ids(updated_at_from=updated_from, limit=limit)
        logger.info(f"Response type: {type(response)}")
        
        if hasattr(response, 'status_code'):
            logger.info(f"Status code: {response.status_code}")
            logger.info(f"Response text: {response.text[:500]}")  # Первые 500 символов
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response JSON keys: {data.keys()}")
                
                # API возвращает 'applies' напрямую, не в 'result.items'!
                applications = data.get('applies', [])
                logger.info(f"Найдено откликов: {len(applications)}")
                
                # Получаем ID для запроса деталей
                app_ids = [app.get('id') for app in applications]
                logger.info(f"IDs откликов: {app_ids[:5]}...")  # Первые 5
                
                return {
                    "applications": applications,
                    "total": len(applications),
                    "ids": app_ids
                }, 200
            else:
                logger.error(f"API вернул код {response.status_code}: {response.text}")
                return {"error": f"API вернул код {response.status_code}"}, response.status_code
        else:
            logger.error(f"Неожиданный формат ответа: {type(response)}")
            return {"error": "Неожиданный формат ответа"}, 500
            
    except Exception as e:
        logger.error(f"Ошибка в get_job_applications: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}, 500

def get_all_job_applications(days=30):
    """
    НОВЫЙ МЕТОД: Получение ВСЕХ откликов через cursor-based пагинацию
    Максимальный лимит API: 100 откликов за запрос
    Используется cursor для загрузки всех страниц
    """
    all_applications = []
    all_ids = []
    limit = 100
    cursor = None
    page = 1
    
    try:
        logger.info(f"=== get_all_job_applications: days={days} ===")
        updated_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        logger.info(f"Запрос ВСЕХ откликов с датой: {updated_from}")
        
        while True:
            logger.info(f"--- Страница {page} ---")
            
            # Cursor-based пагинация для Job API
            if cursor:
                logger.info(f"Запрос с cursor: {cursor[:20]}...")
                response = avito_profile.job.get_application_ids(
                    updated_at_from=updated_from,
                    cursor=cursor,
                    limit=limit
                )
            else:
                logger.info(f"Запрос первой страницы откликов...")
                response = avito_profile.job.get_application_ids(
                    updated_at_from=updated_from, 
                    limit=limit
                )
            
            if hasattr(response, 'status_code'):
                logger.info(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    # API возвращает 'applies' напрямую, не в 'result.items'!
                    applications = data.get('applies', [])
                    logger.info(f"Получено откликов на странице: {len(applications)}")
                    
                    if not applications:  # Если откликов больше нет
                        logger.info("Получен пустой список, пагинация завершена")
                        break
                        
                    all_applications.extend(applications)
                    app_ids = [app.get('id') for app in applications]
                    all_ids.extend(app_ids)
                    logger.info(f"Всего откликов собрано: {len(all_applications)}")
                    
                    # Следующий cursor = ID последнего элемента
                    if applications:
                        last_id = applications[-1].get('id')
                        cursor = last_id
                        logger.info(f"ID последнего отклика для cursor: {last_id[:20]}...")
                    
                    # Если получили меньше чем лимит, значит это последняя страница
                    if len(applications) < limit:
                        logger.info(f"Получено меньше лимита ({len(applications)} < {limit}), последняя страница")
                        break
                        
                    page += 1
                    
                    # Защита от бесконечного цикла
                    if len(all_applications) > 10000:
                        logger.warning("Достигнут лимит безопасности 10000 откликов")
                        break
                else:
                    logger.error(f"Ошибка API: {response.status_code}, {response.text}")
                    break
            else:
                logger.error(f"Неожиданный формат ответа: {type(response)}")
                break
                
        logger.info(f"=== ИТОГО: Получено {len(all_applications)} откликов за {page} страниц ===")
        
        # Проверка уникальности
        unique_ids = set(all_ids)
        if len(unique_ids) != len(all_ids):
            logger.warning(f"ВНИМАНИЕ: Найдены дубликаты! ({len(all_ids)} откликов, {len(unique_ids)} уникальных)")
        else:
            logger.info(f"✅ Все {len(unique_ids)} ID уникальны - дубликатов нет")
        
        return {
            "applications": all_applications,
            "total": len(all_applications),
            "ids": all_ids,
            "pages": page,
            "unique_ids": len(unique_ids)
        }, 200
        
    except Exception as e:
        logger.error(f"Ошибка в get_all_job_applications: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}, 500

def get_applications_details(application_ids):
    """
    ПРАВИЛЬНЫЙ МЕТОД: Получение детальной информации по откликам
    Из comprehensive_api_test.py -> test_get_applications_by_ids()
    """
    try:
        logger.info(f"=== get_applications_details: {len(application_ids)} IDs ===")
        
        if not avito_profile:
            logger.error("Профиль не инициализирован")
            return {"error": "Профиль не инициализирован"}, 500
        
        if not application_ids:
            logger.error("Не указаны ID откликов")
            return {"error": "Не указаны ID откликов"}, 400
        
        # Используем прямой POST запрос как в тесте
        body = {"ids": application_ids[:20]}  # Лимит 20
        logger.info(f"Запрос деталей для {len(body['ids'])} откликов")
        
        response = avito_profile.post("https://api.avito.ru/job/v1/applications/get_by_ids", json=body)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response keys: {data.keys()}")
            applications = data.get('applies', [])  # ВАЖНО: 'applies', не 'applications'!
            logger.info(f"Получено откликов с деталями: {len(applications)}")
            
            # Сохраняем в БД с retry механизмом - ПРАВИЛЬНО обернуто
            def save_applications():
                # Соединение создаётся ВНУТРИ retry, чтобы каждая попытка была независимой
                conn = None
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    for app in applications:
                        applicant = app.get('applicant', {})
                        applicant_data = applicant.get('data', {})
                        candidate_name = applicant_data.get('name', 'Неизвестно')
                        
                        contacts = app.get('contacts', {})
                        phones = contacts.get('phones', [])
                        candidate_phone = phones[0].get('value', '') if phones else ''
                        chat_id = contacts.get('chat', {}).get('value', '')
                        
                        application_id = app.get('id')
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO applications 
                            (application_id, vacancy_id, candidate_name, candidate_phone, chat_id, is_viewed, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            application_id,
                            app.get('vacancy_id'),
                            candidate_name,
                            candidate_phone,
                            chat_id,
                            app.get('is_viewed', False),
                            app.get('created_at'),
                            app.get('updated_at')
                        ))
                        
                        # Сохраняем все телефоны из отклика в таблицу candidate_phones
                        if phones and application_id:
                            for phone_obj in phones:
                                phone_value = phone_obj.get('value', '')
                                phone_status = phone_obj.get('status')
                                
                                if phone_value:  # Сохраняем только непустые телефоны
                                    # ДЕДУПЛИКАЦИЯ: сохраняем каждый телефон один раз
                                    cursor.execute('''
                                        INSERT OR REPLACE INTO candidate_phones (phone, application_id, status)
                                        SELECT ?, ?, ?
                                        WHERE NOT EXISTS (SELECT 1 FROM candidate_phones WHERE phone = ?)
                                    ''', (phone_value, application_id, phone_status, phone_value))
                    
                    phones_saved = cursor.execute('SELECT COUNT(*) FROM candidate_phones').fetchone()[0]
                    logger.info(f"✅ Сохранено {len(applications)} откликов, всего телефонов в БД: {phones_saved}")
                    conn.commit()
                    return True
                except sqlite3.OperationalError as e:
                    if conn:
                        conn.rollback()
                    # Пробрасываем ошибку для retry механизма
                    raise
                finally:
                    if conn:
                        conn.close()
            
            execute_db_with_retry(save_applications)
            logger.info(f"Сохранено в БД: {len(applications)} откликов")
            
            return {"applications": applications, "total": len(applications)}, 200
        else:
            logger.error(f"API вернул код {response.status_code}: {response.text}")
            return {"error": f"API вернул код {response.status_code}"}, response.status_code
            
    except Exception as e:
        logger.error(f"Ошибка в get_applications_details: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}, 500

# ============================================================================
# АВТООТВЕТЧИК
# ============================================================================

def monitor_new_applications():
    """Мониторинг новых откликов для немедленного автоответа."""
    global monitoring_active
    
    print("📋 Мониторинг новых откликов запущен...")
    
    # Сохраняем ID последнего обработанного отклика
    last_processed_id = None
    
    while monitoring_active:
        try:
            if not avito_profile or not auto_reply_active:
                time.sleep(2)
                continue
            
            # Получаем отклики за последний день
            response_data, status = get_job_applications(days=1, limit=10)
            
            if status == 200 and 'applications' in response_data:
                applications = response_data['applications']
                
                # Обрабатываем только новые отклики
                for app in applications:
                    app_id = app.get('id')
                    
                    # Если это новый отклик (еще не обработанный)
                    if last_processed_id and app_id == last_processed_id:
                        break  # Дошли до уже обработанных
                    
                    # Получаем детали отклика для получения chat_id
                    details_data, details_status = get_applications_details([app_id])
                    
                    if details_status == 200 and 'applications' in details_data:
                        app_details = details_data['applications'][0]
                        contacts = app_details.get('contacts', {})
                        chat = contacts.get('chat', {})
                        chat_id = chat.get('value', '')
                        
                        if chat_id:
                            # Проверяем, не отправляли ли уже автоответ в этот чат
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute('SELECT id FROM auto_replies WHERE chat_id = ?', (chat_id,))
                            existing = cursor.fetchone()
                            conn.close()
                            
                            if not existing:
                                # Отправляем автоответ немедленно
                                applicant = app_details.get('applicant', {})
                                applicant_data = applicant.get('data', {})
                                user_name = applicant_data.get('name', 'Кандидат')
                                
                                print(f"📤 Новый отклик! Отправка автоответа в чат {chat_id} для {user_name}...")
                                result, msg_status = send_message_to_chat(chat_id, AUTO_REPLY_TEXT)
                                
                                if msg_status == 200:
                                    # Сохраняем запись об автоответе
                                    conn = get_db_connection()
                                    cursor = conn.cursor()
                                    cursor.execute('''
                                        INSERT OR IGNORE INTO auto_replies (chat_id, user_name, sent_at, message_text)
                                        VALUES (?, ?, ?, ?)
                                    ''', (chat_id, user_name, datetime.now().isoformat(), AUTO_REPLY_TEXT))
                                    conn.commit()
                                    conn.close()
                                    
                                    print(f"✅ Автоответ отправлен на отклик: {user_name}")
                                    
                                    # Уведомляем через WebSocket
                                    socketio.emit('auto_reply_sent', {
                                        'chat_id': chat_id,
                                        'user_name': user_name,
                                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    })
                
                # Обновляем ID последнего обработанного отклика
                if applications:
                    last_processed_id = applications[0].get('id')
            
            time.sleep(5)  # Проверяем новые отклики каждые 5 секунд
            
        except Exception as e:
            print(f"❌ Ошибка в мониторинге откликов: {e}")
            time.sleep(5)
    
    print("🛑 Мониторинг откликов остановлен")

def monitor_new_messages():
    """Мониторинг новых сообщений для автоответа."""
    global monitoring_active
    
    print("🤖 Мониторинг новых сообщений запущен...")
    
    processed_chats = set()
    
    while monitoring_active:
        try:
            if not avito_profile or not auto_reply_active:
                time.sleep(5)
                continue
            
            # Получаем чаты
            chats_data, status = get_chats_list(limit=100)
            
            if status == 200 and "chats" in chats_data:
                chats = chats_data["chats"]
                
                for chat in chats:
                    chat_id = chat.get('id')
                    last_msg = chat.get('last_message', {})
                    
                    # Проверяем: входящее сообщение и еще не обработано
                    if (last_msg.get('direction') == 'in' and 
                        last_msg.get('type') != 'system' and
                        chat_id not in processed_chats):
                        
                        # Проверяем, не отправляли ли мы уже автоответ
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute('SELECT id FROM auto_replies WHERE chat_id = ?', (chat_id,))
                        existing = cursor.fetchone()
                        conn.close()
                        
                        if not existing:
                            # КРИТИЧЕСКАЯ ПРОВЕРКА: Есть ли в чате исходящие сообщения?
                            # Если я уже писал в этот чат - НЕ отправляем автоответ
                            messages_data, msg_status = get_chat_messages(chat_id, limit=100)
                            
                            if msg_status == 200 and 'messages' in messages_data:
                                messages = messages_data['messages']
                                
                                # Проверяем наличие исходящих сообщений
                                has_outgoing = any(msg.get('direction') == 'out' for msg in messages)
                                
                                if has_outgoing:
                                    print(f"⏭️  Пропуск чата {chat_id}: уже был диалог")
                                    processed_chats.add(chat_id)  # Отмечаем как обработанный
                                    continue
                            
                            # Если дошли сюда - можно отправлять автоответ
                            # Отправляем автоответ
                            print(f"📤 Отправка автоответа в чат {chat_id}...")
                            result, status = send_message_to_chat(chat_id, AUTO_REPLY_TEXT)
                            
                            if status == 200:
                                # Сохраняем запись об автоответе
                                chat_users = chat.get('users', [])
                                other_user = None
                                for u in chat_users:
                                    if u.get('id') != int(PROFILE_NUMBER):
                                        other_user = u
                                        break
                                
                                user_name = other_user.get('name', 'Unknown') if other_user else 'Unknown'
                                
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                cursor.execute('''
                                    INSERT INTO auto_replies (chat_id, user_name, sent_at, message_text)
                                    VALUES (?, ?, ?, ?)
                                ''', (chat_id, user_name, datetime.now(), AUTO_REPLY_TEXT))
                                conn.commit()
                                conn.close()
                                
                                processed_chats.add(chat_id)
                                print(f"✅ Автоответ отправлен: {user_name}")
                                
                                # Уведомляем через WebSocket
                                socketio.emit('auto_reply_sent', {
                                    'chat_id': chat_id,
                                    'user_name': user_name,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
            
            time.sleep(2)  # Проверяем каждые 2 секунды для мгновенной отправки
            
        except Exception as e:
            print(f"❌ Ошибка в мониторинге: {e}")
            time.sleep(2)
    
    print("🛑 Мониторинг остановлен")

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Главная страница."""
    import time
    version = int(time.time())  # Timestamp как версия для обхода кэша
    return render_template('index.html', profile_number=PROFILE_NUMBER, v=version)

@app.route('/api/init', methods=['POST'])
def api_init():
    """Инициализация профиля Авито."""
    if init_avito_profile():
        return jsonify({"success": True, "message": "Профиль инициализирован"})
    else:
        return jsonify({"success": False, "message": "Ошибка инициализации"}), 500

@app.route('/api/profile', methods=['GET'])
def api_profile():
    """Получение информации о профиле."""
    data, status = get_profile_info()
    return jsonify(data), status

@app.route('/api/balance', methods=['GET'])
def api_balance():
    """Получение баланса."""
    data, status = get_balance()
    return jsonify(data), status

@app.route('/api/chats', methods=['GET'])
def api_chats():
    """Получение списка чатов."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    data, status = get_chats_list(limit=limit, offset=offset)
    return jsonify(data), status

def get_full_chat_history(chat_id, force_reload=False):
    """
    Загружает ПОЛНУЮ историю чата с пагинацией.
    При force_reload=True загружает все сообщения с API заново.
    Иначе возвращает из БД.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if force_reload:
            logger.info(f"🔄 Загрузка полной истории чата {chat_id} с API...")
            offset = 0
            limit = 100
            all_messages = []
            
            while True:
                data, status = get_chat_messages(chat_id, limit=limit, offset=offset)
                if status != 200 or 'messages' not in data:
                    break
                
                messages = data['messages']
                if not messages:
                    break
                
                all_messages.extend(messages)
                save_messages_to_history(chat_id, messages)  # Сохраняем батч
                
                if len(messages) < limit:  # Последняя страница
                    break
                
                offset += limit
                time.sleep(0.1)  # Небольшая задержка между запросами
            
            logger.info(f"✅ Загружено {len(all_messages)} сообщений из чата {chat_id}")
        
        # Возвращаем из БД (отсортировано по времени создания)
        cursor.execute('''
            SELECT message_id, direction, author_id, content_text, 
                   message_type, created_at, read_at, is_system
            FROM message_history
            WHERE chat_id = ?
            ORDER BY created_at DESC
        ''', (chat_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'direction': row[1],
                'author_id': row[2],
                'content': {'text': row[3]},
                'type': row[4],
                'created': row[5],
                'read': row[6],
                'is_system': row[7]
            })
        
        conn.close()
        return {'messages': messages, 'total': len(messages)}, 200
        
    except Exception as e:
        logger.error(f"Ошибка загрузки истории чата {chat_id}: {e}")
        return {'error': str(e)}, 500

@app.route('/api/chats/<chat_id>/messages', methods=['GET'])
def api_chat_messages(chat_id):
    """Получение сообщений из чата."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    full_history = request.args.get('full_history', 'false').lower() == 'true'
    
    # Если запрашивается полная история - загружаем всё
    if full_history:
        return jsonify(*get_full_chat_history(chat_id, force_reload=True))
    
    # Иначе стандартная пагинация
    data, status = get_chat_messages(chat_id, limit=limit, offset=offset)
    
    # Сохраняем полученные сообщения в историю
    if status == 200 and 'messages' in data:
        save_messages_to_history(chat_id, data['messages'])
    
    return jsonify(data), status

@app.route('/api/chats/<chat_id>/send', methods=['POST'])
def api_send_message(chat_id):
    """Отправка сообщения в чат."""
    message_text = request.json.get('message', '')
    if not message_text:
        return jsonify({"error": "Сообщение не может быть пустым"}), 400
    
    data, status = send_message_to_chat(chat_id, message_text)
    return jsonify(data), status

@app.route('/api/applications', methods=['GET'])
def api_applications():
    """Получение откликов на вакансии."""
    days = request.args.get('days', 30, type=int)
    limit = request.args.get('limit', 100, type=int)
    data, status = get_job_applications(days=days, limit=limit)
    return jsonify(data), status

@app.route('/api/applications/details', methods=['POST'])
def api_applications_details():
    """Получение детальной информации по откликам."""
    application_ids = request.json.get('ids', [])
    data, status = get_applications_details(application_ids)
    return jsonify(data), status

@app.route('/api/chats/<chat_id>/history', methods=['GET'])
def api_chat_history(chat_id):
    """Просмотр сохранённой истории чата из БД (без запросов к API)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Статистика по чату
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN direction = 'in' THEN 1 ELSE 0 END) as incoming,
                   SUM(CASE WHEN direction = 'out' THEN 1 ELSE 0 END) as outgoing,
                   MIN(created_at) as first_message,
                   MAX(created_at) as last_message
            FROM message_history
            WHERE chat_id = ?
        ''', (chat_id,))
        
        stats = cursor.fetchone()
        
        # Получаем сообщения (последние 100 по умолчанию)
        limit = request.args.get('limit', 100, type=int)
        cursor.execute('''
            SELECT message_id, direction, author_id, content_text, 
                   message_type, created_at, read_at, is_system
            FROM message_history
            WHERE chat_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (chat_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'direction': row[1],
                'author_id': row[2],
                'content': {'text': row[3]},
                'type': row[4],
                'created': row[5],
                'read': row[6],
                'is_system': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'chat_id': chat_id,
            'stats': {
                'total': stats[0] or 0,
                'incoming': stats[1] or 0,
                'outgoing': stats[2] or 0,
                'first_message': stats[3],
                'last_message': stats[4]
            },
            'messages': messages
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения истории чата {chat_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/stats', methods=['GET'])
def api_applications_stats():
    """Статистика по откликам из БД."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM applications')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM applications WHERE is_viewed = 1')
    viewed = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM applications WHERE chat_id IS NOT NULL AND chat_id != ""')
    with_chat = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        "total": total,
        "viewed": viewed,
        "not_viewed": total - viewed,
        "with_chat": with_chat,
        "without_chat": total - with_chat
    })

@app.route('/api/auto-reply/toggle', methods=['POST'])
def api_toggle_auto_reply():
    """Включение/выключение автоответчика."""
    global auto_reply_active, monitoring_active, monitoring_thread
    
    action = request.json.get('action', 'toggle')
    
    if action == 'start' or (action == 'toggle' and not auto_reply_active):
        auto_reply_active = True
        
        if not monitoring_active:
            monitoring_active = True
            # Запускаем два потока: для откликов и для сообщений
            thread_messages = threading.Thread(target=monitor_new_messages, daemon=True)
            thread_applications = threading.Thread(target=monitor_new_applications, daemon=True)
            thread_messages.start()
            thread_applications.start()
            print("✅ Запущены оба потока мониторинга: сообщения + отклики")
        
        return jsonify({"success": True, "active": True, "message": "Автоответчик включен"})
    
    elif action == 'stop' or (action == 'toggle' and auto_reply_active):
        auto_reply_active = False
        monitoring_active = False
        
        return jsonify({"success": True, "active": False, "message": "Автоответчик выключен"})
    
    return jsonify({"success": True, "active": auto_reply_active})

@app.route('/api/auto-reply/status', methods=['GET'])
def api_auto_reply_status():
    """Статус автоответчика."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM auto_replies')
    total_sent = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({
        "active": auto_reply_active,
        "monitoring": monitoring_active,
        "total_sent": total_sent,
        "text": AUTO_REPLY_TEXT
    })

@app.route('/api/auto-reply/text', methods=['GET'])
def api_get_auto_reply_text():
    """Получение текста автоответа."""
    return jsonify({"text": AUTO_REPLY_TEXT})

@app.route('/api/auto-reply/text', methods=['POST'])
def api_update_auto_reply_text():
    """Обновление текста автоответа."""
    global AUTO_REPLY_TEXT
    
    new_text = request.json.get('text', '').strip()
    
    if not new_text:
        return jsonify({"error": "Текст не может быть пустым"}), 400
    
    if len(new_text) > 1000:
        return jsonify({"error": "Текст не может превышать 1000 символов"}), 400
    
    # Обновляем глобальную переменную
    AUTO_REPLY_TEXT = new_text
    
    # Сохраняем в БД для сохранения после перезапуска
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at) 
            VALUES (?, ?, ?)
        ''', ('auto_reply_text', new_text, datetime.now()))
        conn.commit()
        conn.close()
        print(f"💾 Текст автоответчика сохранён в БД ({len(new_text)} символов)")
    except Exception as e:
        print(f"❌ Ошибка сохранения в БД: {e}")
    
    return jsonify({
        "success": True,
        "text": AUTO_REPLY_TEXT,
        "message": "Текст автоответа обновлён и сохранён"
    })

# ============================================================================
# НОВЫЕ API ENDPOINTS - ПОЛУЧЕНИЕ ВСЕХ ДАННЫХ
# ============================================================================

@app.route('/api/chats/all', methods=['GET'])
def api_all_chats():
    """Получение ВСЕХ чатов через автоматическую пагинацию."""
    data, status = get_all_chats()
    return jsonify(data), status

@app.route('/api/chats/metrics', methods=['GET'])
def api_chat_metrics():
    """Получение метрик по чатам (5 категорий) - анализирует ВСЕ чаты (макс 1100)"""
    try:
        logger.info("=== api_chat_metrics ===")
        
        # Категории
        metrics = {
            'wrote_read_no_reply': [],  # Написали\Прочитал\Не ответил
            'wrote_unread': [],          # Написали\Не читал
            'not_wrote': [],             # Не писали
            'waiting_reply': [],         # Ждут ответ
            'auto_reply_sent': []        # Отправлен автоответ
        }
        
        # Получаем ВСЕ чаты через пагинацию (макс 1100)
        logger.info("Получение всех чатов через пагинацию...")
        data, status = get_all_chats()
        
        if status != 200:
            logger.error(f"Ошибка получения чатов: {data}")
            return jsonify({'error': data.get('error', 'Unknown error')}), status
        
        chats = data.get('chats', [])
        
        if not isinstance(chats, list):
            logger.error(f"Неожиданный тип чатов: {type(chats)}")
            return jsonify({'error': 'Invalid response type'}), 500
        
        logger.info(f"Получено чатов для анализа: {len(chats)}")
        
        # Сначала загружаем историю всех сообщений в БД
        logger.info("Загрузка истории сообщений для точного определения фильтра...")
        load_all_messages_history()
        
        # Получаем информацию из БД о чатах, куда мы отправляли исходящие сообщения
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Чаты, где есть хотя бы одно наше исходящее сообщение (не системное)
        cursor.execute('''
            SELECT DISTINCT chat_id 
            FROM message_history 
            WHERE direction = 'out' AND is_system = 0
        ''')
        chats_with_outgoing = set(row[0] for row in cursor.fetchall())
        logger.info(f"Чатов с нашими исходящими сообщениями: {len(chats_with_outgoing)}")
        
        # Получаем список помеченных как прочитанные
        cursor.execute('SELECT chat_id FROM read_chats')
        read_chats = set(row[0] for row in cursor.fetchall())
        logger.info(f"Чатов помеченных как прочитанные: {len(read_chats)}")
        
        conn.close()
        
        # Анализируем каждый чат
        for chat in chats:
            chat_id = chat.get('id', 'N/A')
            context = chat.get('context', {}).get('value', {})
            user_name = context.get('user_name', 'Неизвестно')
            last_message = chat.get('last_message', {})
            
            # Проверки
            has_our_messages = chat_id in chats_with_outgoing
            is_marked_read = chat_id in read_chats
            
            if not last_message:
                if not has_our_messages:
                    metrics['not_wrote'].append({
                        'chat_id': chat_id,
                        'user_name': user_name,
                        'reason': 'Нет сообщений'
                    })
                continue
            
            # Анализ последнего сообщения
            direction = last_message.get('direction', '')
            author_id = last_message.get('author_id', 0)
            content = last_message.get('content', {})
            text = content.get('text', '')
            read_timestamp = last_message.get('read', None)
            is_system = (author_id == 0)
            is_auto_reply = AUTO_REPLY_TEXT in text
            
            # Категоризация
            if is_auto_reply and direction == 'out':
                metrics['auto_reply_sent'].append({
                    'chat_id': chat_id,
                    'user_name': user_name
                })
            elif direction == 'in' and not has_our_messages and not is_system and not is_marked_read:
                # НОВАЯ ЛОГИКА: "Ждут ответа" = входящее сообщение И мы никогда не отвечали И не помечен как прочитанный
                metrics['waiting_reply'].append({
                    'chat_id': chat_id,
                    'user_name': user_name,
                    'text': text[:100],
                    'can_mark_read': True
                })
            elif not has_our_messages:
                # "Не писали" = никогда не отправляли исходящие сообщения (но последнее может быть не входящим)
                metrics['not_wrote'].append({
                    'chat_id': chat_id,
                    'user_name': user_name,
                    'reason': 'Никогда не писали исходящих'
                })
            elif direction == 'out' and read_timestamp is not None:
                metrics['wrote_read_no_reply'].append({
                    'chat_id': chat_id,
                    'user_name': user_name,
                    'read_at': read_timestamp
                })
            elif direction == 'out' and read_timestamp is None:
                metrics['wrote_unread'].append({
                    'chat_id': chat_id,
                    'user_name': user_name
                })
        
        # Сохраняем метрики в БД
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Очищаем старые данные
            cursor.execute('DELETE FROM chat_metrics')
            
            # Сохраняем все метрики
            for metric_type, chats_list in metrics.items():
                for chat_info in chats_list:
                    chat_id = chat_info.get('chat_id')
                    user_name = chat_info.get('user_name', 'Неизвестно')
                    text = chat_info.get('text', chat_info.get('reason', ''))
                    
                    # Определяем направление и статус прочтения
                    if metric_type == 'wrote_read_no_reply':
                        direction = 'out'
                        is_read = True
                    elif metric_type == 'wrote_unread':
                        direction = 'out'
                        is_read = False
                    elif metric_type == 'waiting_reply':
                        direction = 'in'
                        is_read = False
                    elif metric_type == 'auto_reply_sent':
                        direction = 'out'
                        is_read = None
                    else:
                        direction = None
                        is_read = None
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO chat_metrics 
                        (chat_id, user_name, metric_type, last_message_direction, 
                         last_message_text, last_message_time, is_read, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (chat_id, user_name, metric_type, direction, text, 
                          datetime.now(), is_read, datetime.now()))
            
            conn.commit()
            conn.close()
            logger.info(f"💾 Метрики сохранены в БД")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения метрик в БД: {e}")
        
        # Статистика
        result = {
            'total_chats': len(chats),
            'metrics': {
                'wrote_read_no_reply': len(metrics['wrote_read_no_reply']),
                'wrote_unread': len(metrics['wrote_unread']),
                'not_wrote': len(metrics['not_wrote']),
                'waiting_reply': len(metrics['waiting_reply']),
                'auto_reply_sent': len(metrics['auto_reply_sent'])
            },
            'details': metrics
        }
        
        logger.info(f"Метрики: {result['metrics']}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Ошибка в api_chat_metrics: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications/all', methods=['GET'])
def api_all_applications():
    """Получение ВСЕХ откликов через автоматическую пагинацию."""
    days = request.args.get('days', 30, type=int)
    data, status = get_all_job_applications(days=days)
    return jsonify(data), status

# ============================================================================
# CANDIDATES API
# ============================================================================

@app.route('/api/candidates', methods=['GET'])
def api_get_candidates():
    """Получение полной информации о всех кандидатах с откликами."""
    try:
        days = request.args.get('days', 90, type=int)
        logger.info(f"=== api_get_candidates (последние {days} дней) ===")
        
        # 1. Получаем все отклики за период
        date_from = (datetime.now() - timedelta(days=days)).isoformat()
        
        response = avito_profile.job.get_application_ids(
            updated_at_from=date_from,
            limit=100
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Ошибка получения откликов'}), response.status_code
        
        data = response.json()
        application_ids = data.get('result', {}).get('items', [])
        logger.info(f"Получено ID откликов: {len(application_ids)}")
        
        if not application_ids:
            return jsonify({'candidates': [], 'total': 0}), 200
        
        # 2. Получаем детальную информацию порциями по 20
        all_candidates = []
        
        for i in range(0, len(application_ids), 20):
            batch = application_ids[i:i+20]
            
            response = avito_profile.post(
                "https://api.avito.ru/job/v1/applications/get_by_ids",
                json={"ids": batch}
            )
            
            if response.status_code != 200:
                logger.error(f"Ошибка получения деталей: {response.status_code}")
                continue
            
            applies_data = response.json()
            applies = applies_data.get('applies', [])
            
            for app in applies:
                app_id = app.get('id', '')
                applicant = app.get('applicant', {}).get('data', {})
                contacts = app.get('contacts', {})
                vacancy = app.get('vacancy', {})
                
                # Извлекаем данные
                candidate = {
                    'application_id': app_id,
                    'name': applicant.get('name', 'Не указано'),
                    'phone': contacts.get('phone', {}).get('value', 'Не указано'),
                    'email': contacts.get('email', {}).get('value', 'Не указано'),
                    'chat_id': contacts.get('chat', {}).get('value', None),
                    'vacancy_id': vacancy.get('id', ''),
                    'vacancy_title': vacancy.get('title', 'Не указано'),
                    'region': applicant.get('region', 'Не указано'),
                    'cover_letter': app.get('cover_letter', {}).get('value', ''),
                    'resume_url': applicant.get('resume_url', ''),
                    'applied_at': app.get('created_at', ''),
                    'status': app.get('status', 'unknown')
                }
                
                # 3. Проверяем какие кампании были отправлены этому кандидату
                if candidate['chat_id']:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT c.id, c.name, cc.sent_at
                        FROM chat_campaigns cc
                        JOIN campaigns c ON cc.campaign_id = c.id
                        WHERE cc.chat_id = ?
                        ORDER BY cc.sent_at DESC
                    ''', (candidate['chat_id'],))
                    
                    sent_campaigns = []
                    for row in cursor.fetchall():
                        sent_campaigns.append({
                            'campaign_id': row[0],
                            'campaign_name': row[1],
                            'sent_at': row[2]
                        })
                    
                    conn.close()
                    candidate['sent_campaigns'] = sent_campaigns
                else:
                    candidate['sent_campaigns'] = []
                
                all_candidates.append(candidate)
        
        # 4. Сохраняем/обновляем в БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for cand in all_candidates:
            cursor.execute('''
                INSERT OR REPLACE INTO candidates 
                (application_id, chat_id, candidate_name, candidate_phone, candidate_email,
                 vacancy_id, vacancy_title, applied_at, cover_letter, resume_url, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                cand['application_id'], cand['chat_id'], cand['name'], cand['phone'], cand['email'],
                cand['vacancy_id'], cand['vacancy_title'], cand['applied_at'], 
                cand['cover_letter'], cand['resume_url'], cand['status'], datetime.now()
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Обработано кандидатов: {len(all_candidates)}")
        
        return jsonify({
            'candidates': all_candidates,
            'total': len(all_candidates)
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка api_get_candidates: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CAMPAIGNS API
# ============================================================================

@app.route('/api/campaigns', methods=['GET'])
def api_get_campaigns():
    """Получение всех кампаний."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.name, c.created_at, c.is_sent,
                   COUNT(cm.id) as message_count,
                   COUNT(DISTINCT cc.chat_id) as sent_to_count
            FROM campaigns c
            LEFT JOIN campaign_messages cm ON c.id = cm.campaign_id
            LEFT JOIN chat_campaigns cc ON c.id = cc.campaign_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''')
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'created_at': row[2],
                'is_sent': bool(row[3]),
                'message_count': row[4],
                'sent_to_count': row[5]
            })
        
        conn.close()
        return jsonify({'campaigns': campaigns}), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения кампаний: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaigns/<int:campaign_id>', methods=['GET'])
def api_get_campaign(campaign_id):
    """Получение деталей кампании с сообщениями."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем кампанию
        cursor.execute('SELECT id, name, created_at, is_sent FROM campaigns WHERE id = ?', (campaign_id,))
        campaign_row = cursor.fetchone()
        
        if not campaign_row:
            conn.close()
            return jsonify({'error': 'Кампания не найдена'}), 404
        
        # Получаем сообщения
        cursor.execute('''
            SELECT id, message_order, text
            FROM campaign_messages
            WHERE campaign_id = ?
            ORDER BY message_order ASC
        ''', (campaign_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'order': row[1],
                'text': row[2]
            })
        
        campaign = {
            'id': campaign_row[0],
            'name': campaign_row[1],
            'created_at': campaign_row[2],
            'is_sent': bool(campaign_row[3]),
            'messages': messages
        }
        
        conn.close()
        return jsonify(campaign), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения кампании: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaigns', methods=['POST'])
def api_create_campaign():
    """Создание новой кампании."""
    try:
        data = request.json
        name = data.get('name', '').strip()
        messages = data.get('messages', [])
        
        if not name:
            return jsonify({'error': 'Название кампании обязательно'}), 400
        
        if not messages:
            return jsonify({'error': 'Добавьте хотя бы одно сообщение'}), 400
        
        # Проверка длины сообщений
        for i, msg in enumerate(messages):
            text = msg.get('text', '').strip()
            if len(text) > 1000:
                return jsonify({'error': f'Сообщение #{i+1} превышает 1000 символов ({len(text)} символов)'}), 400
            if len(text) == 0:
                return jsonify({'error': f'Сообщение #{i+1} пустое'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Создаём кампанию
        cursor.execute('''
            INSERT INTO campaigns (name, created_at, updated_at)
            VALUES (?, datetime('now'), datetime('now'))
        ''', (name,))
        
        campaign_id = cursor.lastrowid
        
        # Добавляем сообщения
        for i, msg in enumerate(messages):
            cursor.execute('''
                INSERT INTO campaign_messages (campaign_id, message_order, text)
                VALUES (?, ?, ?)
            ''', (campaign_id, i + 1, msg.get('text', '').strip()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Создана кампания '{name}' (ID: {campaign_id}) с {len(messages)} сообщениями")
        return jsonify({'success': True, 'campaign_id': campaign_id}), 201
        
    except Exception as e:
        logger.error(f"Ошибка создания кампании: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/campaigns/<int:campaign_id>', methods=['DELETE'])
def api_delete_campaign(campaign_id):
    """Удаление кампании."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Кампания не найдена'}), 404
        
        conn.close()
        logger.info(f"🗑️ Удалена кампания ID: {campaign_id}")
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Ошибка удаления кампании: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API ДЛЯ УПРАВЛЕНИЯ ПРОЧИТАННЫМИ ЧАТАМИ
# ============================================================================

@app.route('/api/search-by-phones', methods=['POST'])
def api_search_by_phones():
    """Поиск чатов по списку телефонных номеров."""
    try:
        data = request.json
        phones_input = data.get('phones', '')
        
        logger.info(f"🔍 === НАЧАЛО ПОИСКА ПО ТЕЛЕФОНАМ ===")
        logger.info(f"📥 Получен input длиной {len(phones_input)} символов")
        logger.info(f"📝 Первые 200 символов: {phones_input[:200]}")
        
        if not phones_input or not phones_input.strip():
            logger.warning("⚠️ Пустой input!")
            return jsonify({'error': 'Не указаны телефоны'}), 400
        
        # Парсим телефоны: разделители - запятая, точка с запятой, перенос строки
        import re
        phones_raw = re.split(r'[,;\n]+', phones_input)
        logger.info(f"📋 Разделено на {len(phones_raw)} частей")
        logger.info(f"📋 Первые 5 частей: {phones_raw[:5]}")
        
        # Очищаем телефоны от пробелов, тире, скобок
        phones_clean = []
        for phone in phones_raw:
            cleaned = re.sub(r'[\s\-\(\)\+]', '', phone.strip())
            if cleaned:
                phones_clean.append(cleaned)
        
        if not phones_clean:
            logger.warning("⚠️ Нет валидных телефонов после очистки!")
            return jsonify({'error': 'Не найдено валидных телефонов'}), 400
        
        logger.info(f"✅ Очищено {len(phones_clean)} телефонов")
        logger.info(f"📞 Первые 10 телефонов: {phones_clean[:10]}")
        logger.info(f"📞 Длины: {[len(p) for p in phones_clean[:10]]}")
        
        # Проверяем, есть ли ВООБЩЕ эти телефоны в БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        logger.info(f"🔎 Проверяем наличие в candidate_phones...")
        placeholders = ','.join('?' * len(phones_clean))
        check_query = f"SELECT phone, COUNT(*) FROM candidate_phones WHERE phone IN ({placeholders}) GROUP BY phone"
        cursor.execute(check_query, phones_clean)
        found_in_db = cursor.fetchall()
        logger.info(f"💾 Найдено в БД: {len(found_in_db)} уникальных телефонов")
        if found_in_db:
            logger.info(f"💾 Примеры из БД: {found_in_db[:5]}")
        
        # Проверяем структуру таблицы applications (ИСПРАВЛЕНО: было candidates)
        cursor.execute("PRAGMA table_info(applications)")
        applications_schema = cursor.fetchall()
        logger.info(f"📋 Схема applications: {[col[1] for col in applications_schema]}")
        
        # Проверяем структуру candidate_phones
        cursor.execute("PRAGMA table_info(candidate_phones)")
        phones_schema = cursor.fetchall()
        logger.info(f"📋 Схема candidate_phones: {[col[1] for col in phones_schema]}")
        
        # Основной запрос (ИСПРАВЛЕНО: ищем в applications, а не candidates)
        query = f'''
            SELECT DISTINCT 
                a.chat_id,
                a.candidate_name,
                cp.phone,
                a.vacancy_id,
                a.created_at,
                a.application_id
            FROM applications a
            JOIN candidate_phones cp ON a.application_id = cp.application_id
            WHERE cp.phone IN ({placeholders})
            ORDER BY a.created_at DESC
        '''
        
        logger.info(f"🔎 Выполняю JOIN запрос...")
        logger.info(f"📝 SQL: {query[:200]}...")
        cursor.execute(query, phones_clean)
        rows = cursor.fetchall()
        logger.info(f"✅ JOIN вернул {len(rows)} строк")
        
        # Если JOIN не дал результатов, проверяем отдельно
        if not rows and found_in_db:
            logger.warning(f"⚠️ Телефоны есть в candidate_phones, но JOIN не дал результатов!")
            
            # Проверяем application_id в candidate_phones
            cursor.execute(f"SELECT DISTINCT application_id FROM candidate_phones WHERE phone IN ({placeholders}) LIMIT 5", phones_clean)
            app_ids_in_phones = cursor.fetchall()
            logger.info(f"🔎 application_id в candidate_phones: {app_ids_in_phones}")
            
            # Проверяем те же application_id в applications (ИСПРАВЛЕНО)
            if app_ids_in_phones:
                app_ids = [row[0] for row in app_ids_in_phones]
                app_placeholders = ','.join('?' * len(app_ids))
                cursor.execute(f"SELECT application_id, candidate_name FROM applications WHERE application_id IN ({app_placeholders})", app_ids)
                matching_applications = cursor.fetchall()
                logger.info(f"🔎 Эти application_id в applications: {matching_applications}")
        
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'chat_id': row[0],
                'candidate_name': row[1],
                'phone': row[2],
                'vacancy_id': row[3],  # ИСПРАВЛЕНО: было vacancy_title
                'created_at': row[4],  # ИСПРАВЛЕНО: было applied_at
                'application_id': row[5]
            })
        
        logger.info(f"🎯 === ИТОГО: {len(results)} чатов найдено ===")
        if results:
            logger.info(f"📋 Первые 3 результата: {results[:3]}")
        
        return jsonify({'success': True, 'results': results, 'debug': {
            'phones_input_length': len(phones_input),
            'phones_parsed': len(phones_clean),
            'phones_found_in_db': len(found_in_db),
            'results_count': len(results)
        }}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка поиска по телефонам: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API ДЛЯ УПРАВЛЕНИЯ ПРОЧИТАННЫМИ ЧАТАМИ
# ============================================================================

@app.route('/api/chats/<chat_id>/mark-read', methods=['POST'])
def api_mark_chat_read(chat_id):
    """Пометить чат как прочитанный."""
    try:
        notes = request.json.get('notes', '') if request.json else ''
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO read_chats (chat_id, marked_read_at, notes)
            VALUES (?, ?, ?)
        ''', (chat_id, datetime.now(), notes))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Чат {chat_id} помечен как прочитанный")
        
        return jsonify({
            'success': True,
            'message': 'Чат помечен как прочитанный',
            'chat_id': chat_id
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка пометки чата как прочитанного: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chats/<chat_id>/unmark-read', methods=['POST'])
def api_unmark_chat_read(chat_id):
    """Снять пометку 'прочитано' с чата."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM read_chats WHERE chat_id = ?', (chat_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ С чата {chat_id} снята пометка 'прочитано'")
        
        return jsonify({
            'success': True,
            'message': 'Пометка снята',
            'chat_id': chat_id
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка снятия пометки: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chats/read-list', methods=['GET'])
def api_get_read_chats():
    """Получить список всех прочитанных чатов."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT chat_id, marked_read_at, notes 
            FROM read_chats 
            ORDER BY marked_read_at DESC
        ''')
        
        read_chats = []
        for row in cursor.fetchall():
            read_chats.append({
                'chat_id': row[0],
                'marked_read_at': row[1],
                'notes': row[2]
            })
        
        conn.close()
        
        return jsonify({
            'read_chats': read_chats,
            'total': len(read_chats)
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения списка прочитанных: {e}")
        return jsonify({'error': str(e)}), 500

def extract_keywords(text, min_length=4):
    """Извлечение ключевых слов из текста (игнорируя регистр и знаки препинания)."""
    import re
    
    # Убираем все знаки препинания и приводим к нижнему регистру
    clean_text = re.sub(r'[^а-яёa-z0-9\s]', ' ', text.lower())
    
    # Разбиваем на слова и фильтруем короткие
    words = [word.strip() for word in clean_text.split() if len(word.strip()) >= min_length]
    
    # Исключаем стоп-слова
    stop_words = {'без', 'для', 'или', 'как', 'что', 'это', 'который', 'которая', 'которое', 
                  'все', 'эта', 'этот', 'чтобы', 'быть', 'мочь', 'весь', 'свой', 'наш', 'ваш'}
    
    keywords = [word for word in words if word not in stop_words]
    
    return list(set(keywords))  # Уникальные слова

def check_keyword_in_history(chat_id, keywords):
    """Проверка, отправлялись ли сообщения с ключевыми словами в этот чат."""
    import re
    
    if not keywords:
        return False, []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем все сообщения, которые были отправлены в этот чат
        cursor.execute('''
            SELECT DISTINCT cm.text, c.name
            FROM chat_campaigns cc
            JOIN campaign_messages cm ON cc.campaign_id = cm.campaign_id
            JOIN campaigns c ON cc.campaign_id = c.id
            WHERE cc.chat_id = ?
        ''', (chat_id,))
        
        sent_messages = cursor.fetchall()
        conn.close()
        
        if not sent_messages:
            return False, []
        
        # Проверяем каждое сообщение на наличие ключевых слов
        found_keywords = []
        
        for message_text, campaign_name in sent_messages:
            # Приводим текст к нижнему регистру и убираем знаки
            clean_msg = re.sub(r'[^а-яёa-z0-9\s]', ' ', message_text.lower())
            clean_camp = re.sub(r'[^а-яёa-z0-9\s]', ' ', campaign_name.lower())
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Ищем слово как отдельное (с пробелами или в начале/конце)
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                
                if re.search(pattern, clean_msg) or re.search(pattern, clean_camp):
                    found_keywords.append((keyword, campaign_name))
        
        return len(found_keywords) > 0, found_keywords
        
    except Exception as e:
        logger.error(f"Ошибка проверки ключевых слов в истории: {e}")
        return False, []

@app.route('/api/campaigns/<int:campaign_id>/send', methods=['POST'])
def api_send_campaign(campaign_id):
    """Отправка кампании в выбранные чаты."""
    import random
    
    try:
        data = request.json
        chat_ids = data.get('chat_ids', [])
        
        if not chat_ids:
            return jsonify({'error': 'Не выбраны чаты'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем название кампании для извлечения ключевых слов
        cursor.execute('SELECT name FROM campaigns WHERE id = ?', (campaign_id,))
        campaign_row = cursor.fetchone()
        
        if not campaign_row:
            conn.close()
            return jsonify({'error': 'Кампания не найдена'}), 404
        
        campaign_name = campaign_row[0]
        keywords = extract_keywords(campaign_name)
        
        logger.info(f"🔑 Кампания '{campaign_name}' - ключевые слова: {keywords}")
        
        # Получаем сообщения кампании
        cursor.execute('''
            SELECT message_order, text
            FROM campaign_messages
            WHERE campaign_id = ?
            ORDER BY message_order ASC
        ''', (campaign_id,))
        
        messages = cursor.fetchall()
        
        if not messages:
            conn.close()
            return jsonify({'error': 'Кампания не содержит сообщений'}), 400
        
        # Исключаем чаты, которым уже отправляли эту кампанию
        cursor.execute('''
            SELECT chat_id FROM chat_campaigns WHERE campaign_id = ?
        ''', (campaign_id,))
        already_sent = set(row[0] for row in cursor.fetchall())
        
        conn.close()
        
        # Фильтруем чаты по двум критериям:
        # 1. Не отправляли эту конкретную кампанию
        # 2. Не отправляли сообщения с теми же ключевыми словами
        chat_ids_to_send = []
        skipped_by_campaign = []
        skipped_by_keyword = []
        
        for cid in chat_ids:
            # Проверка 1: уже отправляли эту кампанию
            if cid in already_sent:
                skipped_by_campaign.append(cid)
                logger.info(f"⏭️ Пропуск {cid}: кампания уже отправлена")
                continue
            
            # Проверка 2: отправляли сообщения с теми же ключевыми словами
            if keywords:
                has_keyword, found = check_keyword_in_history(cid, keywords)
                
                if has_keyword:
                    skipped_by_keyword.append(cid)
                    keyword_info = ', '.join([f"'{kw}' в '{camp}'" for kw, camp in found])
                    logger.warning(f"🚫 Пропуск {cid}: найдены ключевые слова - {keyword_info}")
                    continue
            
            chat_ids_to_send.append(cid)
        
        if not chat_ids_to_send:
            skip_reasons = []
            if skipped_by_campaign:
                skip_reasons.append(f"{len(skipped_by_campaign)} - кампания уже отправлена")
            if skipped_by_keyword:
                skip_reasons.append(f"{len(skipped_by_keyword)} - найдены ключевые слова из истории")
            
            message = 'Все чаты пропущены: ' + ', '.join(skip_reasons)
            
            return jsonify({
                'success': True,
                'sent': 0,
                'failed': 0,
                'skipped_by_campaign': len(skipped_by_campaign),
                'skipped_by_keyword': len(skipped_by_keyword),
                'message': message
            }), 200
        
        # Отправка
        sent = 0
        failed = 0
        
        for chat_id in chat_ids_to_send:
            chat_success = True
            
            # Отправляем сообщения по порядку
            for order, text in messages:
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Используем правильный метод messenger.send_message (v1 API)
                        response = avito_profile.messenger.send_message(chat_id, text)
                        
                        if response.status_code == 200:
                            logger.info(f"✅ Отправлено сообщение {order}/{len(messages)} в чат {chat_id}")
                            break
                        else:
                            logger.error(f"❌ Ошибка отправки в чат {chat_id}: {response.status_code}")
                            if attempt == max_retries - 1:
                                chat_success = False
                                
                    except Exception as e:
                        logger.error(f"❌ Исключение при отправке в чат {chat_id}: {e}")
                        if attempt == max_retries - 1:
                            chat_success = False
                
                # Рандомная задержка между сообщениями (0.4-1.0 сек)
                time.sleep(random.uniform(0.4, 1.0))
            
            # Сохраняем результат
            if chat_success:
                sent += 1
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO chat_campaigns (chat_id, campaign_id, sent_at, status)
                    VALUES (?, ?, datetime('now'), 'sent')
                ''', (chat_id, campaign_id))
                conn.commit()
                conn.close()
            else:
                failed += 1
        
        # Обновляем статус кампании
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE campaigns SET is_sent = TRUE WHERE id = ?', (campaign_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Итого: отправлено={sent}, ошибок={failed}, пропущено_по_кампании={len(skipped_by_campaign)}, пропущено_по_ключевым_словам={len(skipped_by_keyword)}")
        
        return jsonify({
            'success': True,
            'sent': sent,
            'failed': failed,
            'skipped_by_campaign': len(skipped_by_campaign),
            'skipped_by_keyword': len(skipped_by_keyword),
            'keywords_checked': keywords
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка отправки кампании: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/chats/<chat_id>/campaigns', methods=['GET'])
def api_get_chat_campaigns(chat_id):
    """Получение кампаний, отправленных в чат."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.id, c.name, cc.sent_at
            FROM chat_campaigns cc
            JOIN campaigns c ON cc.campaign_id = c.id
            WHERE cc.chat_id = ?
            ORDER BY cc.sent_at DESC
        ''', (chat_id,))
        
        campaigns = []
        for row in cursor.fetchall():
            campaigns.append({
                'id': row[0],
                'name': row[1],
                'sent_at': row[2]
            })
        
        conn.close()
        return jsonify({'campaigns': campaigns}), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения кампаний чата: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Клиент подключился."""
    print('🔌 Клиент подключен')
    emit('connected', {'message': 'Подключено к серверу'})

@socketio.on('disconnect')
def handle_disconnect():
    """Клиент отключился."""
    print('🔌 Клиент отключен')

@socketio.on('request_chats_update')
def handle_chats_update():
    """Запрос на обновление списка чатов."""
    data, status = get_chats_list(limit=50)
    if status == 200:
        emit('chats_updated', data)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("="*80)
    print("🚀 AVITO MESSENGER - ВЕБ-ПРИЛОЖЕНИЕ")
    print("="*80)
    print(f"👤 Profile: {PROFILE_NUMBER}")
    print(f"🔑 Client ID: {CLIENT_ID}")
    print("="*80)
    
    # Инициализация БД
    init_database()
    print("✅ База данных инициализирована")
    
    # Загрузка текста автоответчика из БД
    load_auto_reply_text()
    logger.info("✅ Текст автоответа загружен")
    
    # Инициализация профиля
    logger.info("🔐 Инициализация профиля Авито...")
    if init_avito_profile():
        logger.info("✅ Профиль Авито готов")
    else:
        logger.warning("⚠️ Профиль не инициализирован, используйте /api/init")

    # Запускаем мониторинг автоответчика по умолчанию, если включён
    if auto_reply_active and not monitoring_active:
        monitoring_active = True
        logger.info("🤖 Запуск автоответчика...")
        # Запускаем два потока: для откликов и для сообщений
        thread_messages = threading.Thread(target=monitor_new_messages, daemon=True, name="MonitorMessages")
        thread_applications = threading.Thread(target=monitor_new_applications, daemon=True, name="MonitorApplications")
        thread_messages.start()
        thread_applications.start()
        logger.info("✅ Автоответчик: мониторинг запущен (отклики + сообщения)")
    
    # Запуск сервера
    logger.info("="*60)
    logger.info("🌐 Запуск веб-сервера на http://localhost:5000")
    logger.info("📝 Нажмите Ctrl+C для остановки")
    logger.info("="*60)
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True, log_output=True)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Остановка по Ctrl+C")
    except Exception as e:
        logger.critical(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.critical(traceback.format_exc())
    finally:
        logger.info("👋 Приложение завершено")
