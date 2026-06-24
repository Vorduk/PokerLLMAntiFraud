from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class GameData:
    game_data: Dict[str, Any]

@dataclass
class FraudDetectionResponse:
    fraud_probability: str

class BaseModel(ABC):

    def __init__(self, model_name: str = "base model"):
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