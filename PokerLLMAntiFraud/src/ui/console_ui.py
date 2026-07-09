import asyncio
import sys
from .ui import UI
from PokerLLMAntiFraud.src.core.fraud_detection_manager import FraudDetectionManager

class ConsoleUI(UI):
    def __init__(self, fraud_detection_manager: FraudDetectionManager):
        super().__init__(fraud_detection_manager)
        self.analyzing_task: asyncio.Task | None = None
        self.reading_task: asyncio.Task | None = None
        self.interval = 30.0

    async def run(self):
        self._print_header()
        self.is_running = True
        self.reading_task = asyncio.create_task(self._read_commands())
        try:
            await self.reading_task
        except asyncio.CancelledError:
            pass
        finally:
            if self.analyzing_task and not self.analyzing_task.done():
                self.analyzing_task.cancel()
                try:
                    await self.analyzing_task
                except asyncio.CancelledError:
                    pass
            print("Console stopped.")

    def _print_header(self):
        print("\nFraud Detection Console")
        print("\nCommands:")
        print("start <model id>         - Start games analyzing")
        print("stop                     - Stop games analyzing")
        print("change_model <model id>  - Change ai model by id")
        print("set_interval <interval>  - Update interval in seconds")
        print("exit                     - Completely stop program")

    async def _read_commands(self):
        loop = asyncio.get_event_loop()
        while self.is_running:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                continue
            cmd = line.strip().lower()
            if cmd.startswith('start '):
                model_id = cmd.split(' ', 1)[1]
                await self._cmd_start(model_id)
            elif cmd == 'stop':
                await self._cmd_stop()
            elif cmd.startswith('change_model '):
                model_id = cmd.split(' ', 1)[1]
                await self._cmd_change_model(model_id)
            elif cmd.startswith('set_interval '):
                interval_str = cmd.split(' ', 1)[1]
                await self._cmd_set_interval(interval_str)
            elif cmd == 'exit':
                self.is_running = False
            else:
                print(f"Unknown command: {cmd}")

    async def _cmd_start(self, model_id: str):
        await self._cmd_stop()
        await self._cmd_change_model(model_id)
        self.analyzing_task = asyncio.create_task(self._analyzing_loop())

    async def _cmd_stop(self):
        if self.analyzing_task and not self.analyzing_task.done():
            self.analyzing_task.cancel()
            try:
                await self.analyzing_task
            except asyncio.CancelledError:
                pass
            print("Analyzing stopped")
        self.analyzing_task = None

    async def _cmd_change_model(self, model_id: str):
        print(model_id) #временная затычка
        # что-то типа self.fraud_detection_manager.set_model(model_id)

    async def _cmd_set_interval(self, interval_str: str):
        try:
            new_interval = float(interval_str)
            if new_interval <= 0:
                print("Interval must be a positive number.")
                return
            self.interval = new_interval
            print(f"Interval set to {self.interval} seconds.")
        except ValueError:
            print("Invalid interval. Please enter a number")

    async def _analyzing_loop(self):
        print("Analysis loop started.")
        try:
            while self.is_running:
                try:
                    await self.fraud_detection_manager.step()
                except Exception as e:
                    print(f"Error during analysis step: {e}")
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            print("Analyzing interrupted")
            raise