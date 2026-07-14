import json
from pathlib import Path
from typing import Dict, Optional
import aiohttp

class Authenticator:

    def __init__(self, base_url: str, login: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.login = login
        self.password = password
        self.session_file = Path(__file__).parent.parent.parent / "session.json"
        self.login_url = f"{self.base_url}/webadmin-5rd/"

    async def get_cookies(self) -> Dict[str, str]:
        saved = self._load_session()
        if saved and await self._is_session_valid(saved):
            return saved

        cookies = await self._login()
        self._save_session(cookies)
        return cookies

    async def _login(self) -> Dict[str, str]:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            # 1. GET страницы входа – получаем PHPSESSID и прочие куки
            async with session.get(self.login_url) as resp:
                resp.raise_for_status()

            # 2. POST с данными формы
            post_data = {
                'login': self.login,
                'password': self.password,
                'lang': 'ru',
                'goto': '/webadmin-5rd/',
                'browserLocale': 'ru',
                'submitBtn': 'Отправить',
            }
            headers['Referer'] = self.login_url
            headers['Content-Type'] = 'application/x-www-form-urlencoded'

            async with session.post(self.login_url, data=post_data,
                                    headers=headers, allow_redirects=False) as resp:
                if resp.status not in (200, 302):
                    raise Exception(f"Login failed with status {resp.status}")

            # 3. Собираем все куки, которые теперь есть в сессии
            all_cookies = {}
            for cookie in session.cookie_jar:
                # cookie имеет атрибуты .key и .value
                all_cookies[cookie.key] = cookie.value

            if 'PHPSESSID' not in all_cookies:
                raise Exception("PHPSESSID not found after login")
            return all_cookies

    async def _is_session_valid(self, cookies: Dict[str, str]) -> bool:
        try:
            async with aiohttp.ClientSession(cookies=cookies) as session:
                url = f"{self.base_url}/apiweb/fraud-incidents?itemsPerPage=1"
                headers = {
                    'Accept': 'application/vnd.api+json',
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': f"{self.base_url}/webadmin-5rd/antifraud/incidents",
                }
                async with session.get(url, headers=headers) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def _save_session(self, cookies: Dict[str, str]):
        with open(self.session_file, 'w') as f:
            json.dump(cookies, f)

    def _load_session(self) -> Optional[Dict[str, str]]:
        if self.session_file.exists():
            try:
                with open(self.session_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return None