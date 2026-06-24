from telethon import events
import json
from pathlib import Path

dep = []

BLOCKED_CHATS_FILE = Path("blocked_chats.json")

def load_blocked_chats():
    """Загружает список заблокированных чатов"""
    if BLOCKED_CHATS_FILE.is_file():
        with open(BLOCKED_CHATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_blocked_chats(blocked_chats):
    """Сохраняет список заблокированных чатов"""
    with open(BLOCKED_CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(blocked_chats, f, ensure_ascii=False, indent=2)

async def run(client, restart_userbot):
    
    @client.on(events.NewMessage(outgoing=True))
    async def block_chat(event):
        if event.message.text == '-block':
            chat_id = event.chat_id
            blocked_chats = load_blocked_chats()
            
            if chat_id not in blocked_chats:
                blocked_chats.append(chat_id)
                save_blocked_chats(blocked_chats)
                await event.edit(f"🚫 Чат заблокирован")
            else:
                await event.edit(f"ℹ️ Чат уже в блоклисте")
    
    @client.on(events.NewMessage(outgoing=True))
    async def unblock_chat(event):
        if event.message.text == '-unblock':
            chat_id = event.chat_id
            blocked_chats = load_blocked_chats()
            
            if chat_id in blocked_chats:
                blocked_chats.remove(chat_id)
                save_blocked_chats(blocked_chats)
                await event.edit(f"✅ Чат разблокирован")
            else:
                await event.edit(f"ℹ️ Чат не был заблокирован")
    
    @client.on(events.NewMessage(outgoing=True))
    async def list_blocked(event):
        if event.message.text == '-blocked':
            blocked_chats = load_blocked_chats()
            
            if blocked_chats:
                chats_list = "\n".join([f"• {chat_id}" for chat_id in blocked_chats])
                await event.edit(f"🚫 Заблокированные чаты:\n{chats_list}")
            else:
                await event.edit(f"ℹ️ Нет заблокированных чатов")
    
    @client.on(events.NewMessage(incoming=True))
    async def auto_delete_incoming(event):
        """Автоматически удаляет входящие сообщения в заблокированных чатах"""
        chat_id = event.chat_id
        blocked_chats = load_blocked_chats()
        
        if chat_id in blocked_chats:
            try:
                await event.delete()
            except:
                pass  # Не удалось удалить сообщение
    
    @client.on(events.NewMessage(outgoing=True))
    async def auto_delete_outgoing(event):
        """Автоматически удаляет исходящие сообщения в заблокированных чатах"""
        chat_id = event.chat_id
        blocked_chats = load_blocked_chats()
        
        if chat_id in blocked_chats:
            try:
                await event.delete()
            except:
                pass  # Не удалось удалить сообщение
