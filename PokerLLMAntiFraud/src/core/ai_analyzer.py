from PokerLLMAntiFraud.src.models.schemas import GameData, FraudDetectionResponse
from PokerLLMAntiFraud.src.models.model_factory import ModelFactory
from PokerLLMAntiFraud.src.models.base_model import BaseModel

class AIAnalyzer:

    def __init__(self, model_factory: ModelFactory):
        self.factory = model_factory

    async def analyze_game(self, game: GameData, model_id: str) -> FraudDetectionResponse:
        """Analyze single game with specified or default model"""
        model = self._get_model(model_id)
        return await model.analyze(game)

    def _get_model(self, model_id: str) -> BaseModel:
        """Get appropriate model instance"""
        return self.factory.create_model(model_id)