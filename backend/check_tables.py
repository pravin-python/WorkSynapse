import asyncio, sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.infrastructure.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        # Check for orchestrator tables specifically
        r = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND "
            "(table_name LIKE '%orchestrator%' OR table_name = 'agent_executions') "
            "ORDER BY table_name"
        ))
        rows = r.fetchall()
        if rows:
            print("Found orchestrator tables:")
            for row in rows:
                print(f"  - {row[0]}")
        else:
            print("No orchestrator tables or agent_executions found.")
    await engine.dispose()

async def check_agent():
    async with engine.begin() as conn:
        r = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name LIKE '%agent%' "
            "ORDER BY table_name"
        ))
        for row in r:
            print(row[0])
    await engine.dispose()

asyncio.run(check())
