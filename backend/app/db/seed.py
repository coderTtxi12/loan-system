"""Database seed script for initial data."""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import async_session_maker
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Demo users to seed
DEMO_USERS = [
    {
        "email": "admin@loan.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
    },
    {
        "email": "analyst@loan.com",
        "password": "analyst123",
        "full_name": "Analyst User",
        "role": UserRole.ANALYST,
    },
    {
        "email": "viewer@loan.com",
        "password": "viewer123",
        "full_name": "Viewer User",
        "role": UserRole.VIEWER,
    },
]


async def seed_users() -> None:
    """Seed demo users into the database."""
    logger.info("Starting user seed...")
    
    async with async_session_maker() as session:
        for user_data in DEMO_USERS:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.email == user_data["email"])
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                logger.info(f"User already exists: {user_data['email']}")
                continue
            
            # Create new user
            user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            logger.info(f"Created user: {user_data['email']} ({user_data['role'].value})")
        
        await session.commit()
    
    logger.info("User seed completed!")


async def main() -> None:
    """Run all seed functions."""
    logger.info("=" * 50)
    logger.info("Running database seeds...")
    logger.info("=" * 50)
    
    await seed_users()
    
    logger.info("=" * 50)
    logger.info("All seeds completed successfully!")
    logger.info("=" * 50)
    logger.info("")
    logger.info("Demo Credentials:")
    logger.info("-" * 30)
    for user in DEMO_USERS:
        logger.info(f"  {user['role'].value}: {user['email']} / {user['password']}")
    logger.info("")


if __name__ == "__main__":
    asyncio.run(main())
