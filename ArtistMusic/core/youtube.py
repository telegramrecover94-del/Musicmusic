import os
import yt_dlp

def download_youtube_video(url: str):
    # Railway ke Variables se PROXY_URL lega
    proxy = os.getenv("PROXY_URL")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        # YouTube Bot-Detection bypass karne ke liye generic user-agent
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }

    # Agar Railway me PROXY_URL set hai toh automatically add karega
    if proxy:
        ydl_opts['proxy'] = proxy
        print(" Using Proxy from Railway Variables")
    else:
        print("⚠️ No Proxy found! Running with direct Railway IP")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"⏳ Processing: {url}")
            info = ydl.extract_info(url, download=True)
            print(f" Downloaded Successfully: {info.get('title')}")
            return True
    except Exception as e:
        print(f" Error: {e}")
        return False

if __name__ == "__main__":
    # Test ke liye URL:
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    download_youtube_video(test_url)
