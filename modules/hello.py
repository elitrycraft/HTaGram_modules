# modules/hello.py
from telethon import events

async def run(client, restart_userbot):
    @client.on(events.NewMessage(outgoing=True))
    async def hello(event):
        if event.message.text == '.hello':
            await event.edit("Привет, мир!")
