from telethon import events
import asyncio

dep = []

async def run(client, restart_userbot):
    @client.on(events.NewMessage(outgoing=True))
    async def spam_command(event):
        if event.message.text.startswith('-spam '):
            try:
                # Разбиваем сообщение на части
                parts = event.message.text.split(' ', 2)
                
                if len(parts) < 3:
                    await event.edit("❌ Использование: -spam <кол-во> <сообщение>")
                    return
                
                count = int(parts[1])
                message = parts[2]
                
                if count > 10000:
                    await event.edit("❌ Максимум 10000 сообщений за раз")
                    return
                
                if count < 1:
                    await event.edit("❌ Количество должно быть больше 0")
                    return
                
                await event.delete()
                
                for i in range(count):
                    await client.send_message(event.chat_id, message)
                    await asyncio.sleep(0.1)
                    
            except ValueError:
                await event.edit("❌ Количество должно быть числом")
            except Exception as e:
                await event.edit(f"❌ Ошибка: {str(e)}")
