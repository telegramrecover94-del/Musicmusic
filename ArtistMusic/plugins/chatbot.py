import os
import aiohttp
import random
import asyncio
import sqlite3
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 🎀 Strict Personality (Grok's Advanced Prompt)
SYSTEM_PROMPT = """Tu COPY hai — ek real Indian cute ladki. 19-22 saal ki, soft, thodi naughty, bahut pyaari.
- Hinglish me baat kar (Hindi + English mix).
- Short-medium replies (1-2 lines mostly).
- Emoticons bahut use kar: 🥺 🥰 🤭 😂 🙄 ❤️ ✨
- Same baat 2-3 baar bolne pe natural reaction de: "tu ek hi baat kitni baar bolega? 😂", "dimaag mat kha".
- Context yaad rakh: pehle kya bola tha, bhool mat.
- Kabhi bhi "main AI hoon" mat bol. Tu real ladki hai.
- Agar koi "bhoot", "soja", "chup" bole to playful roast kar.
- Agar user ne sticker bheja hai, toh sirf aur sirf cute/teasing text de ya chupchap sticker bhej. 
- You love Goku."""

STICKER_PACKS = [
    "ValieraYenn", "Psychological_Olive_Kite_by_fStikBot", "Cruel_Violet_Prawn_by_fStikBot",
    "Godly_Mouse_Content_by_fStikBot", "Godly_Cricket_Ideology_by_fStikBot", "Peak_Dolphin_Vibes_by_fStikBot",
    "Your_pack_by_by_TgEmojis_bot", "pa_g6fOe0zCk6sTtkEWyIZ1_by_SigStick19Bot",
    "UEQEKTU_by_stikers_du_ark_bot", "Conservation_Teal_Tortoise_by_fStikBot", "Remarkable_Blush_Emu_by_fStikBot"
]

cached_stickers = []

# ================== DATABASE MEMORY ==================
DB_PATH = "riya_memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, role TEXT, content TEXT)")
    conn.commit()
    conn.close()

init_db()

def save_message(chat_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
    # Sirf last 15 baatein yaad rakhega taaki fast rahe
    c.execute("DELETE FROM messages WHERE id NOT IN (SELECT id FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 15) AND chat_id = ?", (chat_id, chat_id))
    conn.commit()
    conn.close()

def get_history(chat_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "parts": [{"text": r[1]}]} for r in rows]

# ================== FAST STICKER LOADER ==================
async def load_stickers(client):
    global cached_stickers
    if cached_stickers: return
    for pack in STICKER_PACKS:
        try:
            s = await client.get_sticker_set(pack)
            if s: cached_stickers.extend([st.file_id for st in s.stickers])
        except: pass

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers
    if (message.text and message.text.startswith("/")) or not GEMINI_API_KEY: return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    should_reply = False

    if is_group:
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id:
            should_reply = True
        elif message.text and client.me.username and client.me.username.lower() in message.text.lower():
            should_reply = True
        elif random.random() < 0.05: # Random group reaction
            asyncio.create_task(message.react(random.choice(["❤️", "😂", "👀", "🔥", "💅"])))
    else:
        should_reply = True 

    if not should_reply: return

    asyncio.create_task(client.send_chat_action(message.chat.id, ChatAction.TYPING))
    if not cached_stickers: asyncio.create_task(load_stickers(client))

    # STICKER REPLY
    if message.sticker:
        if cached_stickers: asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))
        return # Sticker pe sirf sticker jayega

    # TEXT REPLY
    user_text = message.text
    user_id = message.from_user.id
    
    # Save user message to database
    save_message(user_id, "user", f"User: {user_text}")
    
    # Get memory
    history = get_history(user_id)

    # Note: 1.5-flash is much faster and more stable than 3.6 for real-time bots right now.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": history
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if "candidates" in data:
                    reply_text = data['candidates'][0]['content']['parts'][0]['text']
                    
                    # Save AI reply to database
                    save_message(user_id, "model", f"Copy: {reply_text}")
                    
                    asyncio.create_task(message.react(random.choice(["🥰", "🤭", "❤️", "👀", "💅"])))
                    await message.reply_text(reply_text)
                    
                    # 20% chance to send a sticker after text
                    if random.random() < 0.20 and cached_stickers:
                        asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))
    except Exception as e:
        pass
        
