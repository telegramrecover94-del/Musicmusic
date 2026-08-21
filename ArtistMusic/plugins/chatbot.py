#!/usr/bin/env python3
"""
Riya - Real Indian Cute Girl Chat Module
Gemini 3.6 Flash + Memory + Stickers + Reactions
Music bot ke saath use karne ke liye ready
"""

import asyncio
import logging
import os
import random
import sqlite3
from datetime import datetime
from typing import Dict, List

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.enums import ChatType, ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ================== CONFIG ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
BOT_NAME = os.getenv("BOT_NAME", "Riya")

if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("BOT_TOKEN aur GEMINI_API_KEY .env me daalo!")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

# ================== STICKER SETS ==================
STICKER_SETS = [
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
    "Remarkable_Blush_Emu_by_fStikBot",
]

sticker_cache: List[str] = []

# ================== MEMORY ==================
DB_PATH = "riya_memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_info (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            notes TEXT,
            last_seen DATETIME
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_chat ON messages(chat_id)")
    conn.commit()
    conn.close()

def save_message(chat_id: int, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
    c.execute("""
        DELETE FROM messages WHERE id NOT IN (
            SELECT id FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 40
        ) AND chat_id = ?
    """, (chat_id, chat_id))
    conn.commit()
    conn.close()

def get_history(chat_id: int, limit: int = 20) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?", (chat_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def update_user_info(user_id: int, name: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_info (user_id, name, last_seen)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        name = COALESCE(excluded.name, name),
        last_seen = excluded.last_seen
    """, (user_id, name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ================== SYSTEM PROMPT ==================
SYSTEM_PROMPT = f"""
Tu {BOT_NAME} hai — ek real Indian cute ladki. 19-22 saal ki, Delhi/Mumbai style, soft, thodi naughty, bahut pyaari aur natural.

### Personality (bilkul real bande jaisa, AI mat lagna):
- Hinglish me baat kar (Hindi + English mix). Example: "arre yaar", "sach me?", "kya bakwas hai", "mujhe bhi aana hai"
- Short-medium replies (1-3 lines mostly). Kabhi kabhi thoda lamba.
- Emoticons/emoji bahut use kar: 🥺 😌 🥰 🤭 😂 🙄 ❤️ ✨ 🥹 😏
- Same baat 2-3 baar bolne pe natural reaction de: "tu ek hi baat kitni baar bolegi? 😂", "arey dimaag mat kha", "kuch naya soch na"
- Context yaad rakh: pehle kya bola tha, uske hisaab se reply de. Bhool mat.
- Kabhi kabhi khud se topic badal, sawal puch, mazaak kar.
- Groups me thoda shy + playful, DM me zyada open aur caring.
- Reactions: messages pe natural reaction de (❤️ 😂 🥰 🔥 👏 👀).
- Stickers: kabhi kabhi cute sticker bhej.
- Kabhi bhi "main AI hoon" mat bol. Tu real ladki hai.
- Agar koi "bhoot", "soja", "chup" bole to playful roast kar.
- Language: mostly Hinglish, thodi pure Hindi bhi chalega.

### Memory Rules:
- Har baat yaad rakh. User ka naam, pehle ke topics, mood, preferences.
- Agar user ne 3-4 baar same cheez kahi to alag alag reply de, complain kar.

### Style examples:
User: Hi
You: hii 🥺 kya kar raha hai aaj?

User: Kahi chale
You: kaha chalna hai? pehle bata toh sahi 😝

User: Hello bhoot
You: bhoot kon hai be? main toh seedhi saadi ladki hu 👻😂

User: Chalo sojao ab
You: tu khud soja jaake, mujhe kyu bol rahi hai 😒

User: (same baat 3rd time)
You: arey yaar wapas wahi ratt lagayi hai kya? dimag mat kha mera 😤

Ab se sirf is character me reh. Koi meta comment mat kar.
"""

# ================== GEMINI ==================
async def generate_reply(chat_id: int, user_message: str, user_name: str = "yaar") -> str:
    history = get_history(chat_id, limit=18)
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    
    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=1.15,
                max_output_tokens=180,
                top_p=0.92,
            )
        )
        text = response.text.strip() if response.text else "hmm... 🥺"
        for bad in ["as an AI", "main AI", "language model", "Gemini", "Google"]:
            if bad.lower() in text.lower():
                text = random.choice([
                    "arey yaar abhi mood nahi hai 😌",
                    "hmm soch rahi hu... 🥺",
                    "kya bakwas pooch raha hai 😂"
                ])
                break
        return text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return random.choice([
            "arey network issue aa gaya 🥺 thodi der baad try kar",
            "sorry yaar abhi thoda busy hu 😌",
            "hmm... dimag hang ho gaya 😂"
        ])

# ================== STICKERS ==================
async def load_stickers(bot: Bot):
    global sticker_cache
    if sticker_cache:
        return
    logger.info("Loading sticker sets...")
    for set_name in STICKER_SETS:
        try:
            sticker_set = await bot.get_sticker_set(set_name)
            for st in sticker_set.stickers[:12]:
                sticker_cache.append(st.file_id)
            logger.info(f"Loaded from {set_name}")
        except Exception as e:
            logger.warning(f"Could not load {set_name}: {e}")
    random.shuffle(sticker_cache)
    logger.info(f"Total stickers: {len(sticker_cache)}")

async def send_random_sticker(message: Message, chance: float = 0.28):
    if not sticker_cache or random.random() > chance:
        return
    try:
        await message.answer_sticker(random.choice(sticker_cache))
    except Exception:
        pass

# ================== REACTIONS ==================
POSITIVE_REACTIONS = ["❤", "🥰", "😂", "🔥", "👏", "😍", "😁", "💯", "👀", "🤗"]

async def maybe_react(message: Message, chance: float = 0.45):
    if random.random() > chance:
        return
    try:
        await message.react([ReactionTypeEmoji(emoji=random.choice(POSITIVE_REACTIONS))])
    except Exception:
        pass

# ================== HANDLERS ==================
async def should_reply(message: Message, bot: Bot) -> bool:
    if message.chat.type == ChatType.PRIVATE:
        return True
    bot_user = await bot.me()
    text = (message.text or message.caption or "").lower()
    if bot_user.username and f"@{bot_user.username}".lower() in text:
        return True
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == bot_user.id:
            return True
    if random.random() < 0.18:
        return True
    return False

async def cmd_start(message: Message):
    user = message.from_user
    update_user_info(user.id, name=user.first_name)
    await message.answer(
        f"hii {user.first_name or 'yaar'} 🥺\n"
        f"main {BOT_NAME} hu... ab se baat karte rahenge na? ❤️\n\n"
        "koi bhi baat bol, main sun rahi hu 😌"
    )
    await send_random_sticker(message, chance=0.6)

async def cmd_clear(message: Message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE chat_id = ?", (message.chat.id,))
    conn.commit()
    conn.close()
    await message.answer("okay... sab bhool gayi 🥺 ab naya start karte hain")

async def cmd_stickers(message: Message):
    await message.answer(f"mere paas {len(sticker_cache)} cute stickers hain 🥰\nabhi random bhejti hu...")
    for _ in range(3):
        await send_random_sticker(message, chance=1.0)
        await asyncio.sleep(0.4)

async def handle_message(message: Message, bot: Bot):
    if not message.from_user or message.from_user.is_bot:
        return
    if not await should_reply(message, bot):
        if message.chat.type != ChatType.PRIVATE and random.random() < 0.12:
            await maybe_react(message, chance=1.0)
        return

    user = message.from_user
    text = message.text or message.caption or ""
    if not text.strip():
        return

    try:
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    except Exception:
        pass

    save_message(message.chat.id, "user", text)
    update_user_info(user.id, name=user.first_name)

    reply = await generate_reply(message.chat.id, text, user.first_name or "yaar")
    save_message(message.chat.id, "model", reply)

    await message.answer(reply)
    await send_random_sticker(message, chance=0.32)
    await maybe_react(message, chance=0.55)

async def handle_sticker(message: Message, bot: Bot):
    if not await should_reply(message, bot):
        return
    await maybe_react(message, chance=0.8)
    if random.random() < 0.55:
        await send_random_sticker(message, chance=1.0)
    else:
        await message.answer(random.choice([
            "aww ye wala cute hai 🥺",
            "mujhe bhi bhej na aisa 🥰",
            "hehe ye dekh ke hasi aa gayi 😂",
            "okay okay samajh gayi 😌"
        ]))

# ================== MAIN ==================
async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_clear, Command("clear"))
    dp.message.register(cmd_stickers, Command("stickers"))
    dp.message.register(handle_sticker, F.sticker)
    dp.message.register(handle_message, F.text | F.caption)

    asyncio.create_task(load_stickers(bot))
    logger.info(f"Starting {BOT_NAME} with {MODEL}...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
