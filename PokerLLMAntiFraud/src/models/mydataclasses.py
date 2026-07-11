from dataclasses import dataclass, field
from typing import List
from datetime import datetime

@dataclass
class Participant:
    id: int
    player_id: int
    stack_at_hand_end: int


@dataclass
class GameData:
    """Game data for analysis"""
    game_id: int
    table_id: int
    date_start: datetime
    date_stop: datetime
    game_type: str
    rake: float
    cards: List[str] = field(default_factory=list)
    participants: List[Participant] = field(default_factory=list)
    raw_hand_history: str = ""


@dataclass
class FraudDetectionResponse:
    """Model response"""
    fraud_probability: int
    reasoning: str = ""
    model_used: str = ""
    incident_types: List[str] = field(default_factory=list)

    def __str__(self):
        return f"Fraud probability: {self.fraud_probability:.2%} (by {self.model_used})"