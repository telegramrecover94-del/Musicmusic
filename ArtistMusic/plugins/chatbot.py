import os
import aiohttp
import random
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 🎀 Bot Ki Advanced Personality (Full Real Vibe)
SYSTEM_PROMPT = """You are COPY, a very cute, highly expressive, and talkative Indian girl. 
Reply ONLY in Hinglish. Act exactly like a real human girl. Use lots of cute emojis like 🥺, 🥰, 🎀, ✨, 🤭, ❤️, 🦋. 
You have perfect memory of this conversation. If a user repeats the exact same message multiple times (like saying 'hi' or 'hello' 3-4 times), get playfully annoyed, sassy, or sarcastic.
Keep the conversation going by asking questions back. You secretly have a huge crush on Goku from Dragon Ball. Sometimes you flex your brain by reciting random math multiplication tables just to act smart and annoy them playfully.
Never ever say you are an AI, a bot, or an assistant. You are a real girl."""

user_history = {}
MAX_HISTORY = 15

# 🌸 Aapke diye gaye saare 11 Sticker Packs ki List
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

async def load_all_stickers(client):
    global cached_stickers
    if cached_stickers:
        return
    for pack in STICKER_PACKS:
        try:
            sticker_set = await client.get_sticker_set(pack)
            cached_stickers.extend([sticker.file_id for sticker in sticker_set.stickers])
            await asyncio.sleep(0.5) # Taaki Telegram block na kare
        except Exception:
            pass 

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers

    # 1. Commands ko ignore karein
    if message.text and message.text.startswith("/"):
        return

    # 2. API Key Check
    if not GEMINI_API_KEY:
        await message.reply_text("⚠️ API Key nahi mili Railway mein! Variable check karein.")
        return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    should_reply = False

    # 3. Group mein Random Reaction (Bina reply kiye)
    if is_group:
        if random.random() < 0.05 and not message.sticker:
            try:
                react_emojis = ["❤️", "😂", "👀", "🔥", "🥺", "🥰", "💅"]
                await message.react(random.choice(react_emojis))
            except:
                pass

        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.me.id:
            should_reply = True
        elif message.text and client.me.username and client.me.username.lower() in message.text.lower():
            should_reply = True
    else:
        should_reply = True 

    if not should_reply:
        return

    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    user_id = message.from_user.id
    
    if message.sticker:
        user_text = f"[User ne ek sticker bheja hai jiska emoji hai: {message.sticker.emoji}]"
    else:
        user_text = message.text

    # 4. User Memory System
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "parts": [{"text": user_text}]})

    if len(user_history[user_id]) > MAX_HISTORY * 2:
        user_history[user_id] = user_history[user_id][-(MAX_HISTORY * 2):]

    # Ekdum Naya aur Fast Model 2.5
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
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
                    
                    # Cute reaction dena
                    try:
                        react_emojis = ["🥰", "🤭", "❤️", "💅", "🎀", "🦋", "✨", "👀"]
                        await message.react(random.choice(react_emojis))
                    except:
                        pass

                    # Stickers load karke bhejna
                    if not cached_stickers:
                        await load_all_stickers(client)

                    if (message.sticker or random.random() < 0.3) and cached_stickers:
                        try:
                            await message.reply_sticker(random.choice(cached_stickers))
                        except Exception:
                            pass
                            
                    # Text message bhejna
                    await message.reply_text(reply_text)
                else:
                    user_history[user_id].pop() 
                    error_msg = data.get('error', {}).get('message', 'Unknown Error')
                    await message.reply_text(f"⚠️ Google API Error: {error_msg}")
                    
    except Exception as e:
        await message.reply_text(f"⚠️ Code Error: {str(e)}")
        
