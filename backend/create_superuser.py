import asyncio
import logging
import sys
from getpass import getpass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.database.session import engine
from app.services.user import user_service
from app.models.user.model import User, UserRole, UserStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_superuser():
    """Create a superuser via command line."""
    print("\n--- Create Superuser ---\n")
    
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    full_name = input("Full Name: ").strip()
    password = getpass("Password: ")
    confirm_password = getpass("Confirm Password: ")
    
    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        return

    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as db:
        try:
            # Check if user exists
            existing_user = await user_service.get_by_email(db, email=email)
            if existing_user:
                print(f"Error: User with email {email} already exists.")
                # We could offer to promote existing user, but let's keep it simple for now
                return
            
            existing_username = await user_service.get_by_username(db, username=username)
            if existing_username:
                print(f"Error: Username {username} is already taken.")
                return

            print("Creating superuser...")
            
            # Create user object
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=user_service.hash_password(password),
                is_superuser=True,
                is_active=True,
                status=UserStatus.ACTIVE,
                email_verified=True,
                role=UserRole.SUPER_ADMIN
            )
            
            db.add(user)
            await db.commit()
            
            print(f"\n✅ Superuser '{username}' created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating superuser: {e}")
            await db.rollback()

def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(create_superuser())
    except KeyboardInterrupt:
        print("\nCancelled.")

if __name__ == "__main__":
    main()
