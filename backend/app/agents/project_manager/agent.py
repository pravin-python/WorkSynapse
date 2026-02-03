from app.agents.base import BaseAgent

class ProjectManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PM Bot", role="Project Manager")

    async def process_message(self, message: str) -> str:
        return f"PM Agent received: {message}"
