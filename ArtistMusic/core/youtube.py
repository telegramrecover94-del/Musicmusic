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
