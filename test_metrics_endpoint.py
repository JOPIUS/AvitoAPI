"""
Тест endpoint /api/chats/metrics
"""
import requests
import json

try:
    print("🧪 Тестирование GET /api/chats/metrics")
    print("=" * 60)
    
    response = requests.get('http://localhost:5000/api/chats/metrics')
    
    print(f"📊 Status Code: {response.status_code}")
    print("=" * 60)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ УСПЕШНЫЙ ОТВЕТ:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Вывод метрик
        print("\n" + "=" * 60)
        print("📈 МЕТРИКИ ЧАТОВ:")
        print("=" * 60)
        metrics = data.get('metrics', {})
        print(f"1️⃣ Написали\\Прочитал\\Не ответил: {metrics.get('wrote_read_no_reply', 0)}")
        print(f"2️⃣ Написали\\Не читал: {metrics.get('wrote_unread', 0)}")
        print(f"3️⃣ Не писали: {metrics.get('not_wrote', 0)}")
        print(f"4️⃣ Ждут ответ: {metrics.get('waiting_reply', 0)}")
        print(f"5️⃣ Отправлен автоответ: {metrics.get('auto_reply_sent', 0)}")
        print(f"📊 Всего чатов: {data.get('total_chats', 0)}")
        
        # Проверка суммы
        total_categorized = sum(metrics.values())
        total_chats = data.get('total_chats', 0)
        print(f"\n✅ Категоризовано: {total_categorized}/{total_chats}")
        
        if total_categorized == total_chats:
            print("✅ ВСЕ ЧАТЫ КОРРЕКТНО РАСПРЕДЕЛЕНЫ!")
        else:
            print(f"⚠️ Несоответствие: {total_chats - total_categorized} чатов не распределены")
    else:
        print(f"❌ ОШИБКА: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ ОШИБКА: Сервер не запущен на http://localhost:5000")
    print("💡 Запустите: python messenger_app.py")
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
