from telethon import events
import time
import random
import aiohttp
import json
from datetime import datetime
import re
import asyncio

# ===== КОНФИГУРАЦИЯ =====
MEANDER_API = "https://backend.meander.sbs/quests"
MEANDER_SHARE = "https://backend.meander.sbs/share/quest/"
CACHE_TIME = 300  # 5 минут кеширования

quest_cache = {
    'data': [],
    'last_update': 0
}

# ===== ФУНКЦИИ =====

async def fetch_quests():
    """Получает список квестов из API с повторными попытками"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(MEANDER_API) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        quest_cache['data'] = data
                        quest_cache['last_update'] = time.time()
                        return data
                    else:
                        print(f"[ERROR] API вернул статус {resp.status}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return None
        except Exception as e:
            print(f"[ERROR] Попытка {attempt+1}/{max_retries} не удалась: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            return None
    return None

def get_cached_quests():
    """Возвращает кешированные квесты или загружает новые"""
    if time.time() - quest_cache['last_update'] > CACHE_TIME or not quest_cache['data']:
        return None
    return quest_cache['data']

def find_quest_by_id_or_title(query, quests):
    """Ищет квест по ID или названию"""
    if not quests:
        return None
    for q in quests:
        if q.get('id') == query:
            return q
        if query.lower() in q.get('title', '').lower():
            return q
    return None

def format_quest_caption(quest):
    """Форматирует описание квеста для подписи к фото"""
    description = quest.get('description', 'Нет описания')
    if len(description) > 500:
        description = description[:500] + '...'
    
    genres = ', '.join(quest.get('genres', ['Неизвестно']))
    rating = quest.get('average_rating', 'Нет')
    
    return f"""
🎮 **{quest.get('title', 'Без названия')}**

📖 {description}

👤 Автор: {quest.get('author_name', 'Неизвестен')}
📂 Жанр: {genres}
⭐ Рейтинг: {rating}
📥 Скачиваний: {quest.get('downloads_count', 0)}
❤️ Лайков: {quest.get('like_count', 0)} | 👎 Дизлайков: {quest.get('dislike_count', 0)}

🔗 [Ссылка на квест]({quest.get('download_url', '#')})
🌐 [Поделиться]({MEANDER_SHARE}{quest.get('id', '')})
    """.strip()

def format_quest_short(quest, index):
    """Краткий формат квеста для списка"""
    return f"{index}. **{quest.get('title', 'Без названия')}** — {quest.get('author_name', 'Неизвестен')} ⭐{quest.get('average_rating', '?')}"

async def send_quest_with_photo(event, quest):
    """Отправляет квест с фото и описанием (удаляет команду, отправляет новое сообщение)"""
    if not quest:
        await event.edit("❌ Квест не найден.")
        return
    
    preview_url = quest.get('preview_image_url')
    caption = format_quest_caption(quest)
    
    try:
        # Удаляем исходное сообщение с командой
        await event.delete()
    except:
        pass
    
    # Отправляем новое сообщение с фото
    if preview_url:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(preview_url) as resp:
                    if resp.status == 200:
                        await event.respond(
                            file=await resp.read(),
                            caption=caption,
                            parse_mode='markdown'
                        )
                        return
        except Exception as e:
            print(f"[ERROR] Не удалось загрузить фото: {e}")
    
    # Если фото не загрузилось, отправляем текстовое сообщение
    await event.respond(caption, parse_mode='markdown')

async def safe_send_quest(event, quest):
    """Безопасная отправка квеста с повторной попыткой при ошибке"""
    try:
        await send_quest_with_photo(event, quest)
    except Exception as e:
        print(f"[ERROR] Ошибка при отправке квеста: {e}")
        await asyncio.sleep(1)
        try:
            await send_quest_with_photo(event, quest)
        except Exception as e2:
            print(f"[ERROR] Вторая попытка также не удалась: {e2}")
            await event.respond("❌ Не удалось отправить квест. Попробуй позже.")

# ===== ПЛАГИН =====

async def run(client, restart_userbot):
    """Запуск плагина"""
    
    # === ОБРАБОТЧИК ССЫЛОК ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'https://backend\.meander\.sbs/share/quest/[a-f0-9-]+')))
    async def handle_quest_link(event):
        """Обрабатывает ссылки на квесты: подтягивает описание и фото"""
        match = re.search(r'/share/quest/([a-f0-9-]+)', event.text)
        if not match:
            return
        
        quest_id = match.group(1)
        
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        quest = find_quest_by_id_or_title(quest_id, quests)
        if not quest:
            await event.edit(f"❌ Квест не найден: {quest_id}")
            return
        
        await safe_send_quest(event, quest)
    
    # === КОМАНДА: -quest ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'^-quest$|^-quest random$')))
    async def random_quest(event):
        """Показывает случайный квест"""
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
        
        quest = random.choice(quests)
        await safe_send_quest(event, quest)
    
    # === КОМАНДА: -quests ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'^-quests(?:\s+(\d+))?$')))
    async def list_quests(event):
        """Показывает список квестов с пагинацией"""
        page = 1
        match = re.search(r'^-quests(?:\s+(\d+))?$', event.text)
        if match and match.group(1):
            try:
                page = int(match.group(1))
            except:
                page = 1
        
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
        
        per_page = 10
        total_pages = (len(quests) + per_page - 1) // per_page
        
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, len(quests))
        quests_page = quests[start_idx:end_idx]
        
        text = f"📚 **Квесты Meander** (стр. {page}/{total_pages})\n\n"
        text += "\n".join([format_quest_short(q, i+start_idx+1) for i, q in enumerate(quests_page)])
        text += f"\n\n📌 Используй `-quests {page+1}` для следующей страницы"
        text += f"\n📌 Используй `-quest info <название>` для деталей"
        
        await event.edit(text)
    
    # === КОМАНДА: -quest info ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'^-quest info (.+)$')))
    async def quest_info(event):
        """Показывает информацию о конкретном квесте"""
        match = re.search(r'^-quest info (.+)$', event.text)
        if not match:
            return
        query = match.group(1).strip()
        
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        quest = find_quest_by_id_or_title(query, quests)
        if not quest:
            await event.edit(f"❌ Квест не найден: {query}")
            return
        
        await safe_send_quest(event, quest)
    
    # === КОМАНДА: -quest stats ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'^-quest stats$')))
    async def quest_stats(event):
        """Показывает статистику по квестам"""
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
        
        total = len(quests)
        genres = {}
        avg_rating = 0
        total_downloads = 0
        
        for q in quests:
            for g in q.get('genres', []):
                genres[g] = genres.get(g, 0) + 1
            rating = q.get('average_rating')
            if rating:
                avg_rating += float(rating)
            total_downloads += q.get('downloads_count', 0)
        
        avg_rating = avg_rating / total if total > 0 else 0
        top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]
        top_genres_text = '\n'.join([f"  • {g}: {c}" for g, c in top_genres])
        
        text = f"""
