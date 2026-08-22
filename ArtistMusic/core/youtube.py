if file.endswith(".txt"):
                        self.cookies.append(file)
            self.checked = True

        if not self.cookies:
            if not self.warned:
                self.warned = True
                logger.warning("🍪 Cookies are missing; downloads might fail.")
            return None

        cookie_file = f"ArtistMusic/cookies/{random.choice(self.cookies)}"
        logger.debug(f"Using cookie file: {cookie_file}")
        return cookie_file

    async def save_cookies(self, urls: list[str]) -> None:
        """Save cookies from URLs to files."""
        logger.info("🍪 Saving cookies from urls...")
        saved_count = 0

        cookies_dir = Path("ArtistMusic/cookies")
        cookies_dir.mkdir(parents=True, exist_ok=True)

        for url in urls:
            try:
                path = cookies_dir / f"cookie{random.randint(10000, 99999)}.txt"

                if "pastebin.com" in url:
                    link = url.replace("pastebin.com", "pastebin.com/raw")
                elif "batbin.me" in url:
                    link = url.replace("batbin.me", "batbin.me/raw")
                else:
                    link = url

                async with aiohttp.ClientSession() as session:
                    async with session.get(link, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status != 200:
                            logger.error(f"❌ Cookie download failed: HTTP {resp.status} from {url}")
                            continue

                        content = await resp.read()
                        if not content or len(content) < 50:
                            logger.error(f"❌ Cookie file empty or invalid from {url}")
                            continue

                        with open(path, "wb") as fw:
                            fw.write(content)

                        if path.exists() and path.stat().st_size > 0:
                            saved_count += 1
                            cookie_filename = path.name
                            if cookie_filename not in self.cookies:
                                self.cookies.append(cookie_filename)
                            logger.info(f"✅ Saved: {cookie_filename} ({len(content)} bytes)")

            except asyncio.TimeoutError:
                logger.error(f"❌ Cookie download timeout from {url}")
            except Exception as e:
                logger.error(f"❌ Cookie download error from {url}: {e}")

        self.checked = True
        if saved_count > 0:
            logger.info(f"✅ Cookies saved successfully! ({saved_count} file(s))")
        else:
            logger.error("❌ No cookies saved! Check COOKIE_URL in .env.")

    async def download_via_api(self, link: str, video: bool = False) -> Optional[str]:
        """Download audio/video using ArtistBots API (Primary Method)."""
        if not self.enable_api:
            logger.debug("API is disabled in config")
            return None

        if not self.api_url:
            logger.debug("ARTISTBOTS_API_URL not configured")
            return None

        # Extract video ID
        if "v=" in link:
            video_id = link.split("v=")[-1].split("&")[0]
        elif "youtu.be" in link:
            video_id = link.split("/")[-1].split("?")[0]
        else:
            video_id = link

        if not video_id or len(video_id) < 3:
            logger.debug(f"Invalid video ID: {video_id}")
            return None

        download_dir = Path("downloads")
        download_dir.mkdir(parents=True, exist_ok=True)

        file_ext = ".mp4" if video else ".mp3"
        file_path = os.path.join(download_dir, f"{video_id}{file_ext}")

        if os.path.exists(file_path):

logger.debug(f"File already exists: {file_path}")
            return file_path

        try:
            download_type = "video" if video else "audio"
            logger.info(f"🚀 [API PRIMARY] Trying ArtistBots API for {video_id} (type: {download_type})")

            params = {
                "url": video_id,
                "type": download_type,
            }

            if self.artistbots_key:
                params["api_key"] = self.artistbots_key
            else:
                logger.warning("No ArtistBots API key configured!")
                return None

            async with aiohttp.ClientSession() as session:
                api_endpoint = f"{self.api_url.rstrip('/')}/download"
                async with session.get(
                    api_endpoint,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.api_stream_timeout),
                ) as response:
                    if response.status != 200:
                        logger.error(f"API returned status {response.status}")
                        return None

                    content_length = response.headers.get("content-length")
                    downloaded = 0
                    last_log = 0

                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(65536):
                            f.write(chunk)
                            downloaded += len(chunk)

                            if downloaded - last_log >= 5 * 1024 * 1024:
                                progress_mb = downloaded / (1024 * 1024)
                                if content_length:
                                    total_mb = int(content_length) / (1024 * 1024)
                                    percent = (downloaded / int(content_length)) * 100
                                    logger.info(f"📊 Progress: {progress_mb:.1f}/{total_mb:.1f} MB ({percent:.1f}%)")
                                else:
                                    logger.info(f"📊 Downloaded: {progress_mb:.1f} MB")
                                last_log = downloaded

                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        logger.info(f"✅ [API SUCCESS] Downloaded: {file_path} ({file_size_mb:.2f} MB)")
                        return file_path
                    else:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return None

        except asyncio.TimeoutError:
            logger.error(f"⏰ API timeout for {video_id}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return None
        except Exception as e:
            logger.error(f"❌ API download failed for {video_id}: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return None

    async def download_via_cookies(self, video_id: str, video: bool = False) -> Optional[str]:
        """Download audio/video using yt-dlp with cookies & proxy (Fallback Method)."""
        if not self.enable_cookies_fallback:
            logger.debug("Cookies fallback is disabled in config")
            return None

        url = self.base + video_id
        existing = self._locate_download_file(video_id, video=video)
        if existing:
            return existing

        downloads_dir = Path("downloads")
        downloads_dir.mkdir(parents=True, exist_ok=True)

        async with self._download_semaphore:
            cookie = self.get_cookies()
            base_opts = {
                "outtmpl": "downloads/%(id)s.%(ext)s",

"quiet": True,
                "noplaylist": True,
                "geo_bypass": True,
                "no_warnings": True,
                "overwrites": False,
                "nocheckcertificate": True,
                "continuedl": True,
                "noprogress": True,
                "concurrent_fragment_downloads": 4,
                "http_chunk_size": 524288,
                "socket_timeout": 30,
                "retries": 2,
                "fragment_retries": 2,
                "extractor_retries": 5,
                "sleep_interval_requests": 1,
                "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
                "proxy": self.proxy,
            }

            if video:
                height_filter = f"[height<={self._max_video_height}]" if self._max_video_height else ""
                format_chain = (
                    f"bestvideo[ext=mp4]{height_filter}+bestaudio[ext=m4a]/"
                    f"bestvideo{height_filter}+bestaudio/"
                    "bestvideo+bestaudio/best"
                )
                ydl_opts = {
                    **base_opts,
                    "format": format_chain,
                    "merge_output_format": "mp4",
                    "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
                }
            else:
                ydl_opts = {
                    **base_opts,
                    "format": "bestaudio[ext=m4a]/bestaudio[acodec=opus]/bestaudio/best",
                    "postprocessors": [],
                }

            ydl_opts_cookie = {
                **ydl_opts,
                "cookiefile": cookie,
            }

            def _download(ydl_runtime_opts):
                ydl_instance = None
                try:
                    ydl_instance = yt_dlp.YoutubeDL(ydl_runtime_opts)
                    ydl_instance.extract_info(url, download=True)
                    time.sleep(0.5)
                    return self._locate_download_file(video_id, video=video)
                except Exception as ex:
                    logger.warning(f"⚠️ Download error for {video_id}: {ex}")
                    return self._locate_download_file(video_id, video=video)
                finally:
                    if ydl_instance:
                        try:
                            ydl_instance.close()
                        except Exception:
                            pass

            logger.info(f"🍪 [COOKIES/PROXY FALLBACK] Downloading {video_id}...")
            result = await asyncio.to_thread(_download, ydl_opts_cookie)

            if result:
                logger.info(f"✅ [FALLBACK SUCCESS] Downloaded: {result}")
            else:
                logger.warning(f"⚠️ [FALLBACK FAILED] Could not download {video_id}")

            return result

    async def download(self, link: str, video: bool = False) -> Optional[str]:
        """Unified download method handling API primary and Cookie/Proxy fallback."""
        if "v=" in link:
            video_id = link.split("v=")[-1].split("&")[0]
        elif "youtu.be" in link:
            video_id = link.split("/")[-1].split("?")[0]
        else:
            video_id = link

        # 1. Check API first
        if self.enable_api:
            file_path = await self.download_via_api(video_id, video=video)
            if file_path:
                return file_path

        # 2. Fallback to yt-dlp (Proxy + Cookies)
        return await self.download_via_cookies(video_id, video=video)

    def valid(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        return bool(re.match(self.regex, url))

    def url(self, message_1: types.Message) -> Union[str, None]:
