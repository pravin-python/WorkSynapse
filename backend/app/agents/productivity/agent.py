from app.agents.base import BaseAgent

class ProductivityAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ProdBot", role="Productivity Analyst")

    async def process_message(self, message: str) -> str:
        return f"Analyzing productivity: {message}"