📊 **Статистика квестов Meander**

📌 Всего квестов: {total}
⭐ Средний рейтинг: {avg_rating:.1f}
📥 Всего скачиваний: {total_downloads}

🏷️ **Топ-5 жанров:**
{top_genres_text}

📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """.strip()
        
        await event.edit(text)
    
    # === КОМАНДА: -quest top ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'^-quest top$')))
    async def quest_top(event):
        """Показывает топ-5 квестов по рейтингу"""
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
        
        sorted_quests = sorted(
            [q for q in quests if q.get('average_rating')],
            key=lambda x: float(x['average_rating']),
            reverse=True
        )[:5]
        
        text = "🏆 **Топ-5 квестов**\n\n"
        for i, q in enumerate(sorted_quests, 1):
            rating = q.get('average_rating', 'Нет')
            title = q.get('title', 'Без названия')
            author = q.get('author_name', 'Неизвестен')
            downloads = q.get('downloads_count', 0)
            text += f"{i}. **{title}** — {author}\n   ⭐{rating} | 📥{downloads}\n"
        
        await event.edit(text)
    
    # === КОМАНДА: -quest refresh ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'^-quest refresh$')))
    async def refresh_cache(event):
        """Принудительное обновление кеша"""
        await event.edit("🔄 Обновление кеша квестов...")
        quests = await fetch_quests()
        if quests:
            await event.edit(f"✅ Кеш обновлён! Доступно {len(quests)} квестов.")
        else:
            await event.edit("❌ Ошибка обновления кеша.")
    
    # === КОМАНДА: -quest help ===
    @client.on(events.NewMessage(outgoing=True, pattern=re.compile(r'^-quest help$')))
    async def quest_help(event):
        """Показывает справку по командам"""
        text = """
🎮 **Meander Quest Bot**

**Команды:**
`-quest` — случайный квест с фото
`-quests [страница]` — список квестов
`-quest info <название>` — детали квеста
`-quest stats` — статистика
`-quest top` — топ-5 квестов
`-quest refresh` — обновить кеш
`-quest help` — справка

**Ссылки:**
Просто отправь ссылку на квест Meander — бот сам подтянет описание и фото!

Пример: `https://backend.meander.sbs/share/quest/b229a484-3cf8-408f-9ec1-847f78771b8a`
        """.strip()
        await event.edit(text)
    
    # Автоматическая загрузка кеша при старте
    print("🔄 Загрузка квестов в кеш...")
    await fetch_quests()
    print(f"✅ Загружено {len(quest_cache['data'])} квестов")
