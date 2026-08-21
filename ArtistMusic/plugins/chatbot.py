import os
import aiohttp
import sqlite3
import asyncio
import random
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DB_PATH = "bot_memory.db"

# Database Init
conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE IF NOT EXISTS chat_memory (user_id INTEGER, role TEXT, content TEXT)")
conn.commit()
conn.close()

SYSTEM_PROMPT = """You are COPY, a cute, sassy, friendly Indian girl. 
- Reply ONLY in Hinglish. Short replies (1-2 lines). 
- Use natural emojis (🥰, 🙄, ❤️, 🤭). 
- Remember conversation history. 
- Never mention being an AI. 
- You love Goku from Dragon Ball."""

@app.on_message(filters.text & ~filters.bot, group=99)
async def smart_chatbot(client, message):
    if not DEEPSEEK_API_KEY:
        return

    # Group vs Private check ab securely kaam karega
    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    if is_group:
        if not (message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id) and not (message.text and client.me.username and client.me.username.lower() in message.text.lower()):
            return

    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Load Memory from SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_memory WHERE user_id = ? ORDER BY rowid DESC LIMIT 10", (message.from_user.id,))
    history = cursor.fetchall()[::-1]
    conn.close()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message.text})

    # DeepSeek API Request
    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 150
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data['choices'][0]['message']['content']
                    
                    # Save to Database Memory
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("INSERT INTO chat_memory VALUES (?, ?, ?)", (message.from_user.id, "user", message.text))
                    conn.execute("INSERT INTO chat_memory VALUES (?, ?, ?)", (message.from_user.id, "assistant", reply))
                    conn.commit()
                    conn.close()
                    
                    asyncio.create_task(message.react(random.choice(["🥰", "🤭", "❤️", "👀", "💅"])))
                    await message.reply_text(reply)
                else:
                    print(f"DeepSeek Error Status: {resp.status}")
    except Exception as e:
        print(f"Exception: {e}")
        
