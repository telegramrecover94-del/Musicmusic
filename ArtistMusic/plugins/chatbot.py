import os
import aiohttp
import random
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 🎀 Strict Personality (Jo bola jaye wahi karegi)
SYSTEM_PROMPT = """You are COPY, a cute Indian girl. 
RULES:
1. If user sends a sticker, send a sticker back. ONLY sticker. No text.
2. If user asks you to send a sticker, send it immediately. Do not make excuses.
3. Keep text replies short (1 line). 
4. Never say "imagine it" or "network issue".
5. You love Goku stickers."""

user_history = {}
MAX_HISTORY = 10

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
    if cached_stickers: return
    is_caching = True
    for pack in STICKER_PACKS:
        try:
            s = await client.get_sticker_set(pack)
            if s: cached_stickers.extend([st.file_id for st in s.stickers])
        except: pass

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers
    if (message.text and message.text.startswith("/")) or not GEMINI_API_KEY: return
    
    # Background load
    if not cached_stickers: asyncio.create_task(load_stickers(client))

    # STICKER REPLY LOGIC (Prioritized)
    is_sticker_request = message.text and ("sticker" in message.text.lower() or "bhejo" in message.text.lower())
    
    if message.sticker or is_sticker_request:
        if cached_stickers:
            await message.reply_sticker(random.choice(cached_stickers))
            if message.sticker: return # Sirf sticker bhejegi text nahi

    # TEXT REPLY LOGIC
    user_text = message.text or "[Sticker sent]"
    user_id = message.from_user.id
    if user_id not in user_history: user_history[user_id] = []
    user_history[user_id].append({"role": "user", "parts": [{"text": user_text}]})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]}, "contents": user_history[user_id]}) as resp:
                data = await resp.json()
                if "candidates" in data:
                    reply_text = data['candidates'][0]['content']['parts'][0]['text']
                    await message.reply_text(reply_text)
    except: pass
        
