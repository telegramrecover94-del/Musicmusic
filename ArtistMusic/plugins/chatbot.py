import os
import aiohttp
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatAction
from ArtistMusic import app

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

@app.on_message(filters.text & ~filters.bot, group=99)
async def debug_chatbot(client, message):
    if not GROQ_API_KEY:
        await message.reply("API Key missing!")
        return

    # 1. Start typing
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    # 2. Prepare request
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": message.text}],
        "max_tokens": 100
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                response_text = await resp.text() # Get full raw response for debugging
                if resp.status == 200:
                    data = await resp.json()
                    reply = data['choices'][0]['message']['content']
                    await message.reply_text(reply)
                else:
                    # If it fails, this will reply with the error so we know what's wrong
                    await message.reply_text(f"Error {resp.status}: {response_text[:100]}")
    except Exception as e:
        await message.reply_text(f"Exception: {str(e)}")
        
