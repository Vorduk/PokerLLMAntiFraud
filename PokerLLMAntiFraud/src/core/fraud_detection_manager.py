from .game_fetcher import GameFetcher
from .ai_analyzer import AIAnalyzer
from .mydataclasses import FraudRecord
from typing import List
from PokerLLMAntiFraud.src.models import GameData
from .table_formatter import TableFormatter


class FraudDetectionManager:
    """Main orchestrator class

    Fetches games, sends them to ai models, gets results.
    """

    def __init__(self, game_fetcher: GameFetcher, ai_analyzer: AIAnalyzer, table_formatter: TableFormatter):
        self.fetcher = game_fetcher
        self.analyzer = ai_analyzer
        self.model_id = "@cf/google/gemma-4-26b-a4b-it"
        self.table_formatter = table_formatter

    async def step(self):
        incidents = await self.fetcher.fetch_new_incidents(1000) # Incidents (contain many games)
        if not incidents:
            print("No new incidents")
            return

        records: List[FraudRecord] = [] # To write in table file

        for inc in incidents: # Check ALL incidents
            for game in inc.games: # Check ALL games in particular incident

                try:
                    game_data : GameData = await self.fetcher.fetch_single_game(game.game_id)
                except Exception as e:
                    print(f"Error fetching game {game.game_id}: {e}")
                    continue

                if not game_data.participants:
                    record = FraudRecord(
                        time=inc.date_updated,
                        game_id=game_data.game_id,
                        incident_types=[],
                        participants_ids=game.participants_ids,
                        description="Insufficient data for analysis"
                    )
                    records.append(record)
                    continue

                try:
                    response = await self.analyzer.analyze_game(game_data, self.model_id)
                except Exception as e:
                    print(f"Error analyzing {game_data.game_id}: {e}")
                    continue

                record = FraudRecord(
                    time=inc.date_updated,
                    game_id=game_data.game_id,
                    incident_types=response.incident_types,
                    participants_ids=game.participants_ids,
                    description=response.reasoning,
                )
                records.append(record)

                if record:
                    self.table_formatter.save_result(records)

    def set_model(self, model_id: str):
        self.model_id = model_id

