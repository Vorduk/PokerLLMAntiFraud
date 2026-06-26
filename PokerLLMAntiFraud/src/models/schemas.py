from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class GameData:
    """Game data for analyze"""
    game_data: Dict[str, Any]

@dataclass
class FraudDetectionResponse:
    """Model response"""
    fraud_probability: float
    reasoning: str = ""
    model_used: str = ""

    def __str__(self):
        return f"Fraud probability: {self.fraud_probability:.2%} (by {self.model_used})"