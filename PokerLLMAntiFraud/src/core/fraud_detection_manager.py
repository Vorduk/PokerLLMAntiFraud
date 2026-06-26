from .game_fetcher import GameFetcher
from .ai_analyzer import AIAnalyzer
from PokerLLMAntiFraud.src.models.schemas import FraudDetectionResponse

class FraudDetectionManager:
    """Main orchestrator class

    Fetches games, sends them to ai models, gets results.
    """

    def __init__(self, game_fetcher: GameFetcher, ai_analyzer: AIAnalyzer):
        self.fetcher = game_fetcher
        self.analyzer = ai_analyzer

    async def detect_fraud_single_game(self, game_id: str, model_id: str) -> FraudDetectionResponse:
        """Analyze a single game"""
        game = await self.fetcher.fetch_single_game(game_id)
        return await self.analyzer.analyze_game(game, model_id)