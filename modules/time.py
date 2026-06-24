from telethon import events
import datetime

dep = []

async def run(client, restart_userbot):
    @client.on(events.NewMessage(outgoing=True))
    async def get_time(event):
        if event.message.text == '-time':
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await event.edit(f"Текущее время: {now}")
