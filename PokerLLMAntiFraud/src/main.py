import asyncio
from core import FraudDetectionManager, GameFetcher, AIAnalyzer, TableFormatter
import os
from config import ConfigLoader
from models import ModelFactory
from ui import ConsoleUI

async def main():
    print("Poker fraud AI detection system")

    # Initialize components
    config = ConfigLoader()
    factory = ModelFactory(config)

    base_url = os.getenv('GAME_FETCHER_BASE_URL')
    session_id = os.getenv('SESSION_ID')
    if (not base_url) or (not session_id):
        raise ValueError("GAME_FETCHER_BASE_URL or SESSION_ID not set in .env")
    game_fetcher = GameFetcher(base_url, session_id)
    ai_analyzer = AIAnalyzer(factory)
    table_formatter = TableFormatter()
    orchestrator = FraudDetectionManager(game_fetcher, ai_analyzer, table_formatter)

    #create console
    console_ui = ConsoleUI(orchestrator)
    try:
        await console_ui.run()
    finally:
        await game_fetcher.close()
        table_formatter.flush()

if __name__ == "__main__":
    asyncio.run(main())
