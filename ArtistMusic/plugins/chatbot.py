import os
import aiohttp
import sqlite3
import asyncio
import random
from pyrogram import filters
from pyrogram.enums import ChatAction
from ArtistMusic import app

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DB_PATH = "bot_memory.db"

# Database Init for Memory (Riruru Style)
conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE IF NOT EXISTS chat_memory (user_id INTEGER, role TEXT, content TEXT)")
conn.commit()
conn.close()

SYSTEM_PROMPT = """You are COPY, a real Indian cute girl (19-22). 
- Use Hinglish, be sassy, natural emojis (🥰, 🙄, ❤️, 🤭).
- Remember conversation history. 
- Never mention being an AI. 
- You love Goku from Dragon Ball.
- Short, conversational, WhatsApp-style replies (1-2 lines)."""

STICKER_PACKS = [
    "ValieraYenn", "Psychological_Olive_Kite_by_fStikBot", "Cruel_Violet_Prawn_by_fStikBot",
    "Godly_Mouse_Content_by_fStikBot", "Godly_Cricket_Ideology_by_fStikBot", "Peak_Dolphin_Vibes_by_fStikBot",
    "Your_pack_by_by_TgEmojis_bot", "pa_g6fOe0zCk6sTtkEWyIZ1_by_SigStick19Bot",
    "UEQEKTU_by_stikers_du_ark_bot", "Conservation_Teal_Tortoise_by_fStikBot", "Remarkable_Blush_Emu_by_fStikBot"
]

cached_stickers = []
is_caching = False

async def load_stickers(client):
    global cached_stickers, is_caching
    if is_caching or cached_stickers: return
    is_caching = True
    for pack in STICKER_PACKS:
        try:
            s = await client.get_sticker_set(pack)
            if s: cached_stickers.extend([st.file_id for st in s.stickers])
            await asyncio.sleep(0.3)
        except: pass

async def get_deepseek_reply(user_id, user_text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_memory WHERE user_id = ? ORDER BY rowid DESC LIMIT 12", (user_id,))
    history = cursor.fetchall()[::-1]
    conn.close()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})

    # DeepSeek API Endpoint
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat", # DeepSeek ka stable chat model
        "messages": messages,
        "max_tokens": 150
    }
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data['choices'][0]['message']['content']
            else:
                return f"Arre network error aa gaya 🥺 ({resp.status})"

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def smart_chatbot(client, message):
    global cached_stickers
    if (message.text and message.text.startswith("/")) or not DEEPSEEK_API_KEY: return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    if is_group:
        if not (message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id) and not (message.text and client.me.username and client.me.username.lower() in message.text.lower()):
            return

    if not cached_stickers: asyncio.create_task(load_stickers(client))
    asyncio.create_task(client.send_chat_action(message.chat.id, ChatAction.TYPING))

    # Sticker Logic
    if message.sticker or (message.text and "sticker" in message.text.lower()):
        if cached_stickers: await message.reply_sticker(random.choice(cached_stickers))
        if message.sticker: return

    user_text = message.text or "Sent a sticker"
    user_id = message.from_user.id

    # Get Reply from DeepSeek
    reply = await get_deepseek_reply(user_id, user_text)

    # Save to SQLite Memory
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO chat_memory VALUES (?, ?, ?)", (user_id, "user", user_text))
    conn.execute("INSERT INTO chat_memory VALUES (?, ?, ?)", (user_id, "assistant", reply))
    conn.commit()
    conn.close()

    asyncio.create_task(message.react(random.choice(["🥰", "🤭", "❤️", "👀", "💅"])))
    await message.reply_text(reply)

    if random.random() < 0.20 and cached_stickers:
        asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))
        
