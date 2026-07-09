from abc import ABC, abstractmethod
from PokerLLMAntiFraud.src.core.fraud_detection_manager import FraudDetectionManager

class UI(ABC):
    def __init__(self, fraud_detection_manager: FraudDetectionManager):
        self.fraud_detection_manager = fraud_detection_manager
        self.is_running = False

    @abstractmethod
    async def run(self):
        self.is_running = True
        while(self.is_running):
            print('running')