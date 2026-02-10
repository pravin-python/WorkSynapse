import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import get_db, engine
from app.services.agent_builder_service import AgentBuilderService
from app.schemas.agent_builder import CustomAgentCreate, AgentToolConfigCreate, AgentAutonomyLevel
from app.agents.orchestrator.core import get_orchestrator

async def main():
    import traceback
    try:
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as db:
            # ... (rest of the logic)
            # 0. Create a fresh test model to avoid existing data issues
            from app.models.agent_builder.model import AgentModel
            from app.models.llm.model import LLMKeyProvider
            from app.schemas.agent_builder import AgentModelCreate
            
            print("Ensuring test provider exists...")
            # Check for provider first
            stmt = select(LLMKeyProvider).where(LLMKeyProvider.name == "test-provider")
            provider = await db.scalar(stmt)
            if not provider:
                 provider = LLMKeyProvider(name="test-provider", display_name="Test Provider", type="custom")
                 db.add(provider)
                 await db.commit()
                 await db.refresh(provider)
            print(f"Using provider: {provider.id}")

            print("Creating/Fetching test model...")
            stmt = select(AgentModel).where(AgentModel.name == "test-gpt-4o")
            existing_model = await db.scalar(stmt)
            if existing_model:
                model_id = existing_model.id
                print(f"Using existing test model: {model_id}")
                # Update to not require key if needed
                if existing_model.requires_api_key:
                    existing_model.requires_api_key = False
                    await db.commit()
            else:
                new_model = AgentModel(
                    name="test-gpt-4o", 
                    display_name="Test GPT-4o", 
                    provider_id=provider.id,
                    context_window=128000, 
                    max_output_tokens=4096,
                    input_price_per_million=5.0, 
                    output_price_per_million=15.0,
                    requires_api_key=False, # IMPORTANT: No key required for test
                    is_active=True
                )
                db.add(new_model)
                await db.commit()
                await db.refresh(new_model)
                model_id = new_model.id
                print(f"Created test model_id: {model_id}")

            # 0.5 Ensure a valid user exists
            from app.models.user.model import User
            print("Fetching/Creating test user...")
            stmt = select(User).limit(1)
            user = await db.scalar(stmt)
            if not user:
                user = User(
                    email="testadmin@worksynapse.com",
                    username="testadmin",
                    full_name="Test Admin",
                    hashed_password="hashed_secret",
                    is_active=True,
                    is_superuser=True
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            user_id = user.id
            print(f"Using user_id: {user_id}")

            # 1. Create Agent
            import uuid
            unique_name = f"Test Action Agent {uuid.uuid4().hex[:8]}"
            print(f"Creating Agent: {unique_name}...")
            agent_data = CustomAgentCreate(
                name=unique_name,
                system_prompt="You are a helpful assistant.",
                model_id=model_id,
                action_mode_enabled=True,
                autonomy_level=AgentAutonomyLevel.MEDIUM,
                max_steps=5,
                mcp_enabled=False
            )
            
            # Pass user_id
            # AgentBuilderService methods are static and take db as first arg, user_id second, data third
            agent = await AgentBuilderService.create_agent(db, user_id=user_id, data=agent_data)
            print(f"Agent Created: ID={agent.id}, Action Mode={agent.action_mode_enabled}, Max Steps={agent.max_steps}")
            
            # 2. Prepare Config (mimic endpoint logic)
            agent_config = {
                "id": agent.id,
                "name": agent.name,
                "system_prompt": agent.system_prompt,
                "goal": agent.goal_prompt,
                "llm_provider": "openai", # Fallback
                "model_name": "gpt-4o",
                "temperature": agent.temperature,
                "max_tokens": agent.max_tokens,
                "tools": [], # No tools for now
                "mcp_enabled": agent.mcp_enabled,
                "mcp_servers": [],
                "action_mode_enabled": agent.action_mode_enabled,
                "max_steps": agent.max_steps,
                "permissions": {},
            }
            
            # 3. Run Orchestrator
            print("Running Orchestrator...")
            orchestrator = get_orchestrator()
            result = await orchestrator.run(
                agent_config=agent_config,
                message="Hello, are you in action mode?"
            )
            
            print(f"Response: {result.response}")
            
            # Clean up
            await AgentBuilderService.delete_agent(db, agent.id, user_id=user_id)
            print("Agent Deleted.")
            
            with open("verify_result.txt", "w", encoding="utf-8") as f:
                f.write("SUCCESS\n")
                f.write(f"Agent ID: {agent.id}\n")
                f.write(f"Response: {result.response}\n")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        with open("verify_result.txt", "w", encoding="utf-8") as f:
            f.write(f"ERROR: {e}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
