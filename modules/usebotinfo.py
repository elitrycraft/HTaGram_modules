from telethon import events
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dep = []

async def run(client, restart_userbot):
    logger.info("Userbot Info module started")
    
    @client.on(events.NewMessage(outgoing=True))
    async def userbot_info(event):
        if event.message.text == '-info':
            try:
                # Получаем информацию о боте/юзерботе
                me = await client.get_me()
                
                # Диалоги (количество чатов)
                dialogs = await client.get_dialogs()
                dialogs_count = len(dialogs)
                
                # Время работы (если есть переменная старта)
                start_time = getattr(restart_userbot, 'start_time', time.time())
                uptime_seconds = time.time() - start_time
                uptime = format_uptime(uptime_seconds)
                
                # Формируем вывод
                output = f"""
**📱 USERBOT INFO**
├ Name: HTaGram

**👤 Account:**
├ ID: `{me.id}`
├ Username: @{me.username if me.username else 'None'}
├ First Name: {me.first_name}
├ Last Name: {me.last_name if me.last_name else '-'}
├ Premium: {'✅ Yes' if me.premium else '❌ No'}
├ Verified: {'✅ Yes' if me.verified else '❌ No'}

**💬 Stats:**
├ Dialogs: `{dialogs_count}`
├ Chats: `{len([d for d in dialogs if d.is_group])}`
├ Channels: `{len([d for d in dialogs if d.is_channel])}`
├ Users: `{len([d for d in dialogs if d.is_user])}`

**⏱️ Uptime:**
└ `{uptime}`

**🔧 System:**
├ API ID: `HIDEN`
└ Bot: {'✅ Yes' if me.bot else '❌ No (Userbot)'}
"""
                
                await event.edit(output, parse_mode='markdown')
                
            except Exception as e:
                await event.edit(f"**❌ Error:**\n```\n{str(e)}\n```")
                logger.error(f"Error in userbot_info: {e}")

def format_uptime(seconds):
    """Форматирование времени работы"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {secs}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
