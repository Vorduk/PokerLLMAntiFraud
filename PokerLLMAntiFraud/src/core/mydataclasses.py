from datetime import datetime
from dataclasses import dataclass, field
from typing import List

@dataclass
class FraudGame:
    """Game linked to a fraud incident"""
    game_id: str
    participants_ids: List[int] = field(default_factory=list)
    confidence: int = 0


@dataclass
class FraudIncident:
    """Fraud incident from admin panel"""
    id: str
    date_created: datetime
    date_updated: datetime
    incident_type: str
    confidence: int
    participants_ids: List[int] = field(default_factory=list)
    games: List[FraudGame] = field(default_factory=list)


@dataclass
class FraudRecord:
    """One record in the .xlsx table file"""
    time: datetime
    game_id: int
    description: str
    incident_types: List[str] = field(default_factory=list)
    participants_ids: List[int] = field(default_factory=list)


