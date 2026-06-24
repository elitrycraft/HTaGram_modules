from telethon import events
import time

dep = []

async def run(client, restart_userbot):
    @client.on(events.NewMessage(outgoing=True))
    async def ping_pong(event):
        if event.message.text == '-ping':
            start = time.time()
            msg = await event.edit("Пинг...")
            end = time.time()
            await msg.edit(f"Понг! {round((end - start) * 1000)} мс")
