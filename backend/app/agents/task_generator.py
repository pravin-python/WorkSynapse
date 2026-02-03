from .base import BaseAgent

class TaskGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TaskGen Bot", role="Task Generator")

    async def process_message(self, message: str) -> str:
        return f"I will breakdown '{message}' into actionable tasks."
    
    async def generate_tasks_from_feature(self, feature_description: str) -> list:
        # Logic to return list of tasks
        return [{"title": "Implement X", "status": "TODO"}]
