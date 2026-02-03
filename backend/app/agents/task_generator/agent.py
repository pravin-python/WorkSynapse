from app.agents.base import BaseAgent

class TaskGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TaskGen Bot", role="Task Generator")

    async def process_message(self, message: str) -> str:
        return f"TaskGen received: {message}"
