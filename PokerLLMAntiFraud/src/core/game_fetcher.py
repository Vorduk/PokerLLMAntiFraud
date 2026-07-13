from PokerLLMAntiFraud.src.core.mydataclasses import FraudIncident, FraudGame
from PokerLLMAntiFraud.src.models.mydataclasses import GameData, Participant
import re
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

class GameFetcher:
    def __init__(self, base_url: str, session_id: str = None):
        self.base_url = base_url.rstrip('/')
        self.session_id = session_id
        self._processed_incidents_ids: set = set()
        self._processed_game_ids: set = set()
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._http_session is None:
            self._http_session = aiohttp.ClientSession(
                cookies={'PHPSESSID': self.session_id} if self.session_id else {},
                headers={
                    'Accept': 'application/vnd.api+json',
                    'Content-Type': 'application/vnd.api+json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0',
                    'Referer': f'{self.base_url}/webadmin-5rd/antifraud/incidents',
                }
            )
        return self._http_session

    async def close(self):
        if self._http_session:
            await self._http_session.close()
            self._http_session = None

    # Real API fetching of fraud incidents
    async def fetch_new_incidents(self, lookback_minutes: int) -> List[FraudIncident]:
        session = await self._get_session()
        now = datetime.now(timezone.utc)
        from_time = now - timedelta(minutes=lookback_minutes)

        # Get the list of incidents (without metadata)
        list_params = {
            'include': '_type,status,participants',  # metadata is not needed here
            'itemsPerPage': '20',
            'page': '1',
            'order[updatedAtStamp]': 'desc',
            'from': from_time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            'to': now.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            '_SESSID': self.session_id,
        }
        url = f'{self.base_url}/apiweb/fraud-incidents'
        new_incidents = []

        # Iterate through the list pages
        while url:
            async with session.get(url, params=list_params if '?' not in url else None) as resp:
                resp.raise_for_status()
                list_data = await resp.json()

            # Process each incident in the list
            for inc_summary in list_data.get('data', []):
                inc_id = inc_summary['id']  # full path /apiweb/fraud-incidents/...
                internal_id = inc_summary['attributes']['_id']  # numeric ID
                if inc_id in self._processed_incidents_ids:
                    continue

                # Request incident details (with metadata)
                detail_url = f'{self.base_url}/apiweb/fraud-incidents/{internal_id}'
                detail_params = {
                    'include': '_type,status,participants,metadata,notes,lastStatusSetBy',
                    '_SESSID': self.session_id,
                }
                async with session.get(detail_url, params=detail_params) as detail_resp:
                    detail_resp.raise_for_status()
                    detail_data = await detail_resp.json()

                # Parse the details
                incident = self._parse_incident_detail(detail_data)
                if incident:
                    new_incidents.append(incident)
                    self._processed_incidents_ids.add(inc_id)

            # Pagination
            links = list_data.get('links', {})
            next_url = links.get('next')
            if next_url:
                url = f"{self.base_url}{next_url}"
                list_params = None
            else:
                url = None

        return new_incidents

    def _parse_incident_detail(self, detail_data: dict) -> Optional[FraudIncident]:
        """Extracts FraudIncident from the full JSON of a single incident."""
        if 'data' not in detail_data:
            return None
        inc_data = detail_data['data']
        attrs = inc_data['attributes']
        rels = inc_data.get('relationships', {})
        included_map = {item['id']: item for item in detail_data.get('included', [])}

        # Incident type
        type_id = rels['_type']['data']['id']
        type_obj = included_map.get(type_id, {})
        incident_type = type_obj.get('attributes', {}).get('name', 'Unknown')

        # Dates
        date_created = datetime.fromisoformat(attrs['createdAtStamp'].replace('+00:00', '+00:00'))
        date_updated = datetime.fromisoformat(attrs['updatedAtStamp'].replace('+00:00', '+00:00'))

        # Confidence
        confidence = int(attrs.get('scoreInPercents', 0))

        # Participants
        participants_ids = []
        for p in rels.get('participants', {}).get('data', []):
            match = re.search(r'/(\d+)$', p['id'])
            if match:
                participants_ids.append(int(match.group(1)))

        # Games from metadata
        games_map: Dict[str, Dict] = {}
        metadata_rels = rels.get('metadata', {}).get('data', [])
        for meta_ref in metadata_rels:
            meta_item = included_map.get(meta_ref['id'])
            if not meta_item or meta_item.get('type') != 'FraudMetadataItem':
                continue
            meta_attrs = meta_item.get('attributes', {})
            meta_type = meta_attrs.get('_type', {})
            # Type 5: Chip dumping game
            if meta_type.get('id') != 5 or meta_type.get('name') != 'Chip dumping game':
                continue
            game_id = meta_attrs.get('value')
            if not game_id:
                continue

            # Link to player
            player_rel = meta_item.get('relationships', {}).get('player', {}).get('data')
            if not player_rel or player_rel.get('type') != 'FraudSuspectPlayer':
                continue
            match = re.search(r'/(\d+)$', player_rel['id'])
            if not match:
                continue
            player_id = int(match.group(1))

            if game_id not in games_map:
                games_map[game_id] = {
                    'game_id': game_id,
                    'participants_ids': set(),
                    'confidence': 0
                }
            games_map[game_id]['participants_ids'].add(player_id)
            game_conf = int(meta_attrs.get('scoreInPercents', 0))
            if game_conf > games_map[game_id]['confidence']:
                games_map[game_id]['confidence'] = game_conf

        games = [
            FraudGame(
                game_id=g['game_id'],
                participants_ids=list(g['participants_ids']),
                confidence=g['confidence']
            )
            for g in games_map.values()
        ]

        return FraudIncident(
            id=inc_data['id'],
            date_created=date_created,
            date_updated=date_updated,
            incident_type=incident_type,
            confidence=confidence,
            participants_ids=participants_ids,
            games=games
        )

    async def fetch_single_game(self, game_id: str) -> GameData:
        """Fetch and parse game HTML page into GameData using positional row indices."""
        url = f"{self.base_url}/webadmin-5rd/game/view/id/{game_id}"
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
            "Referer": f"{self.base_url}/webadmin-5rd/antifraud/incidents",
        }
        cookies = {}
        if self.session_id:
            cookies["PHPSESSID"] = self.session_id

        async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")

        # Locate the main info table – try new layout first, then old
        info_table = soup.find("table", class_="viewing-table")  # new style
        if not info_table:
            info_table = soup.find("table", class_="table-bordered")  # old style
        if not info_table:
            raise ValueError("Main game info table not found")

        # Get all rows (new layout may not have <tbody>)
        rows = info_table.find_all("tr")

        # Helper to extract text from the first td of a given row (old layout fallback)
        def get_td_text(row_index):
            if row_index < len(rows):
                tds = rows[row_index].find_all("td")
                if tds:
                    return tds[0].get_text(strip=True)
            return ""

        # Universal helper: search by <th> text and return the following <td> text
        def get_value_by_label(label):
            for row in rows:
                th = row.find("th")
                if th and th.get_text(strip=True) == label:
                    td = row.find("td")
                    if td:
                        return td.get_text(strip=True)
            # Fallback to old positional indices if label not found
            label_to_index = {
                "ID:": 0, "Стол:": 1, "Начат:": 2, "Остановлен:": 3,
                "Карты:": 4, "Тип:": 5, "Рейк:": 7
            }
            idx = label_to_index.get(label)
            if idx is not None:
                return get_td_text(idx)
            return ""

        # Row indices (0-based) – used as fallback for old layout
        # 0: ID
        # 1: Table
        # 2: Started
        # 3: Stopped
        # 4: Cards
        # 5: Type
        # 6: Second Runout
        # 7: Rake
        # 8: Participants
        # 9: Insurance
        # 10: Insurance Result

        # Parse game ID
        game_id_str = get_value_by_label("ID:")
        match = re.search(r'(\d+)', game_id_str)
        page_game_id = int(match.group(1)) if match else int(game_id)

        # Parse table ID from link
        table_cell = None
        for row in rows:
            th = row.find("th")
            if th and th.get_text(strip=True) == "Стол:":
                table_cell = row.find("td")
                break
        if not table_cell and len(rows) > 1:  # fallback to row 1
            table_cell = rows[1].find("td")
        table_id = 0
        if table_cell:
            a = table_cell.find("a")
            if a:
                match = re.search(r'/id/(\d+)', a.get("href", ""))
                if match:
                    table_id = int(match.group(1))

        # Parse start date
        def parse_date(text):
            try:
                return datetime.strptime(text, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                raise ValueError(f"Invalid datetime format: {text}")

        date_start_str = get_value_by_label("Начат:")
        date_start = parse_date(date_start_str) if date_start_str else None

        # Parse stop date
        date_stop_str = get_value_by_label("Остановлен:")
        date_stop = parse_date(date_stop_str) if date_stop_str else None

        # Parse game type
        game_type = get_value_by_label("Тип:")

        # Parse rake
        rake_str = get_value_by_label("Рейк:")
        # Remove currency symbols, commas and spaces
        clean_rake = re.sub(r'[^\d.\-]', '', rake_str) if rake_str else ''
        rake = float(clean_rake) if clean_rake else 0.0

        # Parse community cards from img titles
        cards = []
        for row in rows:
            th = row.find("th")
            if th and th.get_text(strip=True) == "Карты:":
                td = row.find("td")
                if td:
                    for img in td.find_all("img"):
                        title = img.get("title", "")
                        if title:
                            cards.append(title)
                break
        # Fallback to old row index if not found
        if not cards and len(rows) > 4:
            cards_row = rows[4].find("td")
            if cards_row:
                for img in cards_row.find_all("img"):
                    title = img.get("title", "")
                    if title:
                        cards.append(title)

        # Parse participants from inner table
        participants = []
        # Look for inner table anywhere (new layout puts it inside a <td colspan="2">)
        inner_table = info_table.find("table", class_="inner-table")
        if inner_table:
            for row in inner_table.find_all("tr")[1:]:  # skip header
                cols = row.find_all("td")
                if len(cols) >= 3:
                    try:
                        part_id = int(cols[0].get_text(strip=True))
                    except ValueError:
                        continue
                    a_tag = cols[1].find("a")
                    player_id = 0
                    if a_tag:
                        href = a_tag.get("href", "")
                        match = re.search(r'/id/(\d+)', href)
                        if match:
                            player_id = int(match.group(1))
                    # Stack may contain '$' and commas
                    stack_text = cols[2].get_text(strip=True)
                    clean_stack = re.sub(r'[^\d.\-]', '', stack_text)
                    try:
                        stack = int(float(clean_stack)) if clean_stack else 0
                    except ValueError:
                        stack = 0
                    participants.append(Participant(
                        id=part_id,
                        player_id=player_id,
                        stack_at_hand_end=stack
                    ))

        # Parse raw hand history: combine the <pre> text and the actions table
        raw_history_parts = []
        history_header = soup.find("h2", string="История руки") or soup.find("h3", string="История руки")
        if history_header:
            # Find a proper container that holds both <pre> and the actions table
            # Try common wrapper classes first, then fall back to any parent <div>
            container = history_header.find_parent("div", class_="box") or \
                        history_header.find_parent("div", class_="game-info-hand-history") or \
                        history_header.find_parent("div", class_="row game-info")
            if container is None:
                container = history_header.find_parent("div")  # last resort

            if container:
                # Get text from <pre> if present (new layout uses game-info-hand-history-start)
                pre_tag = container.find("pre")
                if pre_tag:
                    raw_history_parts.append(pre_tag.get_text(separator="\n", strip=True))

                # Get text from the actions table (old layout uses viewing-table, new uses hand-history-table)
                actions_table = container.find("table", class_="viewing-table") or \
                                container.find("table", class_="hand-history-table")
                if actions_table:
                    for row in actions_table.find_all("tr")[1:]:  # skip header
                        cols = row.find_all("td")
                        if len(cols) == 2:
                            second = cols[0].get_text(strip=True)
                            action = cols[1].get_text(strip=True)
                            raw_history_parts.append(f"[{second}s] {action}")

        raw_history = "\n".join(raw_history_parts)

        return GameData(
            game_id=page_game_id,
            table_id=table_id,
            date_start=date_start,
            date_stop=date_stop,
            game_type=game_type,
            rake=rake,
            cards=cards,
            participants=participants,
            raw_hand_history=raw_history
        )
