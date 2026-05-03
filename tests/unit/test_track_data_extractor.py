from unittest.mock import MagicMock, AsyncMock
import pytest
from bot.utils.link_extractor import TrackDataExtractor
from bot.integrations.http.client import AioHttpClient



class TestTrackDataExtractor:

    @pytest.fixture
    async def mock_http(self):

        async def get_json(url, headers=None):
            return {"title": "Fake Title",
                    "name": "Fake Title",
                    "artists": [{"name":"fake artist"}]}

        async def get_text(url, headers=None):
            return "<html><title>Fake Title</title></html>"

        async def post_form(url, data, headers=None):
            return {"access_token": "fake_token"}
        
        mock_http = MagicMock(spec=AioHttpClient)

        mock_http.get_json = get_json
        mock_http.get_text = get_text
        mock_http.post_form = post_form

        return mock_http

    @pytest.fixture
    async def extractor(self, mock_http, test_config):
        extractor = TrackDataExtractor(http=mock_http, config=test_config)
        extractor._get_spotify_token = AsyncMock(return_value="test_token")
        return extractor

    async def test_youtube_link_variations(self, extractor):
        urls = [
            "http://www.youtube.com/watch?v=-wtIMTasddsadCHWuI",
            "http://youtube.com/watch?v=-wtIMdasdasTCHWuI",
            "http://m.youtube.com/watch?v=-wtIdsadaMTCHWuI",
            "https://www.youtube.com/watch?v=lalOyasdasd8Mbfdc",
            "https://youtube.com/watch?v=lalOyasdas8Mbfdc",
            "https://m.youtube.com/watch?v=laasdldasOsady8Mbfdc",
            "http://www.youtube.com/watch?v=dsad&fdsaeature=youtu.be",
            "http://youtube.com/watch?v=lalsaOyasddas8Mbasddc&feature=youtu.be",
            "http://m.youtube.com/watch?v=lalOy8Mbsadsadfdasdc&feature=youtu.be",
            "https://www.youtube.com/watch?v=lalOyasdbfsaddasc&feature=youtu.be",
            "https://youtube.com/watch?v=lalOy8asdsadMaasdsdbfdc&feature=youtu.be",
            "https://m.youtube.com/watch?v=lsadc&feature=youtu.be",
            "http://youtu.be/-wtIMTsadasCHWasduI",

        ]

        for url in urls:
            platform = extractor.detect_platform(url)
            assert platform == "youtube"


    async def test_spotify_link_variations(self, extractor):
        urls = [
            "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp",
            "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp?si=abc123",
            "https://open.spotify.com/track/7ouMYWpwJ422jRcDASZB7P?si=xyz789&utm_source=clipboard",
            "https://open.spotify.com/track/0VjIjW4GlUZAMYd2vXMi3b?context=spotify%3Aalbum%3A12345",
            "https://open.spotify.com/intl-en/track/5ChkMS8OtdzJeqyybCc9R5",
            "https://open.spotify.com/intl-de/track/2TpxZ7JUBn3uw46aR7qd6V",
            "https://open.spotify.com/embed/track/4iV5W9uYEdYUVa79Axb7Rh",
            "https://open.spotify.com/embed/track/1301WleyT98MSxVHPZCA6M?utm_source=generator",

        ]

        for url in urls:
            platform = extractor.detect_platform(url)
            assert platform == "spotify"



    async def test_soundcloud_link_variations(self, extractor):
        urls = [
            "https://soundcloud.com/artistname/track-name?utm_source=clipboard",
            "https://soundcloud.com/user123/cyberpunk-beat?si=abc123",
            "https://soundcloud.com/user123/cyberpunk-beat?in=artistname/sets/album-name",
            "https://soundcloud.com/artistname/track-name",
            "https://soundcloud.com/user123/cyberpunk-beat",
            "https://w.soundcloud.com/player/?url=https%3A//soundcloud.com/artistname/track-name"

        ]

        for url in urls:
            platform = extractor.detect_platform(url)
            assert platform == "soundcloud"


    async def test_applemusic_link_variations(self, extractor):
        urls = [
            "https://music.apple.com/us/album/song-name/1440857781?i=1440857785",
            "https://music.apple.com/tr/album/cyberpunk-track/1234567890?i=1234567891",
            "https://music.apple.com/us/album/song-name/1440857781",
            "https://music.apple.com/us/album/song-name/1440857781?i=1440857785&uo=4",
            "https://music.apple.com/us/album/song-name/1440857781?i=1440857785&app=music",
            "https://music.apple.com/nl/album/song-name/1440857781?i=1440857785",
            "https://music.apple.com/us/album/song-name/1440857781?i="

        ]

        for url in urls:
            platform = extractor.detect_platform(url)
            assert platform == "apple_music"

    async def test_invalid_url_extract_title(self, extractor):

        title, platform = await extractor.extract_title("https://google.com")

        assert title == "unknown title"
        assert platform == "unknown"


    async def test_youtube_extract_title(self, extractor):

        title, platform = await extractor.extract_title("https://youtube.com/watch?v=123")

        assert title == "Fake Title"

    
    async def test_soundcloud_extract_title(self, extractor):

        title, platform = await extractor.extract_title("https://soundcloud.com/some_artist/some_music")

        assert title == "Fake Title"

    

    async def test_spotify_extract_title(self, extractor):

        title, platform = await extractor.extract_title("https://open.spotify.com/track/sdfdsg7asdgsasfasafasf")



        assert platform == "spotify"
        assert title == "Fake Title - fake artist"

    
    async def test_applemusic_extract_title(self, extractor):

        title, platform = await extractor.extract_title("https://music.apple.com/song/sdfsdfsdf")

        assert title == "Fake Title"

    




