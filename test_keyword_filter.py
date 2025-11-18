"""
Тест фильтрации по ключевым словам в рассылках
"""
import sqlite3
import re

def extract_keywords(text, min_length=4):
    """Извлечение ключевых слов из текста (игнорируя регистр и знаки препинания)."""
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
    if not keywords:
        return False, []
    
    conn = sqlite3.connect('messenger.db', timeout=5)
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

print("="*70)
print("🧪 ТЕСТ ФИЛЬТРАЦИИ ПО КЛЮЧЕВЫМ СЛОВАМ")
print("="*70)
print()

# ТЕСТ 1: Извлечение ключевых слов
print("📋 ТЕСТ 1: Извлечение ключевых слов")
print("-"*70)

test_campaigns = [
    "ПОЛАТИ БЕЗ ИЗОЛИРОВКИ ПЛЮС ПАКЕТ (12 сообщений)",
    "\"Полати\" - строительная компания",
    "Работа в компании ПОЛАТИ",
    "Обычная рассылка без ключевых слов",
]

for camp_name in test_campaigns:
    keywords = extract_keywords(camp_name)
    print(f"  '{camp_name}'")
    print(f"    → Ключевые слова: {keywords}")
print()

# ТЕСТ 2: Проверка истории
print("📋 ТЕСТ 2: Проверка истории сообщений")
print("-"*70)

conn = sqlite3.connect('messenger.db', timeout=5)
cursor = conn.cursor()

# Берём первые 10 чатов, которым уже отправляли кампании
cursor.execute('''
    SELECT DISTINCT cc.chat_id, c.name
    FROM chat_campaigns cc
    JOIN campaigns c ON cc.campaign_id = c.id
    LIMIT 10
''')

test_chats = cursor.fetchall()
conn.close()

if test_chats:
    print(f"  Проверяем {len(test_chats)} чатов с историей...\n")
    
    # Проверяем с ключевым словом "полати"
    test_keywords = ['полати', 'изолировки', 'пакет']
    
    for chat_id, last_campaign in test_chats:
        print(f"  Чат: {chat_id}")
        print(f"    Последняя кампания: '{last_campaign}'")
        
        for keyword in test_keywords:
            has_keyword, found = check_keyword_in_history(chat_id, [keyword])
            
            if has_keyword:
                print(f"    ❌ Ключевое слово '{keyword}' найдено!")
                for kw, camp in found:
                    print(f"       - в кампании '{camp}'")
            else:
                print(f"    ✅ Ключевого слова '{keyword}' нет в истории")
        
        print()
else:
    print("  ⚠️ Нет чатов с историей для тестирования")
    print()

# ТЕСТ 3: Симуляция фильтрации
print("📋 ТЕСТ 3: Симуляция фильтрации рассылки")
print("-"*70)

new_campaign_name = "ПОЛАТИ БЕЗ ИЗОЛИРОВКИ ПЛЮС ПАКЕТ (12 сообщений)"
keywords = extract_keywords(new_campaign_name)

print(f"  Новая кампания: '{new_campaign_name}'")
print(f"  Ключевые слова: {keywords}")
print()

conn = sqlite3.connect('messenger.db', timeout=5)
cursor = conn.cursor()

# Берём 20 случайных чатов
cursor.execute('SELECT DISTINCT chat_id FROM applications LIMIT 20')
all_chats = [row[0] for row in cursor.fetchall() if row[0]]
conn.close()

print(f"  Проверяем {len(all_chats)} чатов...")
print()

allowed = []
blocked_by_keyword = []

for chat_id in all_chats:
    has_keyword, found = check_keyword_in_history(chat_id, keywords)
    
    if has_keyword:
        blocked_by_keyword.append(chat_id)
        keyword_info = ', '.join([f"'{kw}' в '{camp}'" for kw, camp in found])
        print(f"  🚫 {chat_id}: ПРОПУСТИТЬ - {keyword_info}")
    else:
        allowed.append(chat_id)
        print(f"  ✅ {chat_id}: РАЗРЕШЕНО")

print()
print("="*70)
print("📊 ИТОГО:")
print(f"  ✅ Разрешено: {len(allowed)} чатов")
print(f"  🚫 Заблокировано: {len(blocked_by_keyword)} чатов (по ключевым словам)")
print("="*70)
