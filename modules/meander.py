from telethon import events
import time
import random
import aiohttp
import json
from datetime import datetime
import re

# ===== КОНФИГУРАЦИЯ =====
MEANDER_API = "https://backend.meander.sbs/quests"
MEANDER_SHARE = "https://backend.meander.sbs/share/quest/"
CACHE_FILE = "quests_cache.json"
CACHE_TIME = 300  # 5 минут кеширования

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

def find_quest_by_id_or_title(query, quests):
    """Ищет квест по ID или названию"""
    for q in quests:
        if q.get('id') == query:
            return q
        if query.lower() in q.get('title', '').lower():
            return q
    return None

def format_quest_caption(quest):
    """Форматирует описание квеста для подписи к фото"""
    description = quest.get('description', 'Нет описания')
    # Обрезаем описание до 400 символов
    if len(description) > 400:
        description = description[:400] + '...'
    
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
    """Отправляет квест с фото и описанием (редактирует исходное сообщение)"""
    if not quest:
        await event.edit("❌ Квест не найден.")
        return
    
    # Получаем URL превью
    preview_url = quest.get('preview_image_url')
    caption = format_quest_caption(quest)
    
    # Удаляем исходное сообщение (если это команда)
    # И отправляем новое с фото
    if preview_url:
        try:
            # Скачиваем изображение
            async with aiohttp.ClientSession() as session:
                async with session.get(preview_url) as resp:
                    if resp.status == 200:
                        # Удаляем команду
                        await event.delete()
                        # Отправляем фото с подписью
                        await event.respond(
                            file=await resp.read(),
                            caption=caption,
                            parse_mode='markdown'
                        )
                        return
        except Exception as e:
            print(f"[ERROR] Не удалось загрузить фото: {e}")
    
    # Если фото не загрузилось, отправляем текстовое сообщение
    await event.edit(caption)

# ===== ПЛАГИН =====

async def run(client, restart_userbot):
    """Запуск плагина"""
    
    # === ОБРАБОТЧИК ССЫЛОК ===
    @client.on(events.NewMessage(outgoing=True, pattern=r'https://backend\.meander\.sbs/share/quest/[a-f0-9-]+'))
    async def handle_quest_link(event):
        """Обрабатывает ссылки на квесты: подтягивает описание и фото"""
        # Извлекаем ID из ссылки
        match = re.search(r'/share/quest/([a-f0-9-]+)', event.text)
        if not match:
            return
        
        quest_id = match.group(1)
        
        # Получаем квесты
        quests = get_cached_quests()
        if not quests:
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты.")
                return
        
        # Ищем квест
        quest = find_quest_by_id_or_title(quest_id, quests)
        if not quest:
            await event.edit(f"❌ Квест не найден: {quest_id}")
            return
        
        # Отправляем с фото
        await send_quest_with_photo(event, quest)
    
    # === КОМАНДА: -quest ===
    @client.on(events.NewMessage(outgoing=True, pattern=r'^-quest$|^-quest random$'))
    async def random_quest(event):
        """Показывает случайный квест"""
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
        
        # Отправляем с фото
        await send_quest_with_photo(event, quest)
    
    # === КОМАНДА: -quests ===
    @client.on(events.NewMessage(outgoing=True, pattern=r'^-quests(?:\s+(\d+))?$'))
    async def list_quests(event):
        """Показывает список квестов с пагинацией"""
        page = 1
        if event.pattern_match and event.pattern_match.group(1):
            page = int(event.pattern_match.group(1))
        
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
    @client.on(events.NewMessage(outgoing=True, pattern=r'^-quest info (.+)$'))
    async def quest_info(event):
        """Показывает информацию о конкретном квесте"""
        query = event.pattern_match.group(1)
        
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
        
        await send_quest_with_photo(event, quest)
    
    # === КОМАНДА: -quest stats ===
    @client.on(events.NewMessage(outgoing=True, pattern=r'^-quest stats$'))
    async def quest_stats(event):
        """Показывает статистику по квестам"""
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
                return
        
        total = len(quests)
        genres = {}
        avg_rating = 0
        
        for q in quests:
            for g in q.get('genres', []):
                genres[g] = genres.get(g, 0) + 1
            rating = q.get('average_rating')
            if rating:
                avg_rating += float(rating)
        
        avg_rating = avg_rating / total if total > 0 else 0
        top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:5]
        top_genres_text = '\n'.join([f"  • {g}: {c}" for g, c in top_genres])
        
        text = f"""
📊 **Статистика квестов Meander**

📌 Всего квестов: {total}
⭐ Средний рейтинг: {avg_rating:.1f}

🏷️ **Топ-5 жанров:**
{top_genres_text}

📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """.strip()
        
        await event.edit(text)
    
    # === КОМАНДА: -quest top ===
    @client.on(events.NewMessage(outgoing=True, pattern=r'^-quest top$'))
    async def quest_top(event):
        """Показывает топ-5 квестов по рейтингу"""
        quests = get_cached_quests()
        if not quests:
            await event.edit("🔄 Загрузка квестов...")
            quests = await fetch_quests()
            if not quests:
                await event.edit("❌ Не удалось загрузить квесты. Попробуй позже.")
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
            text += f"{i}. **{title}** — {author} ⭐{rating}\n"
        
        await event.edit(text)
    
    # === КОМАНДА: -quest refresh ===
    @client.on(events.NewMessage(outgoing=True, pattern=r'^-quest refresh$'))
    async def refresh_cache(event):
        """Принудительное обновление кеша"""
        await event.edit("🔄 Обновление кеша квестов...")
        quests = await fetch_quests()
        if quests:
            await event.edit(f"✅ Кеш обновлён! Доступно {len(quests)} квестов.")
        else:
            await event.edit("❌ Ошибка обновления кеша.")
    
    # === КОМАНДА: -quest help ===
    @client.on(events.NewMessage(outgoing=True, pattern=r'^-quest help$'))
    async def quest_help(event):
        """Показывает справку по командам"""
        text = """
🎮 **Meander Quest Bot**

**Команды:**
`-quest` — случайный квест
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
    await fetch_quests()
