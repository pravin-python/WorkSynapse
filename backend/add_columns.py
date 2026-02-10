
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os

# Database URL (assuming default dev environment if not set)
# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/worksynapse")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://root:Admin%40123@10.0.101.117:5432/worksynapse")

async def add_columns():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.connect() as conn:
        print("Adding columns to llm_key_providers...")
        
        # Add is_system column
        try:
            await conn.execute(text("ALTER TABLE llm_key_providers ADD COLUMN IF NOT EXISTS is_system BOOLEAN DEFAULT FALSE"))
            print("Added is_system column.")
        except Exception as e:
            print(f"Error adding is_system: {e}")
            
        # Add purchase_url column
        try:
            await conn.execute(text("ALTER TABLE llm_key_providers ADD COLUMN IF NOT EXISTS purchase_url VARCHAR(500)"))
            print("Added purchase_url column.")
        except Exception as e:
            print(f"Error adding purchase_url: {e}")
            
        # Add documentation_url column
        try:
            await conn.execute(text("ALTER TABLE llm_key_providers ADD COLUMN IF NOT EXISTS documentation_url VARCHAR(500)"))
            print("Added documentation_url column.")
        except Exception as e:
            print(f"Error adding documentation_url: {e}")
            
        await conn.commit()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_columns())
