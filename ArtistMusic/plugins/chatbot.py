import os
import aiohttp
import random
import asyncio
from collections import deque
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

# Ab hum Groq API use kar rahe hain
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# 🎀 Sassy, Fast, & Memory-Rich Persona
SYSTEM_PROMPT = """You are COPY, a cute, sassy, friendly Indian girl on WhatsApp.
- Reply ONLY in Hinglish. Keep it short (1-2 lines). No long essays.
- Use natural emojis (🥰, 🙄, 🤭, ❤️, 💅).
- You secretly love Goku from Dragon Ball.
- Sometimes (rarely), you playfully flex your brain by reciting random math multiplication tables (like 17x4=68) just to act smart and annoy the user.
- If user repeats the same message, get playfully annoyed.
- Never say you are an AI."""

user_history = {} # Super fast in-memory storage
cached_stickers = []
is_caching = False

STICKER_PACKS = [
    "ValieraYenn", "Psychological_Olive_Kite_by_fStikBot", "Cruel_Violet_Prawn_by_fStikBot",
    "Godly_Mouse_Content_by_fStikBot", "Godly_Cricket_Ideology_by_fStikBot", "Peak_Dolphin_Vibes_by_fStikBot",
    "Your_pack_by_by_TgEmojis_bot", "pa_g6fOe0zCk6sTtkEWyIZ1_by_SigStick19Bot",
    "UEQEKTU_by_stikers_du_ark_bot", "Conservation_Teal_Tortoise_by_fStikBot", "Remarkable_Blush_Emu_by_fStikBot"
]

async def load_stickers_in_background(client):
    global cached_stickers, is_caching
    if is_caching or cached_stickers: return
    is_caching = True
    for pack in STICKER_PACKS:
        try:
            s = await client.get_sticker_set(pack)
            if s: cached_stickers.extend([st.file_id for st in s.stickers])
            await asyncio.sleep(0.3)
        except: pass

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers
    if (message.text and message.text.startswith("/")) or not GROQ_API_KEY: return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    should_reply = False

    if is_group:
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id:
            should_reply = True
        elif message.text and client.me.username and client.me.username.lower() in message.text.lower():
            should_reply = True
    else:
        should_reply = True 

    if not should_reply: return

    if not cached_stickers: asyncio.create_task(load_stickers_in_background(client))
    asyncio.create_task(client.send_chat_action(message.chat.id, ChatAction.TYPING))

    # Sticker Logic
    if message.sticker or (message.text and "sticker" in message.text.lower()):
        if cached_stickers: await message.reply_sticker(random.choice(cached_stickers))
        if message.sticker: return 

    # Prepare Memory
    user_id = message.from_user.id
    if user_id not in user_history: 
        user_history[user_id] = deque(maxlen=15) # Fast Memory
    
    user_history[user_id].append({"role": "user", "content": message.text or "Sent a sticker"})

    # Groq API Request (Using the fastest Llama 3 model)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Format messages for Groq/OpenAI style
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(list(user_history[user_id]))

    payload = {
        "model": "llama3-8b-8192", # Extremely fast model
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply_text = data['choices'][0]['message']['content']
                    
                    user_history[user_id].append({"role": "assistant", "content": reply_text})
                    
                    asyncio.create_task(message.react(random.choice(["🥰", "🤭", "❤️", "👀", "💅"])))
                    await message.reply_text(reply_text)
                    
                    if random.random() < 0.20 and cached_stickers:
                        asyncio.create_task(message.reply_sticker(random.choice(cached_stickers)))
                else:
                    print(f"Groq Error: {await resp.text()}")
    except Exception as e:
        print(f"Error: {e}")
        
