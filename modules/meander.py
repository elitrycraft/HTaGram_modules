from telethon import events
import time
import random
import aiohttp
import json
from datetime import datetime

# ===== КОНФИГУРАЦИЯ =====
MEANDER_API = "https://backend.meander.sbs/quests"
CACHE_FILE = "quests_cache.json"
CACHE_TIME = 300  # 5 минут кеширования
deps = ["aiohttp"]

quest_cache = {
    'data': [],
    'last_update': 0
}

# ===== ФУНКЦИИ =====

async def fetch_quests():
    """Получает список квестов из API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(MEANDER_API) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    quest_cache['data'] = data
                    quest_cache['last_update'] = time.time()
                    return data
                else:
                    return None
    except Exception as e:
        print(f"[ERROR] Не удалось получить квесты: {e}")
        return None

def get_cached_quests():
    """Возвращает кешированные квесты или загружает новые"""
    if time.time() - quest_cache['last_update'] > CACHE_TIME:
        return None
    return quest_cache['data']

def format_quest(quest):
    """Форматирует квест для вывода в Telegram"""
    return f"""
🎮 **{quest.get('title', 'Без названия')}**
👤 Автор: {quest.get('author_name', 'Неизвестен')}
📂 Жанр: {', '.join(quest.get('genres', ['Неизвестно']))}
⭐ Рейтинг: {quest.get('average_rating', 'Нет')}
📥 Скачиваний: {quest.get('downloads_count', 0)}
❤️ Лайков: {quest.get('like_count', 0)}
👎 Дизлайков: {quest.get('dislike_count', 0)}
📖 Описание: {quest.get('description', 'Нет описания')[:200]}...

🔗 Скачать: {quest.get('download_url', 'Недоступно')}
🖼️ Превью: {quest.get('preview_image_url', 'Нет')}
    """.strip()

def format_quest_short(quest):
    """Краткий формат квеста для списка"""
    return f"🎮 {quest.get('title', 'Без названия')} — {quest.get('author_name', 'Неизвестен')} ⭐{quest.get('average_rating', '?')}"

def format_stats(quests):
    """Статистика по квестам"""
    total = len(quests)
    genres = {}
    avg_rating = 0
    
    for q in quests:
        for g in q.get('genres', []):
            genres[g] = genres.get(g, 0) + 1
        avg_rating += float(q.get('average_rating', 0) or 0)
    
    avg_rating = avg_rating / total if total > 0 else 0
    
    top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]
    top_genres_text = '\n'.join([f"  • {g}: {c}" for g, c in top_genres])
    
    return f"""
📊 **Статистика квестов Meander**

📌 Всего квестов: {total}
⭐ Средний рейтинг: {avg_rating:.1f}

🏷️ **Топ-5 жанров:**
{top_genres_text}

📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
    """.strip()

async def run(client, restart_userbot):
    """Запуск плагина"""
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.quest$|^\.quest random$'))
    async def random_quest(event):
        """Показывает случайный квест"""
        start = time.time()
        
        # Получаем квесты
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        if not quests:
            await event.edit("❌ Нет доступных квестов.")
            return
        
        # Выбираем случайный
        quest = random.choice(quests)
        
        # Форматируем
        text = format_quest(quest)
        end = time.time()
        
        await event.edit(f"{text}\n\n⏱️ {round((end - start) * 1000)} мс")
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.quests(?:\s+(\d+))?$'))
    async def list_quests(event):
        """Показывает список квестов с пагинацией"""
        # Получаем номер страницы
        page = 1
        if event.pattern_match and event.pattern_match.group(1):
            page = int(event.pattern_match.group(1))
        
        # Получаем квесты
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        if not quests:
            await event.edit("❌ Нет доступных квестов.")
            return
        
        # Пагинация (по 10 квестов на страницу)
        per_page = 10
        total_pages = (len(quests) + per_page - 1) // per_page
        
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, len(quests))
        
        quests_page = quests[start_idx:end_idx]
        
        # Форматируем список
        text = f"📚 **Квесты Meander** (стр. {page}/{total_pages})\n\n"
        text += "\n".join([f"{i+start_idx+1}. {format_quest_short(q)}" for i, q in enumerate(quests_page)])
        text += f"\n\n📌 Используй `.quests {page+1}` для следующей страницы"
        text += f"\n📌 Используй `.quest info <название>` для деталей"
        
        await event.edit(text)
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.quest info (.+)$'))
    async def quest_info(event):
        """Показывает информацию о конкретном квесте по ID или названию"""
        query = event.pattern_match.group(1)
        
        # Получаем квесты
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        # Ищем квест по ID или названию
        found = None
        for q in quests:
            if q.get('id') == query or query.lower() in q.get('title', '').lower():
                found = q
                break
        
        if not found:
            await event.edit(f"❌ Квест не найден: {query}")
            return
        
        text = format_quest(found)
        await event.edit(text)
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.quest stats$'))
    async def quest_stats(event):
        """Показывает статистику по квестам"""
        # Получаем квесты
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        text = format_stats(quests)
        await event.edit(text)
    
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.quest top$'))
    async def quest_top(event):
        """Показывает топ квестов по рейтингу"""
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        # Сортируем по рейтингу
        sorted_quests = sorted(
            [q for q in quests if q.get('average_rating')],
            key=lambda x: float(x['average_rating']),
            reverse=True
        )[:5]
        
        text = "🏆 **Топ-5 квестов**\n\n"
        for i, q in enumerate(sorted_quests, 1):
            rating = q.get('average_rating', 'Нет')
            text += f"{i}. {q.get('title', 'Без названия')} — ⭐{rating}\n"
        
        await event.edit(text)
    
    # Автоматическая загрузка кеша при старте
    await fetch_quests()
    
    # Сохраняем кеш каждые 5 минут
    @client.on(events.NewMessage(outgoing=True, pattern=r'^\.quest refresh$'))
    async def refresh_cache(event):
        """Принудительное обновление кеша"""
        await event.edit("🔄 Обновление кеша квестов...")
        quests = await fetch_quests()
        if quests:
            await event.edit(f"✅ Кеш обновлён! Доступно {len(quests)} квестов.")
        else:
            await event.edit("❌ Ошибка обновления кеша.")
