import json
import aiohttp
from .base_model import BaseModel
from .mydataclasses import GameData, FraudDetectionResponse
import re


class CloudflareModels(BaseModel):
    """Model implementation for Cloudflare Workers AI."""

    def __init__(self, model_id: str, model_name: str, account_id: str, api_key: str, base_url: str, max_tokens: int):
        super().__init__(model_id, "cloudflare", model_name)
        self.account_id = account_id
        self.api_key = api_key
        self.max_tokens = max_tokens
        self.base_url = f"{base_url}/accounts/{account_id}/ai/run"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _build_prompt(self, game_data: GameData) -> str:
        """Build prompt for fraud detection in poker"""
        players_text = ""
        for p in game_data.participants:
            players_text += f"- Player {p.player_id} (stack: {p.stack_at_hand_end})\n"

        cards_text = ", ".join(game_data.cards) if game_data.cards else "None"

        prompt = f"""You are a poker fraud detection expert. Analyze this poker hand for suspicious activity.

    GAME INFORMATION:
    - Game ID: {game_data.game_id}
    - Table ID: {game_data.table_id}
    - Type: {game_data.game_type}
    - Started: {game_data.date_start}
    - Ended: {game_data.date_stop}
    - Rake: {game_data.rake}
    - Community Cards: {cards_text}

    PARTICIPANTS:
    {players_text}

    RAW HAND HISTORY:
    {game_data.raw_hand_history[:3000]}

    TASK:
    Analyze this hand for potential fraud indicators:
    1. Unusual betting patterns
    2. Suspicious timing
    3. Potential collusion (soft play, chip dumping)
    4. Bot-like behavior (mechanical patterns, unnatural bet sizing)
    5. Card sharing (players knowing cards they shouldn't)

    RESPOND IN THIS EXACT JSON FORMAT:
    {{
        "fraud_probability": <number between 0 and 100>,
        "reasoning": "<detailed explanation with specific evidence>",
        "incident_types": ["<type1>", "<type2>", ...]
    }}
    """
        return prompt

    async def _send_request(self, prompt: str) -> str:
        """Send async request to Cloudflare Workers AI"""
        payload = {
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens
        }

        url = f"{self.base_url}/{self.model_id}"

        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Cloudflare API error {response.status}: {error_text}")

                data = await response.json()

                print("\n[DEBUG] Full API response:", json.dumps(data, indent=2, ensure_ascii=False))

                if not data.get("success", False):
                    errors = data.get("errors", [])
                    raise Exception(f"Cloudflare API returned errors: {errors}")

                result = data["result"]

                if "choices" in result and len(result["choices"]) > 0:
                    msg = result["choices"][0]["message"]
                    content = msg.get("content")
                    reasoning = msg.get("reasoning")

                    if content is not None and content.strip():
                        return content

                    # Content is empty:
                    if reasoning:
                        print("[WARNING] content is empty, but reasoning field is present. "
                              "Consider increasing max_tokens or disabling reasoning.")
                    raise Exception("Model returned empty content. Possibly output truncated due to low max_tokens. "
                                    "Reasoning length: " + str(len(reasoning or "")))

                if "response" in result:
                    resp = result["response"]
                    if resp is None:
                        raise Exception("Model returned null response.")
                    return resp

                # Nothing found
                raise Exception(f"Unexpected API response structure: {json.dumps(result, indent=2)}")

    def _parse_response(self, raw_response: str) -> FraudDetectionResponse:
        """Parse model response, stripping markdown fences if present."""
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
            cleaned = re.sub(r'\s*```$', '', cleaned)
            cleaned = cleaned.strip()
        try:
            data = json.loads(cleaned)
            return FraudDetectionResponse(
                fraud_probability=int(data["fraud_probability"]),
                reasoning=data.get("reasoning", ""),
                model_used=self.model_name,
                incident_types=data.get("incident_types", []),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Failed to parse model response: {e}\nRaw response: {raw_response[:500]}")