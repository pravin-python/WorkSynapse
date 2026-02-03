from .base import BaseAgent

class ProjectManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PM Bot", role="Project Manager")

    async def process_message(self, message: str) -> str:
        # TODO: Implement LLM integration
        return f"As a Project Manager, I received your request: {message}. I will update the roadmap accordingly."
    
    async def create_roadmap(self, project_details: str):
        # Logic to parse text and generate Project/Task objects
        pass
