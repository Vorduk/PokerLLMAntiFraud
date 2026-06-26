import asyncio
from core import FraudDetectionManager, GameFetcher, AIAnalyzer
from config import ConfigLoader
from models import ModelFactory

async def main():
    print("=" * 60)
    print("Poker fraud detection system")
    print("=" * 60)

    # Initialize components
    config = ConfigLoader()
    factory = ModelFactory(config)

    game_fetcher = GameFetcher()
    ai_analyzer = AIAnalyzer(factory)

    # Create orchestrator
    orchestrator = FraudDetectionManager(
        game_fetcher=game_fetcher,
        ai_analyzer=ai_analyzer
    )

    # Run detection
    results = await orchestrator.detect_fraud_single_game("test_game", "@cf/google/gemma-4-26b-a4b-it")

    print(f"\nFraud Probability: {results.fraud_probability:.2%}")
    print(f"Reasoning: {results.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
