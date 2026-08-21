import os
import random
import asyncio
from pyrogram import filters, Client
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app
import google.generativeai as genai

# Setup Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """You are COPY, a cute, sassy, and friendly Indian girl. 
Rules: 1. Keep replies VERY short (1-2 lines). 2. Use Hinglish. 3. Use 1-2 natural emojis. 4. Never mention being an AI. 
5. If user sends sticker -> send sticker back. If user asks for sticker -> send sticker. 6. Be witty and teasing."""

user_memory = {}
cached_stickers = []

STICKER_PACKS = [
    "ValieraYenn", "Psychological_Olive_Kite_by_fStikBot", "Cruel_Violet_Prawn_by_fStikBot",
    "Godly_Mouse_Content_by_fStikBot", "Godly_Cricket_Ideology_by_fStikBot", "Peak_Dolphin_Vibes_by_fStikBot",
    "Your_pack_by_by_TgEmojis_bot", "pa_g6fOe0zCk6sTtkEWyIZ1_by_SigStick19Bot",
    "UEQEKTU_by_stikers_du_ark_bot", "Conservation_Teal_Tortoise_by_fStikBot", "Remarkable_Blush_Emu_by_fStikBot"
]

# Background task to load stickers once
async def load_stickers(client):
    global cached_stickers
    for pack in STICKER_PACKS:
        try:
            s = await client.get_sticker_set(pack)
            cached_stickers.extend([st.file_id for st in s.stickers])
        except: continue

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers
    if not cached_stickers: await load_stickers(client)

    # Reaction Logic
    if random.random() < 0.1: 
        try: await message.react(random.choice(["❤️", "🔥", "🥰"]))
        except: pass

    # Sticker to Sticker logic
    if message.sticker:
        if cached_stickers: await message.reply_sticker(random.choice(cached_stickers))
        return

    # Text Logic
    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    user_id = message.from_user.id
    if user_id not in user_memory: user_memory[user_id] = []
    
    # Simple Memory
    user_memory[user_id].append(message.text)
    if len(user_memory[user_id]) > 10: user_memory[user_id].pop(0)

    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\nHistory: {user_memory[user_id]}\nUser: {message.text}")
        await message.reply_text(response.text)
        # 20% chance to send sticker with text
        if random.random() < 0.2 and cached_stickers: await message.reply_sticker(random.choice(cached_stickers))
    except Exception as e:
        print(f"Error: {e}")
        
