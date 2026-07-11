from .game_fetcher import GameFetcher
from .ai_analyzer import AIAnalyzer
from PokerLLMAntiFraud.src.models.dataclasses import FraudDetectionResponse

class FraudDetectionManager:
    """Main orchestrator class

    Fetches games, sends them to ai models, gets results.
    """

    def __init__(self, game_fetcher: GameFetcher, ai_analyzer: AIAnalyzer):
        self.fetcher = game_fetcher
        self.analyzer = ai_analyzer
        self.model_id = "@cf/google/gemma-4-26b-a4b-it"

    async def detect_fraud_single_game(self, game_id: str) -> FraudDetectionResponse:
        """Analyze a single game"""
        game = await self.fetcher.fetch_single_game(game_id)
        return await self.analyzer.analyze_game(game, self.model_id)

    async def step(self):
        print('step')