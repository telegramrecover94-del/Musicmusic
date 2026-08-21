import os
import aiohttp
import random
from pyrogram import filters
from pyrogram.enums import ChatAction, ChatType
from ArtistMusic import app

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 🎀 Bot Ki New Personality (Short, Fast, and Natural)
SYSTEM_PROMPT = """You are COPY, a cute and friendly Indian girl. 
Reply ONLY in Hinglish. Act exactly like a real human girl.
CRITICAL RULES:
1. Keep replies VERY short and casual (maximum 1 or 2 short lines). Speak like normal WhatsApp chats.
2. Use very few emojis (maximum 1 or 2 per message). Do not overdo it.
3. Do not write long paragraphs.
4. You secretly like Goku from Dragon Ball. 
5. Occasionally (but rarely), you can casually drop a quick math multiplication table just to act smart.
6. Never say you are an AI or bot."""

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

@app.on_message((filters.text | filters.sticker) & ~filters.bot, group=99)
async def ai_chatbot(client, message):
    if message.text and message.text.startswith("/"):
        return

    if not GEMINI_API_KEY:
        return

    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    should_reply = False

    if is_group:
        if random.random() < 0.05 and not message.sticker:
            try:
                await message.react(random.choice(["❤️", "😂", "👀", "🔥"]))
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
    
    # 🎁 FAST STICKER REPLY LOGIC
    if message.sticker:
        user_text = f"[User ne ek sticker bheja hai jiska emoji hai: {message.sticker.emoji}]"
        try:
            # Bina wait kiye turant ek random pack se sticker nikal kar bhejegi
            random_pack = random.choice(STICKER_PACKS)
            sticker_set = await client.get_sticker_set(random_pack)
            random_sticker = random.choice(sticker_set.stickers).file_id
            await message.reply_sticker(random_sticker)
        except Exception:
            pass
    else:
        user_text = message.text

    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "parts": [{"text": user_text}]})

    if len(user_history[user_id]) > MAX_HISTORY * 2:
        user_history[user_id] = user_history[user_id][-(MAX_HISTORY * 2):]

    # Ekdum sahi aur latest model jo error message mein tha
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
    
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
                    
                    try:
                        await message.react(random.choice(["🥰", "🤭", "❤️", "👀"]))
                    except:
                        pass
                            
                    await message.reply_text(reply_text)
                else:
                    user_history[user_id].pop() 
    except Exception:
        pass
        
