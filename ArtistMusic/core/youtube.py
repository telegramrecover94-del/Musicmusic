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

import os
import re
import glob
import time
import yt_dlp
import random
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Union

from pyrogram import enums, types
from py_yt import VideosSearch
from ArtistMusic import config, logger


class YouTube:
    def __init__(self):
        """Initialize YouTube handler with configuration and caching."""
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.warned = False

        # Get API configuration from config
        self.api_url = config.ARTISTBOTS_API_URL
        self.artistbots_key = config.ARTISTBOTS_KEY
        self.enable_api = config.ENABLE_API
        self.enable_cookies_fallback = config.ENABLE_COOKIES_FALLBACK
        self.api_timeout = config.API_TIMEOUT
        self.api_stream_timeout = config.API_STREAM_TIMEOUT

        # Regular expression to match YouTube URLs
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|live/|embed/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

        # Cache search results (10 minute TTL)
        self.search_cache = {}
        self._download_semaphore = asyncio.Semaphore(5)
        self._max_video_height = config.VIDEO_MAX_HEIGHT

        # Log configuration
        logger.info("=" * 50)
        logger.info("📹 YouTube Handler Initialized")
        logger.info(f"🎵 API Priority: {'ENABLED' if self.enable_api else 'DISABLED'}")
        if self.enable_api:
            logger.info(f"🔗 API URL: {self.api_url}")
            if self.artistbots_key:
                masked_key = self.artistbots_key[:8] + "..." if len(self.artistbots_key) > 8 else "***"
                logger.info(f"🔑 API Key: {masked_key}")
            else:
                logger.warning("⚠️ No API Key configured!")
        logger.info(f"🍪 Cookies Fallback: {'ENABLED' if self.enable_cookies_fallback else 'DISABLED'}")
        logger.info("=" * 50)

    async def search(self, query: str, max_results: int = 1):
        """Search YouTube for videos."""
        try:
            results = VideosSearch(query, limit=max_results)
            dict_result = await results.next()
            result_list = dict_result.get("result", [])
            
            if not result_list:
                return None, None
            
            item = result_list[0]
            title = item.get("title")
            vidid = item.get("id")
            
            return title, vidid
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
            return None, None

    def _locate_download_file(self, video_id: str, video: bool = False) -> Optional[str]:
        """Locate any completed download file for a video id."""
        pattern = f"downloads/{video_id}*"
        candidates = sorted([
            path for path in glob.glob(pattern)
            if not path.endswith((".part", ".ytdl", ".info.json", ".temp"))
        ])

        video_exts = {".mp4", ".mkv", ".webm", ".mov"}
        audio_exts = {".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav", ".flac"}

        if video:
            for path in candidates:
                if os.path.isdir(path):
                    continue
                if Path(path).suffix.lower() in video_exts:
                    return path
        else:
            for path in candidates:
                if os.path.isdir(path):
                    continue
                if Path(path).suffix.lower() in audio_exts:
                    return path

        for path in candidates:
            if os.path.isdir(path):
                continue
            return path
        return None

    def get_cookies(self):
        """Get random cookie file from cookies directory."""
        if not self.checked:
            cookies_dir = "ArtistMusic/cookies"
            if os.path.exists(cookies_dir):
                for file in os.listdir(cookies_dir):
                    if file.endswith(".txt"):
                        self.cookies.append(file)
            self.checked = True
        
        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("🍪 Cookies are missing; downloads might fail.")
            return None
        
        cookie_file = f"ArtistMusic/cookies/{random.choice(self.cookies)}"
        return cookie_file

    async def download_via_cookies(self, video_id: str, video: bool = False) -> Optional[str]:
        """Download audio/video using yt-dlp with cookies and proxy."""
        if not self.enable_cookies_fallback:
            return None

        url = self.base + video_id
        async with self._download_semaphore:
            cookie = self.get_cookies()
            proxy_url = os.getenv("PROXY", "http://soucwyed:xa8j3kvuna24@31.59.20.176:6754")
            
            base_opts = {
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "geo_bypass": True,
                "no_warnings": True,
                "overwrites": False,
                "nocheckcertificate": True,
                "proxy": proxy_url,
                "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
            }

            if video:
                ydl_opts = {**base_opts, "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best"}
            else:
                ydl_opts = {**base_opts, "format": "bestaudio[ext=m4a]/bestaudio/best"}

            ydl_opts_cookie = {**ydl_opts, "cookiefile": cookie} if cookie else ydl_opts

            def _download(opts):
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.extract_info(url, download=True)
                    return self._locate_download_file(video_id, video=video)
                except Exception as ex:
                    logger.warning(f"Download error: {ex}")
                    return self._locate_download_file(video_id, video=video)

            return await asyncio.to_thread(_download, ydl_opts_cookie)

    def valid(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        return bool(re.match(self.regex, url))

    def url(self, message_1: types.Message) -> Union[str, None]:
        """Extract YouTube URL from message."""
        messages = [message_1]
        link = None
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)

        for message in messages:
            text = message.text or message.caption or ""
            if message.entities:
                for entity in message.entities:
                    if entity.type == enums.MessageEntityType.URL:
                        link = text[entity.offset: entity.offset + entity.length]
                        break
            if link:
                break
        return link
        
