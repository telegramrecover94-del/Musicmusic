import os
import aiohttp
import random
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 🎀 Bot Ki New Sassy & FAST Personality
SYSTEM_PROMPT = """You are COPY, a cute, sassy, and friendly Indian girl. 
Reply ONLY in Hinglish. Act exactly like a real human girl on WhatsApp.
CRITICAL RULES:
1. Keep replies VERY short (maximum 1 or 2 lines). No long paragraphs.
2. Use emojis naturally (max 1-2 per message). 
3. You secretly like Goku from Dragon Ball. 
4. Never say you are an AI or bot.
5. If the user sends a sticker, give a short teasing, funny, or sassy reaction."""

user_history = {}
MAX_HISTORY = 15

# 🌸 Aapke 11 Sticker Packs
STICKER_PACKS = [
    "ValieraYenn",
    "Psychological_Olive_Kite_by_fStikBot",
    "Cruel_Violet_Prawn_by_fStikBot",
    "Godly_Mouse_Content_by_fStikBot",
    "Godly_Cricket_Ideology_by_fStikBot",
    "Peak_Dolphin_Vibes_by_fStikBot",
    "Your_pack_by_by_TgEmojis_bot",
    "pa_g6fOe0zCk6sTtkEWyIZ1_by_SigStick19Bot",
    "UEQEKTU_by_stikers_du_ark_bot",
    "Conservation_Teal_Tortoise_by_fStikBot",
    "Remarkable_Blush_Emu_by_fStikBot"
]

cached_stickers = []
is_caching = False

# ⚡ Background mein chupchap stickers load karne ka function
async def load_stickers_in_background(client):
    global cached_stickers, is_caching
    if is_caching or cached_stickers:
        return
    is_caching = True
    for pack in STICKER_PACKS:
        try:
            sticker_set = await client.get_sticker_set(pack)
            if sticker_set and sticker_set.stickers:
                cached_stickers.extend([s.file_id for s in sticker_set.stickers])
            await asyncio.sleep(0.3) # Fast loading bina block kiye
        except:
            pass

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers

    if message.text and message.text.startswith("/"):
        return

    if not GEMINI_API_KEY:
        return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    should_reply = False

    if is_group:
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id:
            should_reply = True
        elif message.text and client.me.username and client.me.username.lower() in message.text.lower():
            should_reply = True
    else:
        should_reply = True 

    if not should_reply:
        return

    # 1. Typing action background mein (Toh bot rukega nahi)
    asyncio.create_task(client.send_chat_action(message.chat.id, ChatAction.TYPING))
    
    # 2. Stickers ko background mein load pe lagao
    if not cached_stickers:
        asyncio.create_task(load_stickers_in_background(client))

    # 3. Sticker Logic
    send_sticker_now = False
    if message.sticker:
        send_sticker_now = True 
        user_text = "[User ne ek sticker bheja hai. Short aur funny/sassy reaction do.]"
    else:
        if random.random() < 0.20: 
            send_sticker_now = True
        user_text = message.text

    # 🚀 4. TURANT STICKER BHEJO (Bina AI ka wait kiye)
    if send_sticker_now and cached_stickers:
        asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))

    # --- AI TEXT REPLY ---
    user_id = message.from_user.id
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "parts": [{"text": user_text}]})
    if len(user_history[user_id]) > MAX_HISTORY * 2:
        user_history[user_id] = user_history[user_id][-(MAX_HISTORY * 2):]

    # 🌟 Naya Model Jo Aapne Manga (3.6-flash) 🌟
    models = ["gemini-3.6-flash", "gemini-1.5-pro"]
    
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": user_history[user_id]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    data = await resp.json()
                    
                    if "candidates" in data:
                        reply_text = data['candidates'][0]['content']['parts'][0]['text']
                        user_history[user_id].append({"role": "model", "parts": [{"text": reply_text}]})
                        
                        # Reaction background mein
                        asyncio.create_task(message.react(random.choice(["🥰", "🤭", "❤️", "👀", "💅"])))
                                
                        await message.reply_text(reply_text)
                        return # Ek model chal gaya, aage check karne ki zarurat nahi
        except Exception:
            continue # Agar 3.6 error de, toh turant backup pro model pe jump karega
