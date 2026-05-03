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
        self.session = aiohttp.ClientSession()

    async def close(self):
        if not self.session.closed:
            await self.session.close()

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
            content = await response.read()
            return content