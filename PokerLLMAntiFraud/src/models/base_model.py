from abc import ABC, abstractmethod
from .mydataclasses import GameData, FraudDetectionResponse

class BaseModel(ABC):
    """Base class for all AI models"""

    def __init__(self, model_id: str, provider: str, model_name: str):
        self.model_id = model_id
        self.provider = provider
        self.model_name = model_name

    async def analyze(self, game_data: GameData) -> FraudDetectionResponse:
        prompt = self._build_prompt(game_data)
        raw_response = await self._send_request(prompt)
        response = self._parse_response(raw_response)
        return response

    @abstractmethod
    def _build_prompt(self, game_data: GameData) -> str:
        pass

    @abstractmethod
    async def _send_request(self, prompt: str) -> str:
        pass

    @abstractmethod
    def _parse_response(self, raw_response: str) -> FraudDetectionResponse:
        pass

    def __str__(self):
        return f"{self.model_name} ({self.provider})"