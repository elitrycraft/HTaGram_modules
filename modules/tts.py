from telethon import events
from gtts import gTTS
import os
import uuid

dep = ["gTTS"]

async def run(client, arg):
    @client.on(events.NewMessage(outgoing=True))
    async def tts_cmd(event):
        if event.message.text.startswith('-tts '):
            text = event.message.text[5:]
            
            if not text:
                await event.edit("❌ Использование: -tts <текст>")
                return
            
            await event.delete()
            
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            tts = gTTS(text=text, lang='ru', slow=False)
            tts.save(filename)
            
            await client.send_file(
                event.chat_id,
                filename,
                voice_note=True,
                reply_to=event.message.reply_to_msg_id
            )
            
            os.remove(filename)
            await event.delete()
