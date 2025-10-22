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

# Настройка логирования в файл
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('messenger_app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Добавляем путь к AvitoAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'AvitoAPI', 'src'))

from AvitoAPI.Profile import Profile

app = Flask(__name__)
app.secret_key = 'avito-messenger-secret-key-2025-very-secure'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 час
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

PROFILE_NUMBER = "316615541"
CLIENT_ID = "Dm4ruLMEr9MFsV72dN95"
CLIENT_SECRET = "f73lNoAJLzuqwoGtVaMnByhQfSlwcyIN_m7wyOeT"
AUTO_REPLY_TEXT = 'Спасибо, что откликнулись. Обычно мы отвечаем в течение 24 часов. Если мы не свяжемся с вами за это время, напишите, пожалуйста на whatsapp на номер 79890443897.'

# Глобальные переменные
avito_profile = None
auto_reply_active = False
monitoring_thread = None
monitoring_active = False

# ============================================================================
# БАЗА ДАННЫХ
# ============================================================================

def init_database():
    """Инициализация базы данных."""
    conn = sqlite3.connect('messenger.db')
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
    
    conn.commit()
    conn.close()

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
                conn = sqlite3.connect('messenger.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO messages_status (chat_id, sent_at, is_auto_reply, message_text)
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, datetime.now(), False, message_text))
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
            
            # Сохраняем в БД
            conn = sqlite3.connect('messenger.db')
            cursor = conn.cursor()
            
            for app in applications:
                applicant = app.get('applicant', {})
                applicant_data = applicant.get('data', {})
                candidate_name = applicant_data.get('name', 'Неизвестно')
                
                contacts = app.get('contacts', {})
                phones = contacts.get('phones', [])
                candidate_phone = phones[0].get('value', '') if phones else ''
                chat_id = contacts.get('chat', {}).get('value', '')
                
                cursor.execute('''
                    INSERT OR REPLACE INTO applications 
                    (application_id, vacancy_id, candidate_name, candidate_phone, chat_id, is_viewed, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    app.get('id'),
                    app.get('vacancy_id'),
                    candidate_name,
                    candidate_phone,
                    chat_id,
                    app.get('is_viewed', False),
                    app.get('created_at'),
                    app.get('updated_at')
                ))
            
            conn.commit()
            conn.close()
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
                        conn = sqlite3.connect('messenger.db')
                        cursor = conn.cursor()
                        cursor.execute('SELECT id FROM auto_replies WHERE chat_id = ?', (chat_id,))
                        existing = cursor.fetchone()
                        conn.close()
                        
                        if not existing:
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
                                
                                conn = sqlite3.connect('messenger.db')
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
            
            time.sleep(10)  # Проверяем каждые 10 секунд
            
        except Exception as e:
            print(f"❌ Ошибка в мониторинге: {e}")
            time.sleep(10)
    
    print("🛑 Мониторинг остановлен")

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Главная страница."""
    return render_template('index.html', profile_number=PROFILE_NUMBER)

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

@app.route('/api/chats/<chat_id>/messages', methods=['GET'])
def api_chat_messages(chat_id):
    """Получение сообщений из чата."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    data, status = get_chat_messages(chat_id, limit=limit, offset=offset)
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

@app.route('/api/applications/stats', methods=['GET'])
def api_applications_stats():
    """Статистика по откликам из БД."""
    conn = sqlite3.connect('messenger.db')
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
            monitoring_thread = threading.Thread(target=monitor_new_messages, daemon=True)
            monitoring_thread.start()
        
        return jsonify({"success": True, "active": True, "message": "Автоответчик включен"})
    
    elif action == 'stop' or (action == 'toggle' and auto_reply_active):
        auto_reply_active = False
        monitoring_active = False
        
        return jsonify({"success": True, "active": False, "message": "Автоответчик выключен"})
    
    return jsonify({"success": True, "active": auto_reply_active})

@app.route('/api/auto-reply/status', methods=['GET'])
def api_auto_reply_status():
    """Статус автоответчика."""
    conn = sqlite3.connect('messenger.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM auto_replies')
    total_sent = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({
        "active": auto_reply_active,
        "monitoring": monitoring_active,
        "total_sent": total_sent
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
        
        # Анализируем каждый чат
        for chat in chats:
            chat_id = chat.get('id', 'N/A')
            context = chat.get('context', {}).get('value', {})
            user_name = context.get('user_name', 'Неизвестно')
            last_message = chat.get('last_message', {})
            
            if not last_message:
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
            elif is_system:
                metrics['not_wrote'].append({
                    'chat_id': chat_id,
                    'user_name': user_name,
                    'reason': 'Системное сообщение'
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
            elif direction == 'in' and not is_system:
                metrics['waiting_reply'].append({
                    'chat_id': chat_id,
                    'user_name': user_name
                })
        
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
    
    # Инициализация профиля
    if init_avito_profile():
        print("✅ Профиль Авито готов")
    else:
        print("⚠️ Профиль не инициализирован, используйте /api/init")
    
    # Запуск сервера
    print("\n🌐 Запуск веб-сервера на http://localhost:5000")
    print("📝 Нажмите Ctrl+C для остановки\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
