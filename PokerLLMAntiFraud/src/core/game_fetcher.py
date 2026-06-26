import re
from typing import Optional
from PokerLLMAntiFraud.src.models.schemas import GameData

class GameFetcher:
    """Fetches and parses poker games from hand history strings"""

    ACTION_MAP = {
        'BT': 'bets',
        'CL': 'calls',
        'RS': 'raises',
        'CH': 'checks',
        'F': 'folds',
        'FS': 'folds and shows',
        'FF': 'fast folds',
        'SB': 'posts small blind',
        'BB': 'posts big blind',
        'EB': 'posts extra blind',
        'AN': 'posts ante',
        'SR': 'posts straddle',
        'BI': 'posts bring-in',
    }

    async def fetch_single_game(self, game_id: str) -> GameData:
        """
        Parse raw hand history string into structured GameData.

        Args:
            game_id: Game id to fetch

        Returns:
            GameData with parsed game information
        """

        # Temporary test data
        from PokerLLMAntiFraud.src.data_sources.test_game import get_test_game
        raw_game = get_test_game()

        return self._parse_hand_history(raw_game)

    def _parse_hand_history(self, raw_text: str) -> GameData:
        """
        Parse raw hand history text into structured format.
        """
        lines = raw_text.strip().split('\n')

        game_data = {
            "game_type": "Unknown",
            "blinds": {"small": 0.0, "big": 0.0},
            "players": [],
            "dealt_cards": {},
            "actions": [],
            "community_cards": [],
            "result": {
                "winner": "Unknown",
                "pot": 0.0,
                "rake": 0.0
            },
            "raw_hand_history": raw_text
        }

        players_info = {}  # seat -> {"name": str, "stack": float}
        current_pot = 0.0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse seat info: "S 5 5550 6158 john"
            if line.startswith('S '):
                parts = line.split()
                if len(parts) >= 5:
                    seat = int(parts[1])
                    stack = float(parts[2]) / 100  # Convert cents to dollars
                    player_id = parts[3]
                    name = parts[4]
                    players_info[seat] = {"name": name, "stack": stack}
                    self._ensure_player(game_data, name)

            # Parse sit down: "SD 3 486 john"
            elif line.startswith('SD '):
                parts = line.split()
                if len(parts) >= 4:
                    seat = int(parts[1])
                    name = parts[3]
                    players_info[seat] = {"name": name, "stack": 0.0}
                    self._ensure_player(game_data, name)

            # Legacy format: "0  Player Debajitb plays at seat 0 with 9.99"
            elif 'plays at seat' in line and 'Player' in line:
                parts = line.split()
                # "0 Player Debajitb plays at seat 0 with 9.99"
                #  0    1         2     3   4   5    6   7    8
                # seat number is at index 6
                name = parts[2]
                seat = int(parts[6])
                stack = float(parts[-1])
                players_info[seat] = {"name": name, "stack": stack}
                self._ensure_player(game_data, name)

            # Parse game type: "GT 72 F"
            elif line.startswith('GT '):
                game_data["game_type"] = self._parse_game_type(line)

            # Parse blinds: "LI 1 100 200 45"
            elif line.startswith('LI '):
                parts = line.split()
                if len(parts) >= 4:
                    game_data["blinds"]["small"] = float(parts[2]) / 100
                    game_data["blinds"]["big"] = float(parts[3]) / 100

            # Parse cards dealt to player: "C 2 44 Kc"
            elif line.startswith('C '):
                parts = line.split()
                if len(parts) >= 4:
                    seat = int(parts[1])
                    card = parts[3]
                    if seat in players_info:
                        player_name = players_info[seat]["name"]
                        if player_name not in game_data["dealt_cards"]:
                            game_data["dealt_cards"][player_name] = []
                        game_data["dealt_cards"][player_name].append(card)

            # Legacy card format: "Dealt to player Debajitb : 8 of clubs"
            elif 'Dealt to player' in line:
                match = re.match(r'Dealt to player (\w+)\s*:\s*(.+)', line)
                if match:
                    player_name = match.group(1)
                    card = match.group(2).strip()
                    if player_name not in game_data["dealt_cards"]:
                        game_data["dealt_cards"][player_name] = []
                    game_data["dealt_cards"][player_name].append(card)

            # Parse community cards: "D 17 6d"
            elif line.startswith('D '):
                parts = line.split()
                if len(parts) >= 3:
                    card = parts[2]
                    game_data["community_cards"].append(card)

            # Legacy community card: "Card dealt to table: 9 of diamonds"
            elif 'Card dealt to table:' in line:
                card = line.split(': ')[-1].strip()
                game_data["community_cards"].append(card)

            # Parse pot: "B 100 1862" (bets added, pot now...)
            elif line.startswith('B '):
                parts = line.split()
                if len(parts) >= 3:
                    current_pot = float(parts[2]) / 100

            # Parse player won: "PW 0 490"
            elif line.startswith('PW '):
                parts = line.split()
                if len(parts) >= 3:
                    seat = int(parts[1])
                    amount = float(parts[2]) / 100
                    game_data["result"]["pot"] = amount
                    if seat in players_info:
                        game_data["result"]["winner"] = players_info[seat]["name"]

            # Parse pot to player: "PP 2 400 0"
            elif line.startswith('PP '):
                parts = line.split()
                if len(parts) >= 3:
                    seat = int(parts[1])
                    amount = float(parts[2]) / 100
                    game_data["result"]["pot"] += amount
                    if seat in players_info:
                        game_data["result"]["winner"] = players_info[seat]["name"]

            # Parse rake: "PR 40 0"
            elif line.startswith('PR '):
                parts = line.split()
                if len(parts) >= 2:
                    game_data["result"]["rake"] += float(parts[0]) / 100

            # Legacy rake: "Rake was taken 0.75"
            elif 'Rake was taken' in line:
                rake = float(line.split()[-1])
                game_data["result"]["rake"] = rake

            # Legacy winner: "Player Debajitb wins"
            elif 'wins' in line and 'Player' in line:
                match = re.search(r'Player (\w+) wins', line)
                if match:
                    game_data["result"]["winner"] = match.group(1)

            # Legacy pot: "collects main pot 12.85"
            elif 'collects main pot' in line or 'collects pot' in line:
                pot = float(line.split()[-1])
                game_data["result"]["pot"] = max(game_data["result"]["pot"], pot)

            # Parse actions (betting mnemonics)
            else:
                action = self._parse_action(line, players_info)
                if action:
                    game_data["actions"].append(action)

        # If pot not found in standard format, calculate from actions
        if game_data["result"]["pot"] == 0.0 and current_pot > 0:
            game_data["result"]["pot"] = current_pot

        return GameData(game_data=game_data)

    def _ensure_player(self, game_data: dict, player_name: str):
        """Add player to game_data if not already present"""
        if not any(p['name'] == player_name for p in game_data["players"]):
            game_data["players"].append({
                "name": player_name,
                "final_result": "unknown"
            })

    def _parse_game_type(self, gt_line: str) -> str:
        """Parse GT mnemonic into human-readable game type"""
        # Basic implementation - can be extended
        game_types = {
            '72': 'Heads-up No Limit Texas Hold\'em',
            '71': '6-max No Limit Texas Hold\'em',
            '70': '9-max No Limit Texas Hold\'em',
        }
        parts = gt_line.split()
        if len(parts) >= 2:
            type_code = parts[1]
            return game_types.get(type_code, f"Game type {type_code}")
        return "Unknown"

    def _parse_action(self, line: str, players_info: dict) -> Optional[str]:
        """Parse a single line into human-readable action description"""
        parts = line.split()
        if len(parts) < 2:
            return None

        # Try to parse mnemonic format
        code = parts[0]

        # Legacy format: "19  Player Debajitb raises 6.70 to 6.80"
        legacy_match = re.match(
            r'(\d+)\s+Player\s+(\w+)\s+(calls|raises|checks|folds|posts|bets)\s*(.*)',
            line
        )
        if legacy_match:
            player = legacy_match.group(2)
            action = legacy_match.group(3)
            details = legacy_match.group(4).strip()
            return f"Player {player} {action} {details}".strip()

        # Check if it's a known mnemonic code
        if code in self.ACTION_MAP:
            action_name = self.ACTION_MAP[code]

            # Different mnemonics have different formats
            if code in ('SB', 'BB', 'EB', 'AN', 'SR', 'BI'):
                # Format: "SB 4 250"
                if len(parts) >= 3:
                    seat = int(parts[1])
                    amount = float(parts[2]) / 100
                    player = players_info.get(seat, {}).get("name", f"Seat {seat}")
                    return f"Player {player} {action_name} {amount}"

            elif code in ('BT', 'CL', 'RS'):
                # Format: "BT 4 250"
                if len(parts) >= 3:
                    seat = int(parts[1])
                    amount = float(parts[2]) / 100
                    player = players_info.get(seat, {}).get("name", f"Seat {seat}")
                    if code == 'RS' and len(parts) >= 4:
                        to_amount = float(parts[3]) / 100
                        return f"Player {player} {action_name} {amount} to {to_amount}"
                    return f"Player {player} {action_name} {amount}"

            elif code in ('CH', 'F', 'FS', 'FF'):
                # Format: "F 3"
                if len(parts) >= 2:
                    seat = int(parts[1])
                    player = players_info.get(seat, {}).get("name", f"Seat {seat}")
                    return f"Player {player} {action_name}"

        return None