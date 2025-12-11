"""Base repository with common CRUD operations."""
from typing import Any, Generic, Optional, Sequence, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

# Type variable for the model class
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing common CRUD operations.

    All repositories should inherit from this class and specify
    the model type they work with.
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        """
        Initialize the repository.

        Args:
            model: The SQLAlchemy model class
            session: The async database session
        """
        self.model = model
        self.session = session

    async def create(self, obj_in: dict[str, Any]) -> ModelType:
        """
        Create a new record.

        Args:
            obj_in: Dictionary with the model attributes

        Returns:
            The created model instance
        """
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get a record by its ID.

        Args:
            id: The UUID of the record

        Returns:
            The model instance or None if not found
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[Any] = None,
    ) -> Sequence[ModelType]:
        """
        Get multiple records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Column to order by

        Returns:
            List of model instances
        """
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(order_by)
        else:
            # Default to ordering by created_at if it exists
            if hasattr(self.model, "created_at"):
                query = query.order_by(self.model.created_at.desc())

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(
        self,
        db_obj: ModelType,
        obj_in: dict[str, Any],
    ) -> ModelType:
        """
        Update a record.

        Args:
            db_obj: The existing model instance
            obj_in: Dictionary with the attributes to update

        Returns:
            The updated model instance
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.session.add(db_obj)
        await self.session.flush()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, id: UUID) -> bool:
        """
        Delete a record by its ID.

        Args:
            id: The UUID of the record

        Returns:
            True if deleted, False if not found
        """
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.flush()
            return True
        return False

    async def count(self) -> int:
        """
        Count all records.

        Returns:
            Total number of records
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists.

        Args:
            id: The UUID of the record

        Returns:
            True if exists, False otherwise
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return result.scalar_one() > 0
