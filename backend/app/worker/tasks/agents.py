"""
Agent Background Tasks
"""
from celery import shared_task
from app.core.logging import logger

@shared_task(bind=True, max_retries=3)
def run_project_manager_agent(self, project_id: int, prompt: str):
    """Run PM Agent asynchronously."""
    try:
        logger.info(f"Running PM Agent for project {project_id}")
        # TODO: Load agent, run with prompt, save results
        from app.agents.project_manager.agent import ProjectManagerAgent
        agent = ProjectManagerAgent()
        # Sync wrapper for async method
        import asyncio
        result = asyncio.run(agent.process_message(prompt))
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"PM Agent error: {e}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3)
def run_task_generator_agent(self, feature_description: str, project_id: int):
    """Generate tasks from feature description."""
    try:
        logger.info(f"Running TaskGen Agent for project {project_id}")
        from app.agents.task_generator.agent import TaskGeneratorAgent
        agent = TaskGeneratorAgent()
        import asyncio
        result = asyncio.run(agent.process_message(feature_description))
        return {"status": "success", "tasks": result}
    except Exception as e:
        logger.error(f"TaskGen Agent error: {e}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3)
def run_dev_assistant_agent(self, user_id: int, query: str, context: dict = None):
    """Answer developer questions."""
    try:
        logger.info(f"Running DevAssistant for user {user_id}")
        from app.agents.dev_assistant.agent import DevAssistantAgent
        agent = DevAssistantAgent()
        import asyncio
        result = asyncio.run(agent.process_message(query))
        return {"status": "success", "answer": result}
    except Exception as e:
        logger.error(f"DevAssistant error: {e}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3)
def run_productivity_agent(self, user_id: int, period: str = "daily"):
    """Analyze user productivity."""
    try:
        logger.info(f"Running Productivity Agent for user {user_id}")
        from app.agents.productivity.agent import ProductivityAgent
        agent = ProductivityAgent()
        import asyncio
        result = asyncio.run(agent.process_message(f"Analyze {period} productivity for user {user_id}"))
        return {"status": "success", "analysis": result}
    except Exception as e:
        logger.error(f"Productivity Agent error: {e}")
        raise self.retry(exc=e)
