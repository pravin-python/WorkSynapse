import os
import sys
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.getcwd())

from app.models.llm.model import LLMKeyProvider, LLMKeyProviderType
from app.database.session import AsyncSessionLocal

async def seed_groq():
    async with AsyncSessionLocal() as db:
        print("Checking for Groq provider...")
        query = select(LLMKeyProvider).where(LLMKeyProvider.name == "groq")
        result = await db.execute(query)
        groq = result.scalar_one_or_none()
        
        if groq:
            print("Groq provider already exists.")
            return

        print("Creating Groq provider...")
        # Since available_models is stored as Text/JSON string in many implementations, 
        # or implies a list based on model definition. Checking model.py it is Text.
        import json
        models = ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma2-9b-it", "gemma-7b-it"]
        
        groq_provider = LLMKeyProvider(
            name="groq",
            type="groq", # Use string literal as enum might have issues if not reloaded perfectly
            display_name="Groq",
            description="Ultra-fast inference for open source models",
            base_url="https://api.groq.com/openai/v1",
            icon="groq",
            available_models=json.dumps(models),
            is_active=True,
            requires_api_key=True
        )
        db.add(groq_provider)
        await db.commit()
        print("Groq provider seeded successfully!")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_groq())
