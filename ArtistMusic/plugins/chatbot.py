import os
import aiohttp
import random
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 🎀 Bot Ki Sassy Personality
SYSTEM_PROMPT = "You are COPY, a cute, sassy, friendly Indian girl. Reply short (1-2 lines), Hinglish, natural emojis, like WhatsApp. Secretly like Goku. Never say you are an AI."

user_history = {}
MAX_HISTORY = 15

STICKER_PACKS = [
    "ValieraYenn", "Psychological_Olive_Kite_by_fStikBot", "Cruel_Violet_Prawn_by_fStikBot",
    "Godly_Mouse_Content_by_fStikBot", "Godly_Cricket_Ideology_by_fStikBot", "Peak_Dolphin_Vibes_by_fStikBot",
    "Your_pack_by_by_TgEmojis_bot", "pa_g6fOe0zCk6sTtkEWyIZ1_by_SigStick19Bot",
    "UEQEKTU_by_stikers_du_ark_bot", "Conservation_Teal_Tortoise_by_fStikBot", "Remarkable_Blush_Emu_by_fStikBot"
]

cached_stickers = []
is_caching = False

async def load_stickers_in_background(client):
    global cached_stickers, is_caching
    if is_caching or cached_stickers: return
    is_caching = True
    for pack in STICKER_PACKS:
        try:
            sticker_set = await client.get_sticker_set(pack)
            if sticker_set: cached_stickers.extend([s.file_id for s in sticker_set.stickers])
            await asyncio.sleep(0.3)
        except: pass

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers
    if (message.text and message.text.startswith("/")) or not GEMINI_API_KEY: return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    if is_group and not (message.reply_to_message and message.reply_to_message.from_user.id == client.me.id) and not (message.text and client.me.username and client.me.username.lower() in message.text.lower()): return

    asyncio.create_task(client.send_chat_action(message.chat.id, ChatAction.TYPING))
    if not cached_stickers: asyncio.create_task(load_stickers_in_background(client))

    if message.sticker:
        user_text = "[Sticker]"
        if cached_stickers: asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))
    else:
        user_text = message.text
        if random.random() < 0.20 and cached_stickers: asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))

    user_id = message.from_user.id
    if user_id not in user_history: user_history[user_id] = []
    user_history[user_id].append({"role": "user", "parts": [{"text": user_text}]})

    # MODEL FALLBACK LOGIC
    models = ["gemini-1.5-flash", "gemini-1.5-pro"]
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]}, "contents": user_history[user_id]}) as resp:
                    data = await resp.json()
                    if "candidates" in data:
                        reply_text = data['candidates'][0]['content']['parts'][0]['text']
                        user_history[user_id].append({"role": "model", "parts": [{"text": reply_text}]})
                        await message.reply_text(reply_text)
                        return # Success
        except: continue 
