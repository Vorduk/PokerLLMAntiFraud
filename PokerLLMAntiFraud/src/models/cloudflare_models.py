import json
import aiohttp
from .base_model import BaseModel
from .schemas import GameData, FraudDetectionResponse


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
        game = game_data.game_data
        players = game.get('players', [])
        actions = game.get('actions', [])
        community_cards = game.get('community_cards', [])
        dealt_cards = game.get('dealt_cards', {})
        result = game.get('result', {})
        blinds = game.get('blinds', {})

        players_text = ""
        for p in players:
            cards = dealt_cards.get(p['name'], ['unknown'])
            players_text += f"- {p['name']}: {', '.join(cards)}\n"

        recent_actions = actions[-10:] if len(actions) > 10 else actions
        actions_text = "\n".join(f"  {a}" for a in recent_actions)

        prompt = f"""You are a poker fraud detection expert. Analyze this Texas Hold'em hand for suspicious activity.

GAME INFORMATION:
- Type: {game.get('game_type', 'Heads-up NL Hold\'em')}
- Blinds: {blinds.get('small', '?')}/{blinds.get('big', '?')}
- Community Cards: {', '.join(community_cards)}

PLAYERS AND THEIR CARDS:
{players_text}

RESULT:
- Winner: {result.get('winner', 'Unknown')}
- Pot: {result.get('pot', 'Unknown')}
- Rake: {result.get('rake', 'Unknown')}

RECENT ACTIONS:
{actions_text}

TASK:
Analyze this hand for potential fraud indicators:
1. Unusual betting patterns (extremely large raises, min-raises, etc.)
2. Suspicious timing (consistent delays or instant actions)
3. Potential collusion (soft play, chip dumping)
4. Bot-like behavior (mechanical patterns, unnatural bet sizing)
5. Card sharing (players knowing cards they shouldn't)

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "fraud_probability": <number between 0.0 and 1.0>,
    "reasoning": "<detailed explanation with specific evidence>"
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

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Cloudflare API error {response.status}: {error_text}")

                data = await response.json()

                # Временный вывод полного ответа для диагностики
                print("\n[DEBUG] Full API response:", json.dumps(data, indent=2, ensure_ascii=False))

                if not data.get("success", False):
                    errors = data.get("errors", [])
                    raise Exception(f"Cloudflare API returned errors: {errors}")

                result = data["result"]

                # Для чат‑моделей ответ всегда лежит в choices
                if "choices" in result and len(result["choices"]) > 0:
                    msg = result["choices"][0]["message"]
                    content = msg.get("content")
                    reasoning = msg.get("reasoning")

                    if content is not None and content.strip():
                        return content

                    # Контент пуст – возможно, модель потратила все токены на reasoning
                    if reasoning:
                        print("[WARNING] content is empty, but reasoning field is present. "
                              "Consider increasing max_tokens or disabling reasoning.")
                        # Можно попытаться найти JSON в reasoning (ненадёжно)
                        # Для надёжности всё же выбрасываем исключение, чтобы разработчик увидел проблему
                    raise Exception("Model returned empty content. Possibly output truncated due to low max_tokens. "
                                    "Reasoning length: " + str(len(reasoning or "")))

                # На случай, если структура другая (не чат‑модель) — но для gemma это не нужно
                if "response" in result:
                    resp = result["response"]
                    if resp is None:
                        raise Exception("Model returned null response.")
                    return resp

                # Если ничего не нашли
                raise Exception(f"Unexpected API response structure: {json.dumps(result, indent=2)}")


    def _parse_response(self, raw_response: str) -> FraudDetectionResponse:
        """Parse model response to structured format"""
        try:
            data = json.loads(raw_response)
            return FraudDetectionResponse(
                fraud_probability=float(data["fraud_probability"]),
                reasoning=data.get("reasoning", ""),
                model_used=self.model_name
            )
        except (json.JSONDecodeError, KeyError, ValueError):
            return FraudDetectionResponse(
                fraud_probability=0.0,
                reasoning=raw_response,
                model_used=self.model_name
            )