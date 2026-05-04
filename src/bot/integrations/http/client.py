import aiohttp

class HttpClient:
    async def get_json(self, url: str, *, headers: dict | None = None) -> dict:
        raise NotImplementedError

    async def get_text(self, url: str, *, headers: dict | None = None) -> str:
        raise NotImplementedError

    async def post_form(
        self,
        url: str,
        *,
        data: dict,
        headers: dict | None = None
    ) -> dict:
        raise NotImplementedError


class AioHttpClient(HttpClient):
    def __init__(self):
        super().__init__()
        self._session: aiohttp.ClientSession | None = None


    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()
            self._session = None

    @property
    def session(self):
        if self._session is None:
            raise RuntimeError("AioHttpClient must be used as an async context manager")
        return self._session


    async def get_json(self, url: str, *, headers=None) -> dict:
        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return {}
            return await resp.json()

    async def get_text(self, url: str, *, headers=None) -> str:
        async with self.session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return ""
            return await resp.text()

    async def post_form(self, url: str, *, data: dict, headers=None) -> dict:
        async with self.session.post(url, data=data, headers=headers) as resp:
            if resp.status != 200:
                return {}
            return await resp.json()
        

    async def fetch_avatar_image_data(self, url):
        async with self.session.get(url) as response:
            if response.status != 200:
                return None
            content = await response.read()
            return content