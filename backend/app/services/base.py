"""
WorkSynapse CRUD Base Service
=============================
Enhanced base CRUD operations with security, audit logging, and validation.

Security Features:
- SQL injection protection (via SQLAlchemy ORM)
- Audit logging for all write operations
- Soft delete support
- Transaction management
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Callable
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models.base import Base
import datetime
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDException(Exception):
    """Base exception for CRUD operations."""
    pass


class NotFoundError(CRUDException):
    """Resource not found."""
    pass


class DuplicateError(CRUDException):
    """Duplicate resource error."""
    pass


class ValidationError(CRUDException):
    """Validation error."""
    pass


class PermissionError(CRUDException):
    """Permission denied error."""
    pass


class SecureCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Enhanced CRUD base class with security features.
    
    Features:
    - Parameterized queries (SQL injection protection)
    - Soft delete support
    - Audit logging
    - Transaction management
    - Pagination
    - Filtering
    """
    
    def __init__(
        self,
        model: Type[ModelType],
        *,
        enable_soft_delete: bool = True,
        enable_audit_log: bool = True,
    ):
        self.model = model
        self.enable_soft_delete = enable_soft_delete
        self.enable_audit_log = enable_audit_log

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================
    
    async def get(
        self,
        db: AsyncSession,
        id: Any,
        *,
        include_deleted: bool = False,
    ) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: Record ID
            include_deleted: Include soft-deleted records
        
        Returns:
            Model instance or None
        """
        query = select(self.model).filter(self.model.id == id)
        
        if self.enable_soft_delete and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        result = await db.execute(query)
        return result.scalars().first()

    async def get_or_404(
        self,
        db: AsyncSession,
        id: Any,
        *,
        include_deleted: bool = False,
    ) -> ModelType:
        """
        Get a single record by ID or raise NotFoundError.
        """
        obj = await self.get(db, id, include_deleted=include_deleted)
        if obj is None:
            raise NotFoundError(f"{self.model.__name__} with id {id} not found")
        return obj

    async def get_by_field(
        self,
        db: AsyncSession,
        field_name: str,
        field_value: Any,
        *,
        include_deleted: bool = False,
    ) -> Optional[ModelType]:
        """
        Get a single record by a specific field.
        """
        field = getattr(self.model, field_name, None)
        if field is None:
            raise ValueError(f"Field {field_name} does not exist on {self.model.__name__}")
        
        query = select(self.model).filter(field == field_value)
        
        if self.enable_soft_delete and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return (max 1000)
            include_deleted: Include soft-deleted records
            order_by: Field name to order by
            order_desc: Order descending if True
            filters: Dictionary of field_name -> value filters
        
        Returns:
            List of model instances
        """
        # Enforce maximum limit for security
        limit = min(limit, 1000)
        
        query = select(self.model)
        
        # Apply soft delete filter
        if self.enable_soft_delete and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        # Apply custom filters
        if filters:
            for field_name, field_value in filters.items():
                field = getattr(self.model, field_name, None)
                if field is not None:
                    query = query.filter(field == field_value)
        
        # Apply ordering
        if order_by:
            order_field = getattr(self.model, order_by, None)
            if order_field is not None:
                query = query.order_by(order_field.desc() if order_desc else order_field)
        else:
            # Default ordering by created_at desc
            if hasattr(self.model, 'created_at'):
                query = query.order_by(self.model.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        db: AsyncSession,
        *,
        include_deleted: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count records with optional filtering.
        """
        query = select(func.count(self.model.id))
        
        if self.enable_soft_delete and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        if filters:
            for field_name, field_value in filters.items():
                field = getattr(self.model, field_name, None)
                if field is not None:
                    query = query.filter(field == field_value)
        
        result = await db.execute(query)
        return result.scalar_one()

    async def exists(
        self,
        db: AsyncSession,
        id: Any,
        *,
        include_deleted: bool = False,
    ) -> bool:
        """
        Check if a record exists.
        """
        obj = await self.get(db, id, include_deleted=include_deleted)
        return obj is not None

    # =========================================================================
    # CREATE OPERATIONS
    # =========================================================================

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType,
        created_by_user_id: Optional[int] = None,
        commit: bool = True,
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Pydantic schema with creation data
            created_by_user_id: ID of user creating the record
            commit: Whether to commit the transaction
        
        Returns:
            Created model instance
        """
        obj_in_data = obj_in.model_dump()
        
        # Add audit fields if model supports them
        if hasattr(self.model, 'created_by_user_id') and created_by_user_id:
            obj_in_data['created_by_user_id'] = created_by_user_id
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        
        try:
            if commit:
                await db.commit()
                await db.refresh(db_obj)
        except IntegrityError as e:
            await db.rollback()
            raise DuplicateError(f"Duplicate entry: {str(e)}")
        except SQLAlchemyError as e:
            await db.rollback()
            raise CRUDException(f"Database error: {str(e)}")
        
        if self.enable_audit_log:
            logger.info(
                f"Created {self.model.__name__} with id {db_obj.id}",
                extra={"user_id": created_by_user_id, "record_id": db_obj.id}
            )
        
        return db_obj

    async def create_multi(
        self,
        db: AsyncSession,
        *,
        objs_in: List[CreateSchemaType],
        created_by_user_id: Optional[int] = None,
    ) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        """
        db_objs = []
        
        for obj_in in objs_in:
            obj_in_data = obj_in.model_dump()
            
            if hasattr(self.model, 'created_by_user_id') and created_by_user_id:
                obj_in_data['created_by_user_id'] = created_by_user_id
            
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db_objs.append(db_obj)
        
        try:
            await db.commit()
            for db_obj in db_objs:
                await db.refresh(db_obj)
        except IntegrityError as e:
            await db.rollback()
            raise DuplicateError(f"Duplicate entry: {str(e)}")
        except SQLAlchemyError as e:
            await db.rollback()
            raise CRUDException(f"Database error: {str(e)}")
        
        return db_objs

    # =========================================================================
    # UPDATE OPERATIONS
    # =========================================================================

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        updated_by_user_id: Optional[int] = None,
        commit: bool = True,
    ) -> ModelType:
        """
        Update an existing record.
        
        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Pydantic schema or dict with update data
            updated_by_user_id: ID of user updating the record
            commit: Whether to commit the transaction
        
        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        # Add audit fields if model supports them
        if hasattr(self.model, 'updated_by_user_id') and updated_by_user_id:
            update_data['updated_by_user_id'] = updated_by_user_id
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        
        try:
            if commit:
                await db.commit()
                await db.refresh(db_obj)
        except IntegrityError as e:
            await db.rollback()
            raise DuplicateError(f"Duplicate entry: {str(e)}")
        except SQLAlchemyError as e:
            await db.rollback()
            raise CRUDException(f"Database error: {str(e)}")
        
        if self.enable_audit_log:
            logger.info(
                f"Updated {self.model.__name__} with id {db_obj.id}",
                extra={"user_id": updated_by_user_id, "record_id": db_obj.id}
            )
        
        return db_obj

    async def update_by_id(
        self,
        db: AsyncSession,
        *,
        id: Any,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        updated_by_user_id: Optional[int] = None,
    ) -> ModelType:
        """
        Update a record by ID.
        """
        db_obj = await self.get_or_404(db, id)
        return await self.update(
            db,
            db_obj=db_obj,
            obj_in=obj_in,
            updated_by_user_id=updated_by_user_id
        )

    # =========================================================================
    # DELETE OPERATIONS
    # =========================================================================

    async def remove(
        self,
        db: AsyncSession,
        *,
        id: int,
        deleted_by_user_id: Optional[int] = None,
        hard_delete: bool = False,
    ) -> Optional[ModelType]:
        """
        Delete a record (soft delete by default).
        
        Args:
            db: Database session
            id: Record ID
            deleted_by_user_id: ID of user deleting the record
            hard_delete: If True, permanently delete the record
        
        Returns:
            Deleted model instance
        """
        db_obj = await self.get(db, id, include_deleted=True)
        if db_obj is None:
            return None
        
        if hard_delete or not self.enable_soft_delete:
            await db.delete(db_obj)
        else:
            db_obj.soft_delete()
            if hasattr(db_obj, 'updated_by_user_id') and deleted_by_user_id:
                db_obj.updated_by_user_id = deleted_by_user_id
            db.add(db_obj)
        
        try:
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise CRUDException(f"Database error: {str(e)}")
        
        if self.enable_audit_log:
            action = "Hard deleted" if hard_delete else "Soft deleted"
            logger.info(
                f"{action} {self.model.__name__} with id {id}",
                extra={"user_id": deleted_by_user_id, "record_id": id}
            )
        
        return db_obj

    async def restore(
        self,
        db: AsyncSession,
        *,
        id: int,
        restored_by_user_id: Optional[int] = None,
    ) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.
        """
        db_obj = await self.get(db, id, include_deleted=True)
        if db_obj is None:
            return None
        
        if not self.enable_soft_delete:
            raise CRUDException("Soft delete is not enabled for this model")
        
        db_obj.restore()
        if hasattr(db_obj, 'updated_by_user_id') and restored_by_user_id:
            db_obj.updated_by_user_id = restored_by_user_id
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        if self.enable_audit_log:
            logger.info(
                f"Restored {self.model.__name__} with id {id}",
                extra={"user_id": restored_by_user_id, "record_id": id}
            )
        
        return db_obj

    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================

    async def search(
        self,
        db: AsyncSession,
        *,
        search_fields: List[str],
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[ModelType]:
        """
        Search records by multiple fields.
        
        Uses ILIKE for case-insensitive partial matching.
        """
        limit = min(limit, 1000)
        
        query = select(self.model)
        
        if self.enable_soft_delete and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        # Build OR conditions for search
        search_conditions = []
        for field_name in search_fields:
            field = getattr(self.model, field_name, None)
            if field is not None:
                search_conditions.append(field.ilike(f"%{search_term}%"))
        
        if search_conditions:
            query = query.filter(or_(*search_conditions))
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
