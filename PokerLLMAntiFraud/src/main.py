import asyncio
import os
import aiohttp
from .core import FraudDetectionManager, GameFetcher, AIAnalyzer, TableFormatter
from .config import ConfigLoader
from .models import ModelFactory
from .ui import ConsoleUI
from .core.auth import Authenticator

async def main():
    print("Poker fraud AI detection system")

    config = ConfigLoader()
    factory = ModelFactory(config)

    base_url = os.getenv('GAME_FETCHER_BASE_URL')
    login = os.getenv('LOGIN')
    password = os.getenv('PASSWORD')
    if not base_url or not login or not password:
        raise ValueError("GAME_FETCHER_BASE_URL, LOGIN, and PASSWORD must be set in .env")

    auth = Authenticator(base_url, login, password)
    cookies = await auth.get_cookies()
    session_id = cookies.get('PHPSESSID')

    headers = {
        'Accept': 'application/vnd.api+json',
        'Content-Type': 'application/vnd.api+json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
        'Referer': f'{base_url}/webadmin-5rd/antifraud/incidents',
    }
    session = aiohttp.ClientSession(cookies=cookies, headers=headers)

    game_fetcher = GameFetcher(base_url, session, session_id)   # передаём session_id
    ai_analyzer = AIAnalyzer(factory)
    table_formatter = TableFormatter()
    orchestrator = FraudDetectionManager(game_fetcher, ai_analyzer, table_formatter)

    console_ui = ConsoleUI(orchestrator)
    try:
        await console_ui.run()
    finally:
        await game_fetcher.close()
        table_formatter.flush()

if __name__ == "__main__":
    asyncio.run(main())