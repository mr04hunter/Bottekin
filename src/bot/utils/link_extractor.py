from ctypes import cast
import re
import base64
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup, Tag
from typing import TYPE_CHECKING
from bot.error_handler.decorators import external_api_call

if TYPE_CHECKING:
    from bot.config import Config
    from bot.integrations.http.client import HttpClient



class TrackDataExtractor:
    def __init__(self, http: "HttpClient", config: "Config") -> None:
        self.http = http
        self.config = config

    # ---------- PLATFORM DETECTION ----------

    @staticmethod
    def detect_platform(url: str) -> str:
        url = url.lower()

        if re.search(r'(youtube\.com/watch\?v=|youtu\.be/)', url):
            return "youtube"
        if re.search(r'soundcloud\.com/', url):
            return "soundcloud"
        if re.search(r'(spotify\.com.*/track/|spotify\.link/)', url):
            return "spotify"
        if re.search(r'(music\.apple\.com|itunes\.apple\.com)', url):
            return "apple_music"

        return "unknown"

    # ---------- YOUTUBE ----------
    @external_api_call(platform="youtube", fallback="unknown title")
    async def extract_youtube_title(self, url: str) -> str:
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return "unknown title"

        oembed = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        data = await self.http.get_json(oembed)

        return data.get("title", "unknown title")

    def _extract_youtube_id(self, url: str) -> str | None:
        if "youtube.com/watch" in url:
            parsed = urlparse(url)
            return parse_qs(parsed.query).get("v", [None])[0]

        if "youtu.be/" in url:
            return url.split("youtu.be/")[-1].split("?")[0]

        return None

    # ---------- SOUNDCLOUD ----------

    @external_api_call(platform="soundcloud", fallback="unknown title")
    async def extract_soundcloud_title(self, url: str) -> str:
        oembed = f"https://soundcloud.com/oembed?format=json&url={url}"
        data = await self.http.get_json(oembed)
        return data.get("title", "unknown title")

    # ---------- SPOTIFY ----------

    @external_api_call(platform="spotify", fallback="unknown title")
    async def extract_spotify_title(self, url: str) -> str:
        track_id = self._extract_spotify_id(url)
        if not track_id:
            return "unknown title"

        token = await self._get_spotify_token()
        if not token:
            return "unknown title"


        headers = {"Authorization": f"Bearer {token}"}
        data = await self.http.get_json(
            f"https://api.spotify.com/v1/tracks/{track_id}",
            headers=headers,
        )

        if not data:
            return "unknown title"


        return f"{data['name']} - {data['artists'][0]['name']}"

    def _extract_spotify_id(self, url: str) -> str | None:
        match = re.search(r'track/([a-zA-Z0-9]+)', url)
        return match.group(1) if match else None

    async def _get_spotify_token(self) -> str | None:
        auth = f"{self.config.spotify_api_client_id}:{self.config.spotify_api_client_secret}"
        b64 = base64.b64encode(auth.encode()).decode()

        data = await self.http.post_form(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {b64}"},
        )

        return data.get("access_token")

    # ---------- APPLE MUSIC ----------

    async def extract_apple_music_title(self, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html",
        }

        html = await self.http.get_text(url, headers=headers)
        if not html:
            return "unknown title"

        soup = BeautifulSoup(html, "html.parser")

        og = soup.find("meta", property="og:title")
        
        if isinstance(og, Tag) and og.get("content"): 
            return str(og["content"]) 

        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text().replace(" on Apple Music", "").strip()
            return title

        return "unknown title"

    # ---------- MAIN ENTRY ----------

    @external_api_call(platform="multi", fallback=("unknown title", "unknown"))
    async def extract_title(self, url: str) -> tuple[str, str]:
        platform = self.detect_platform(url)

        if platform == "youtube":
            return await self.extract_youtube_title(url), platform
        if platform == "soundcloud":
            return await self.extract_soundcloud_title(url), platform
        if platform == "spotify":
            return await self.extract_spotify_title(url), platform
        if platform == "apple_music":
            return await self.extract_apple_music_title(url), platform

        return "unknown title", "unknown"
