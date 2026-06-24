from telethon import events
import requests

dep = []

async def run(client, restart_userbot):
    @client.on(events.NewMessage(outgoing=True))
    async def my_ip(event):
        if event.message.text == '-ip':
            r = requests.get("https://api.ipify.org").text
            await event.edit(f"IP: {r}")
