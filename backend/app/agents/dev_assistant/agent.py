from app.agents.base import BaseAgent

class DevAssistantAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DevBuddy", role="Developer Assistant")

    async def process_message(self, message: str) -> str:
        return f"Dev Assistant here: {message}"
