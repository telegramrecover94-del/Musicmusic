import os
import aiohttp
import random
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 🎀 Bot Ki Advanced Personality (Full Real Vibe)
SYSTEM_PROMPT = """You are COPY, a very cute, highly expressive, and talkative Indian girl. 
Reply ONLY in Hinglish. Act exactly like a real human girl. Use lots of cute emojis like 🥺, 🥰, 🎀, ✨, 🤭, ❤️, 🦋. 
You have perfect memory of this conversation. If a user repeats the exact same message multiple times (like saying 'hi' or 'hello' 3-4 times), get playfully annoyed, sassy, or sarcastic (like "ek hi baat kitni baar bolega?", "dimag mat kha mera", etc.).
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
        except Exception:
            pass # Agar koi pack delete ho gaya ho toh error ignore karein

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    global cached_stickers
    if not GEMINI_API_KEY:
        return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    should_reply = False

    # 1. Group mein 5% chance hai random kisi ki baat par react karne ka
    if is_group and not message.text.startswith("/"):
        if random.random() < 0.05:
            try:
                react_emojis = ["❤️", "😂", "👀", "🔥", "🥺", "🥰", "💅"]
                await message.react(random.choice(react_emojis))
            except:
                pass

    # 2. Check karna ki reply karna hai ya nahi
    if is_group:
        if message.reply_to_message and message.reply_to_message.from_user.id == client.me.id:
            should_reply = True
        elif message.text and client.me.username and client.me.username.lower() in message.text.lower():
            should_reply = True
    else:
        should_reply = True 

    if not should_reply:
        return

    if message.text and message.text.startswith("/"):
        return

    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
    user_id = message.from_user.id
    
    # 3. Sticker bheja toh AI ko text mein batao
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

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
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
                    
                    # 💅 Hamesha cute reaction dena
                    try:
                        react_emojis = ["🥰", "🤭", "❤️", "💅", "🎀", "🦋", "✨", "👀"]
                        await message.react(random.choice(react_emojis))
                    except:
                        pass

                    # 🎁 Saare packs load karna aur random sticker bhejna
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
    except Exception as e:
        pass
      
