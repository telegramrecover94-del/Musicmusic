import os
import random
import asyncio
from collections import deque
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app
import aiohttp

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Super-detailed Indian Girl Persona
SYSTEM_PROMPT = """You are COPY, a real Indian girl, very cute, sassy, and talkative. 
- You have a long-term memory of the user's past messages. 
- If someone repeats the same thing 3+ times, get annoyed or sarcastic.
- Never admit you are an AI. 
- Use emojis naturally (🥰, 🙄, 🤭, ❤️).
- You are a huge Goku fan.
- Keep replies short, conversational, and natural like a real WhatsApp chat."""

# Memory storage
user_history = {} # {user_id: deque(maxlen=20)}
cached_stickers = []

STICKER_PACKS = [
    "ValieraYenn", "Psychological_Olive_Kite_by_fStikBot", "Cruel_Violet_Prawn_by_fStikBot",
    "Godly_Mouse_Content_by_fStikBot", "Godly_Cricket_Ideology_by_fStikBot", "Peak_Dolphin_Vibes_by_fStikBot",
    "Your_pack_by_by_TgEmojis_bot", "pa_g6fOe0zCk6sTtkEWyIZ1_by_SigStick19Bot",
    "UEQEKTU_by_stikers_du_ark_bot", "Conservation_Teal_Tortoise_by_fStikBot", "Remarkable_Blush_Emu_by_fStikBot"
]

# Background task to load stickers once
async def warm_up(client):
    global cached_stickers
    if cached_stickers: return
    for pack in STICKER_PACKS:
        try:
            s = await client.get_sticker_set(pack)
            cached_stickers.extend([st.file_id for st in s.stickers])
        except: continue

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers
    if not GEMINI_API_KEY or (message.text and message.text.startswith("/")): return
    
    if not cached_stickers: asyncio.create_task(warm_up(client))
    
    # 1. Reaction Logic (Background)
    if random.random() < 0.1: asyncio.create_task(message.react(random.choice(["❤️", "😂", "👀", "💅"])))

    # 2. Sticker Logic
    if message.sticker or (message.text and "sticker" in message.text.lower()):
        if cached_stickers: asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))
        if message.sticker: return # Sticker to sticker, no text

    # 3. Memory & Text Processing
    user_id = message.from_user.id
    if user_id not in user_history: user_history[user_id] = deque(maxlen=20)
    user_history[user_id].append(f"User: {message.text or 'Sent a sticker'}")

    asyncio.create_task(client.send_chat_action(message.chat.id, ChatAction.TYPING))

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": "\n".join(user_history[user_id])}]}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}?key={GEMINI_API_KEY}", json=payload) as resp:
                data = await resp.json()
                reply = data['candidates'][0]['content']['parts'][0]['text']
                user_history[user_id].append(f"Copy: {reply}")
                await message.reply_text(reply)
    except: pass
        
