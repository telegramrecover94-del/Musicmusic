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

# Database Init
conn = sqlite3.connect(DB_PATH)
conn.execute("CREATE TABLE IF NOT EXISTS chat_memory (user_id INTEGER, role TEXT, content TEXT)")
conn.commit()
conn.close()

SYSTEM_PROMPT = "You are COPY, a cute Indian girl. Reply short in Hinglish."

@app.on_message(filters.text & ~filters.bot, group=99)
async def smart_chatbot(client, message):
    print(f"DEBUG: Message received from {message.from_user.id}: {message.text}") # <--- Yeh check karne ke liye ki message aa raha hai ya nahi
    
    if not DEEPSEEK_API_KEY:
        print("DEBUG: DEEPSEEK_API_KEY missing!")
        return

    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    # Load Memory
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_memory WHERE user_id = ? ORDER BY rowid DESC LIMIT 6", (message.from_user.id,))
    history = cursor.fetchall()[::-1]
    conn.close()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for role, content in history:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message.text})

    url = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 100
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                resp_text = await resp.text()
                print(f"DEBUG: DeepSeek Response Status: {resp.status}")
                print(f"DEBUG: DeepSeek Response Body: {resp_text}")
                
                if resp.status == 200:
                    data = await resp.json()
                    reply = data['choices'][0]['message']['content']
                    
                    # Save Memory
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("INSERT INTO chat_memory VALUES (?, ?, ?)", (message.from_user.id, "user", message.text))
                    conn.execute("INSERT INTO chat_memory VALUES (?, ?, ?)", (message.from_user.id, "assistant", reply))
                    conn.commit()
                    conn.close()
                    
                    await message.reply_text(reply)
                else:
                    await message.reply_text(f"API Error: {resp.status}")
    except Exception as e:
        print(f"DEBUG EXCEPTION: {e}")
        
