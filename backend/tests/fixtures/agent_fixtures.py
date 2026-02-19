import pytest
import pytest_asyncio
from app.models.agent_builder.model import CustomAgent, CustomAgentStatus
from faker import Faker

fake = Faker()

@pytest_asyncio.fixture
async def custom_agent_factory(db_session):
    async def create_agent(user, **kwargs):
        name = kwargs.pop("name", fake.name())
        slug = kwargs.pop("slug", fake.slug())

        agent = CustomAgent(
            name=name,
            slug=slug,
            system_prompt="You are a helpful assistant.",
            created_by_user_id=user.id,
            status=CustomAgentStatus.ACTIVE,
            is_public=False,
            **kwargs
        )
        db_session.add(agent)
        await db_session.commit()
        await db_session.refresh(agent)
        return agent
    return create_agent
