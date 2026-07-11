from datetime import datetime
from dataclasses import dataclass
from typing import List

@dataclass
class FraudRecord:
    """One record in the .xlsx table file"""
    time: datetime
    game_id: str
    incident_types: List[str]
    player_nicknames: List[str]
    description: str