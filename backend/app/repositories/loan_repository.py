"""Repository for loan application operations."""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan import LoanApplication, LoanStatus
from app.models.loan_status_history import LoanStatusHistory
from app.repositories.base import BaseRepository


class LoanRepository(BaseRepository[LoanApplication]):
    """Repository for LoanApplication CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LoanApplication, session)

    async def create(
        self,
        *,
        country_code: str,
        document_type: str,
        document_number: str,
        document_hash: str,
        full_name: str,
        amount_requested: Decimal,
        monthly_income: Decimal,
        currency: str = "EUR",
        status: LoanStatus = LoanStatus.PENDING,
        risk_score: Optional[int] = None,
        requires_review: bool = False,
        banking_info: Optional[dict] = None,
        extra_data: Optional[dict] = None,
    ) -> LoanApplication:
        """
        Create a new loan application.

        Args:
            country_code: ISO 2-letter country code
            document_type: Type of document (DNI, CURP, etc.)
            document_number: The document number (encrypted)
            document_hash: SHA256 hash for lookup
            full_name: Applicant's name (encrypted)
            amount_requested: Loan amount
            monthly_income: Monthly income
            currency: Currency code
            status: Initial status
            risk_score: Calculated risk score
            requires_review: Whether manual review is needed
            banking_info: Banking provider response
            extra_data: Additional metadata

        Returns:
            Created LoanApplication instance
        """
        loan = LoanApplication(
            country_code=country_code,
            document_type=document_type,
            document_number=document_number,
            document_hash=document_hash,
            full_name=full_name,
            amount_requested=amount_requested,
            monthly_income=monthly_income,
            currency=currency,
            status=status,
            risk_score=risk_score,
            requires_review=requires_review,
            banking_info=banking_info,
            extra_data=extra_data or {},
        )
        self.session.add(loan)
        await self.session.flush()
        await self.session.refresh(loan)

        # Create initial status history
        history = LoanStatusHistory(
            loan_id=loan.id,
            previous_status=None,
            new_status=status.value,
            reason="Application created",
        )
        self.session.add(history)
        await self.session.flush()

        return loan

    async def get_by_document_hash(
        self,
        document_hash: str,
        country_code: Optional[str] = None,
    ) -> Optional[LoanApplication]:
        """
        Find a loan by document hash.

        Args:
            document_hash: SHA256 hash of the document
            country_code: Optional country filter

        Returns:
            LoanApplication or None (first match if multiple exist)
        """
        query = select(LoanApplication).where(
            LoanApplication.document_hash == document_hash
        )
        if country_code:
            query = query.where(LoanApplication.country_code == country_code)
        
        # Order by created_at desc to get the most recent one if multiple exist
        query = query.order_by(LoanApplication.created_at.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        country_code: Optional[str] = None,
        status: Optional[LoanStatus] = None,
        statuses: Optional[list[LoanStatus]] = None,
        requires_review: Optional[bool] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Sequence[LoanApplication]:
        """
        List loan applications with filters and pagination.

        Args:
            country_code: Filter by country
            status: Filter by single status
            statuses: Filter by multiple statuses
            requires_review: Filter by review requirement
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter
            date_from: Filter by creation date (from)
            date_to: Filter by creation date (to)
            search: Search in document_hash
            skip: Pagination offset
            limit: Maximum results
            order_by: Field to order by
            order_desc: Order descending

        Returns:
            List of matching LoanApplications
        """
        query = select(LoanApplication)
        conditions = []

        if country_code:
            conditions.append(LoanApplication.country_code == country_code)

        if status:
            conditions.append(LoanApplication.status == status)
        elif statuses:
            conditions.append(LoanApplication.status.in_(statuses))

        if requires_review is not None:
            conditions.append(LoanApplication.requires_review == requires_review)

        if min_amount is not None:
            conditions.append(LoanApplication.amount_requested >= min_amount)

        if max_amount is not None:
            conditions.append(LoanApplication.amount_requested <= max_amount)

        if date_from:
            conditions.append(LoanApplication.created_at >= date_from)

        if date_to:
            conditions.append(LoanApplication.created_at <= date_to)

        if search:
            conditions.append(LoanApplication.document_hash.ilike(f"%{search}%"))

        if conditions:
            query = query.where(and_(*conditions))

        # Ordering
        order_column = getattr(LoanApplication, order_by, LoanApplication.created_at)
        if order_desc:
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_count(
        self,
        *,
        country_code: Optional[str] = None,
        status: Optional[LoanStatus] = None,
        statuses: Optional[list[LoanStatus]] = None,
        requires_review: Optional[bool] = None,
    ) -> int:
        """
        Count loan applications with optional filters.

        Args:
            country_code: Filter by country
            status: Filter by single status
            statuses: Filter by multiple statuses
            requires_review: Filter by review requirement

        Returns:
            Count of matching records
        """
        query = select(func.count()).select_from(LoanApplication)
        conditions = []

        if country_code:
            conditions.append(LoanApplication.country_code == country_code)

        if status:
            conditions.append(LoanApplication.status == status)
        elif statuses:
            conditions.append(LoanApplication.status.in_(statuses))

        if requires_review is not None:
            conditions.append(LoanApplication.requires_review == requires_review)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update_status(
        self,
        loan_id: UUID,
        new_status: LoanStatus,
        changed_by: Optional[UUID] = None,
        reason: Optional[str] = None,
        extra_data: Optional[dict] = None,
    ) -> Optional[LoanApplication]:
        """
        Update the status of a loan application.

        Args:
            loan_id: The loan ID
            new_status: The new status
            changed_by: User ID who made the change
            reason: Reason for the status change
            extra_data: Additional context data

        Returns:
            Updated LoanApplication or None if not found
        """
        loan = await self.get_by_id(loan_id)
        if not loan:
            return None

        old_status = loan.status

        # Update status
        loan.status = new_status
        if new_status in (LoanStatus.APPROVED, LoanStatus.REJECTED, LoanStatus.DISBURSED):
            loan.processed_at = datetime.utcnow()

        self.session.add(loan)

        # Create status history record
        history = LoanStatusHistory(
            loan_id=loan_id,
            previous_status=old_status.value,
            new_status=new_status.value,
            changed_by=changed_by,
            reason=reason,
            extra_data=extra_data,
        )
        self.session.add(history)

        await self.session.flush()
        await self.session.refresh(loan)

        return loan

    async def get_status_history(
        self,
        loan_id: UUID,
    ) -> Sequence[LoanStatusHistory]:
        """
        Get the status history for a loan.

        Args:
            loan_id: The loan ID

        Returns:
            List of status history records
        """
        query = (
            select(LoanStatusHistory)
            .where(LoanStatusHistory.loan_id == loan_id)
            .order_by(LoanStatusHistory.created_at.asc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_pending_review(
        self,
        country_code: Optional[str] = None,
        limit: int = 50,
    ) -> Sequence[LoanApplication]:
        """
        Get loans pending review.

        Args:
            country_code: Optional country filter
            limit: Maximum results

        Returns:
            List of loans requiring review
        """
        return await self.list_with_filters(
            country_code=country_code,
            statuses=[LoanStatus.PENDING, LoanStatus.IN_REVIEW],
            requires_review=True,
            limit=limit,
        )

    async def get_statistics(
        self,
        country_code: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get loan statistics.

        Args:
            country_code: Optional country filter

        Returns:
            Dictionary with statistics
        """
        # Count by status
        status_counts = {}
        for status in LoanStatus:
            count = await self.get_count(country_code=country_code, status=status)
            status_counts[status.value] = count

        # Total amount requested
        total_query = select(func.sum(LoanApplication.amount_requested))
        if country_code:
            total_query = total_query.where(LoanApplication.country_code == country_code)
        total_result = await self.session.execute(total_query)
        total_amount = total_result.scalar_one() or Decimal("0")

        # Average amount
        avg_query = select(func.avg(LoanApplication.amount_requested))
        if country_code:
            avg_query = avg_query.where(LoanApplication.country_code == country_code)
        avg_result = await self.session.execute(avg_query)
        avg_amount = avg_result.scalar_one() or Decimal("0")

        # Count by country
        by_country: dict[str, int] = {}
        country_query = select(
            LoanApplication.country_code,
            func.count().label("count"),
        )
        if country_code:
            country_query = country_query.where(
                LoanApplication.country_code == country_code
            )
        country_query = country_query.group_by(LoanApplication.country_code)
        country_result = await self.session.execute(country_query)
        for code, count in country_result.all():
            # Ensure string keys for JSON serialization
            by_country[str(code)] = int(count)

        # Average risk score (ignoring NULLs)
        avg_risk_query = select(func.avg(LoanApplication.risk_score))
        if country_code:
            avg_risk_query = avg_risk_query.where(
                LoanApplication.country_code == country_code
            )
        avg_risk_result = await self.session.execute(avg_risk_query)
        avg_risk = avg_risk_result.scalar_one()

        total_loans = sum(status_counts.values())

        return {
            # Kept for backwards compatibility
            "total_count": total_loans,
            # New explicit field used by frontend
            "total_loans": total_loans,
            "by_status": status_counts,
            "by_country": by_country,
            "total_amount_requested": float(total_amount),
            "average_amount": float(avg_amount),
            "average_risk_score": float(avg_risk) if avg_risk is not None else None,
            "pending_review_count": await self.get_count(
                country_code=country_code,
                requires_review=True,
                statuses=[LoanStatus.PENDING, LoanStatus.IN_REVIEW],
            ),
        }
