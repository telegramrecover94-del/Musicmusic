# ==========================================================
# Copyright (c) 2026 COPYxMUSIC 
# All Rights Reserved.
#
# Project      : COPYxMUSIC API Telegram Music Bot
# Powered By   : Copy
# Type         : API Based Telegram Music Bot
#
# Bot          : @COPYxMUSIC_BOT 
# Channel      : https://t.me/CopymusicOfficial
# GitHub       : 
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================
from pyrogram import types
from pyrogram.enums import ButtonStyle

from ArtistMusic import app, config, lang


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[
            self.ikb(
                text=f"❌  {text}",
                callback_data="cancel_dl",
                style=ButtonStyle.DANGER,
            )
        ]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []

        if status:
            keyboard.append(
                [self.ikb(
                    text=f"{status}",
                    callback_data=f"controls status {chat_id}",
                    style=ButtonStyle.PRIMARY,
                )]
            )
        elif timer:
            keyboard.append(
                [self.ikb(
                    text=f"{timer}",
                    callback_data=f"controls status {chat_id}",
                    style=ButtonStyle.PRIMARY,
                )]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="II",  callback_data=f"controls pause {chat_id}",  style=ButtonStyle.PRIMARY),
                    self.ikb(text="▷",   callback_data=f"controls resume {chat_id}", style=ButtonStyle.SUCCESS),
                    self.ikb(text="↻",   callback_data=f"controls replay {chat_id}", style=ButtonStyle.SUCCESS),
                    self.ikb(text="⏭", callback_data=f"controls skip {chat_id}",   style=ButtonStyle.PRIMARY),
                    self.ikb(text="⏹",   callback_data=f"controls stop {chat_id}",   style=ButtonStyle.DANGER),
                ]
            )
            keyboard.append(
                [
                    self.ikb(
                        text="• ᴄʟᴏsᴇ •",
                        callback_data=f"controls close {chat_id}",
                        style=ButtonStyle.DANGER,
                    ),
                ]
            )

        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [self.ikb(
                    text="• ʙᴀᴄᴋ •",
                    callback_data="help_main",
                    style=ButtonStyle.SUCCESS,
                )]
            ]
        else:
            rows = [
                [
                    self.ikb(text="ᴀᴅᴍɪɴs",     callback_data="help_admins",       style=ButtonStyle.PRIMARY),
                    self.ikb(text="ᴀᴜᴛʜ",        callback_data="help_auth",         style=ButtonStyle.PRIMARY),
                    self.ikb(text="ʙʀᴏᴀᴅᴄᴀsᴛ",  callback_data="help_broadcast",    style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(text="ʙ-ᴄʜᴀᴛ",    callback_data="help_blchat",       style=ButtonStyle.PRIMARY),
                    self.ikb(text="ʙ-ᴜsᴇʀ",    callback_data="help_bluser",       style=ButtonStyle.PRIMARY),
                    self.ikb(text="ɢ-ʙᴀɴ",       callback_data="help_gban",         style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(text="ʟᴏᴏᴘ",        callback_data="help_loop",         style=ButtonStyle.PRIMARY),
                    self.ikb(text="ᴘʟᴀʏ",        callback_data="help_play",         style=ButtonStyle.PRIMARY),
                    self.ikb(text="ǫᴜᴇᴜᴇ",       callback_data="help_queue",        style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(text="sᴇᴇᴋ",        callback_data="help_seek",         style=ButtonStyle.PRIMARY),
                    self.ikb(text="sʜᴜғғʟᴇ",    callback_data="help_shuffle",      style=ButtonStyle.PRIMARY),
                    self.ikb(text="ᴘɪɴɢ",        callback_data="help_ping",         style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(text="sᴛᴀᴛs",       callback_data="help_stats",        style=ButtonStyle.PRIMARY),
                    self.ikb(text="sᴜᴅᴏ",        callback_data="help_sudo",         style=ButtonStyle.PRIMARY),
                    self.ikb(text="ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ", callback_data="help_maintenance", style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(
                        text="• ʙᴀᴄᴋ •",
                        callback_data="start",
                        style=ButtonStyle.SUCCESS,
                    ),
                ],
            ]
        return self.ikm(rows)

    def langs_markup(self) -> types.InlineKeyboardMarkup:
        langs = [
            ("🇬🇧 English",    "en"), ("🇮🇳 Hindi",      "hi"),
            ("🇮🇳 Telugu",     "te"), ("🇰🇷 Korean",     "ko"),
            ("🇲🇲 Myanmar",    "my"), ("🇮🇩 Indonesian", "id"),
            ("🇵🇹 Portuguese", "pt"), ("🇸🇦 Arabic",     "ar"),
            ("🇪🇸 Spanish",    "es"), ("🇫🇷 French",     "fr"),
            ("🇷🇺 Russian",    "ru"), ("🇩🇪 German",     "de"),
            ("🇹🇷 Turkish",    "tr"), ("🇧🇩 Bengali",    "bn"),
            ("🇹🇭 Thai",       "th"), ("🇻🇳 Vietnamese", "vi"),
            ("🇯🇵 Japanese",   "ja"), ("🇨🇳 Chinese",    "zh"),
            ("🇵🇰 Urdu",       "ur"), ("🇮🇷 Persian",    "fa"),
            ("🇮🇳 Bhojpuri",   "bho"), ("🇳🇵 Nepali",     "ne"),
        ]
        rows = []
        for i in range(0, len(langs), 2):
            row = [self.ikb(text=langs[i][0], callback_data=f"setlang_{langs[i][1]}", style=ButtonStyle.PRIMARY)]
            if i + 1 < len(langs):
                row.append(self.ikb(text=langs[i + 1][0], callback_data=f"setlang_{langs[i + 1][1]}", style=ButtonStyle.PRIMARY))
            rows.append(row)
        rows.append([self.ikb(
            text="• ʙᴀᴄᴋ •",
            callback_data="start",
            style=ButtonStyle.SUCCESS,
        )])
        return self.ikm(rows)

    # FIX #1: 'text' param ab actually use ho raha hai (status row me)
    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(
                    text=f"{text}",
                    callback_data="ping_refresh",
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                self.ikb(text="  ᴄʜᴀɴɴᴇʟ", url=config.SUPPORT_CHANNEL, style=ButtonStyle.PRIMARY),
                self.ikb(text="  sᴜᴘᴘᴏʀᴛ",  url=config.SUPPORT_CHAT,    style=ButtonStyle.PRIMARY),
            ],
            [
                self.ikb(
                    text="ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ",
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=ButtonStyle.SUCCESS,
                ),
            ],
        ])

    # FIX #2: 'item_id' ab callback_data me pass ho raha hai taaki
    # multi-track queue me sahi item control ho (galat item na dabe)
    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(text="▷",   callback_data=f"controls resume {chat_id} {item_id}", style=ButtonStyle.SUCCESS),
                self.ikb(text="II",  callback_data=f"controls pause {chat_id} {item_id}",  style=ButtonStyle.PRIMARY),
                self.ikb(text="↻",   callback_data=f"controls replay {chat_id} {item_id}", style=ButtonStyle.SUCCESS),
                self.ikb(text="⏭", callback_data=f"controls skip {chat_id} {item_id}",   style=ButtonStyle.PRIMARY),
                self.ikb(text="⏹",   callback_data=f"controls stop {chat_id} {item_id}",   style=ButtonStyle.DANGER),
            ],
        ])

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(
                text=_text,
                callback_data=f"controls {_action} {chat_id} q",
                style=ButtonStyle.SUCCESS,
            )]]
        )

    # FIX #3: 'language' ab ek row me display ho raha hai
    def settings_markup(
        self, lang: dict, admin_only: bool, force_admin: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        play_mode_txt  = lang["admin_only_txt"] if admin_only  else lang["everyone"]
        force_mode_txt = lang["admin_only_txt"] if force_admin else lang["everyone"]
        return self.ikm([
            [
                self.ikb(text="  " + lang["play_mode"],  callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text=play_mode_txt,               callback_data="playmode",                   style=ButtonStyle.SUCCESS),
            ],
            [
                self.ikb(text="  " + lang["force_mode"], callback_data=f"controls status {chat_id}", style=ButtonStyle.PRIMARY),
                self.ikb(text=force_mode_txt,              callback_data="forcemode",                  style=ButtonStyle.SUCCESS),
            ],
            [
                self.ikb(text="" + language.upper(),  callback_data="help_langs", style=ButtonStyle.PRIMARY),
            ],
        ])

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text="" + lang["add_me"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=ButtonStyle.PRIMARY,
                )
            ],
            [
                self.ikb(text="  " + lang["help"],  callback_data="help"),
            ],
            [
                self.ikb(text="  " + lang["support"], url=config.SUPPORT_CHAT),
                self.ikb(text=" " + lang["channel"], url=config.SUPPORT_CHANNEL),
            ],
            [
                self.ikb(text="ʟᴀɴɢᴜᴀɢᴇ",  callback_data="help_langs"),
                self.ikb(text="ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://github.com/elevenyts/ArtistMusic"),
            ],
        ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(text="ᴄᴏᴘʏ ʟɪɴᴋ",     copy_text=link, style=ButtonStyle.PRIMARY),
                self.ikb(text="ᴏᴘᴇɴ ɪɴ ʏᴛ", url=link,       style=ButtonStyle.DANGER),
            ],
        ])

