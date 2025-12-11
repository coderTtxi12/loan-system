"""Loan application service with business logic."""
import hashlib
import logging
from decimal import Decimal
from typing import Any, Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheKeys, get_cache
from app.core.exceptions import (
    CountryNotSupportedError,
    LoanNotFoundError,
    ValidationError,
)
from app.models.loan import LoanApplication, LoanStatus
from app.repositories.job_repository import JobRepository
from app.repositories.loan_repository import LoanRepository
from app.strategies import BankingInfo, StrategyRegistry, ValidationResult

logger = logging.getLogger(__name__)

# Cache TTL constants (in seconds)
CACHE_TTL_LOAN = 300  # 5 minutes for individual loans
CACHE_TTL_LIST = 60  # 1 minute for list queries
CACHE_TTL_STATS = 120  # 2 minutes for statistics


# Valid status transitions
VALID_TRANSITIONS: dict[LoanStatus, list[LoanStatus]] = {
    LoanStatus.PENDING: [LoanStatus.VALIDATING, LoanStatus.CANCELLED],
    LoanStatus.VALIDATING: [LoanStatus.IN_REVIEW, LoanStatus.APPROVED, LoanStatus.REJECTED],
    LoanStatus.IN_REVIEW: [LoanStatus.APPROVED, LoanStatus.REJECTED],
    LoanStatus.APPROVED: [LoanStatus.DISBURSED, LoanStatus.CANCELLED],
    LoanStatus.REJECTED: [],  # Terminal state
    LoanStatus.CANCELLED: [],  # Terminal state
    LoanStatus.DISBURSED: [LoanStatus.COMPLETED],
    LoanStatus.COMPLETED: [],  # Terminal state
}


class LoanService:
    """
    Service for loan application business logic.

    Handles:
    - Creating loan applications with validation
    - Fetching banking information
    - Applying country-specific rules
    - Managing status transitions
    - Enqueueing background jobs
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.loan_repo = LoanRepository(session)
        self.job_repo = JobRepository(session)

    @staticmethod
    def hash_document(document_number: str, country_code: str) -> str:
        """
        Create a hash of the document for lookup.

        Args:
            document_number: The document number
            country_code: The country code

        Returns:
            SHA256 hash string
        """
        combined = f"{country_code}:{document_number}".upper()
        return hashlib.sha256(combined.encode()).hexdigest()

    async def create_loan_application(
        self,
        *,
        country_code: str,
        document_type: str,
        document_number: str,
        full_name: str,
        amount_requested: Decimal,
        monthly_income: Decimal,
        user_id: Optional[UUID] = None,
    ) -> LoanApplication:
        """
        Create a new loan application.

        Process:
        1. Get country strategy
        2. Validate document format
        3. Fetch banking information
        4. Apply business rules
        5. Calculate risk score
        6. Create in database
        7. Enqueue risk evaluation job

        Args:
            country_code: ISO 2-letter country code
            document_type: Document type (DNI, CURP, etc.)
            document_number: The document number
            full_name: Applicant's full name
            amount_requested: Loan amount
            monthly_income: Monthly income
            user_id: Optional user ID creating the application

        Returns:
            Created LoanApplication

        Raises:
            CountryNotSupportedError: If country is not supported
            ValidationError: If validation fails
        """
        logger.info(
            f"Creating loan application for country={country_code}, "
            f"amount={amount_requested}, document_type={document_type}"
        )

        # 1. Get country strategy
        if not StrategyRegistry.is_supported(country_code):
            raise CountryNotSupportedError(country_code)

        strategy = StrategyRegistry.get_or_raise(country_code)

        # 2. Validate document
        doc_result = strategy.validate_document(document_type, document_number)
        if not doc_result.is_valid:
            logger.warning(f"Document validation failed: {doc_result.errors}")
            raise ValidationError(
                message="Document validation failed",
                errors=doc_result.errors,
            )

        # 3. Fetch banking information
        try:
            banking_info = await strategy.fetch_banking_info(
                document_type=document_type,
                document_number=document_number,
                full_name=full_name,
            )
            logger.debug(f"Banking info fetched: provider={banking_info.provider_name}")
        except Exception as e:
            logger.error(f"Failed to fetch banking info: {e}")
            # Continue without banking info - will require manual review
            banking_info = BankingInfo(
                provider_name=f"{country_code}_UNAVAILABLE",
                raw_data={"error": str(e)},
            )

        # 4. Apply business rules
        rules_result = strategy.validate_business_rules(
            amount_requested=amount_requested,
            monthly_income=monthly_income,
            banking_info=banking_info,
        )

        # Combine validation results
        combined_result = doc_result.merge(rules_result)

        if not combined_result.is_valid:
            logger.warning(f"Business rules validation failed: {combined_result.errors}")
            raise ValidationError(
                message="Business rules validation failed",
                errors=combined_result.errors,
            )

        # 5. Calculate risk score
        risk_score = strategy.calculate_risk_score(
            amount_requested=amount_requested,
            monthly_income=monthly_income,
            banking_info=banking_info,
        )

        # 6. Create loan application
        document_hash = self.hash_document(document_number, country_code)

        # Check for existing application with same document
        existing = await self.loan_repo.get_by_document_hash(
            document_hash=document_hash,
            country_code=country_code,
        )
        if existing and existing.status in (
            LoanStatus.PENDING,
            LoanStatus.VALIDATING,
            LoanStatus.IN_REVIEW,
        ):
            raise ValidationError(
                message="An active application already exists for this document",
                errors=["duplicate_application"],
            )

        loan = await self.loan_repo.create(
            country_code=country_code,
            document_type=document_type,
            document_number=document_number,  # TODO: Encrypt PII
            document_hash=document_hash,
            full_name=full_name,  # TODO: Encrypt PII
            amount_requested=amount_requested,
            monthly_income=monthly_income,
            currency=strategy.currency,
            status=LoanStatus.PENDING,
            risk_score=risk_score,
            requires_review=combined_result.requires_review,
            banking_info=banking_info.to_dict(),
            extra_data={
                "validation_warnings": combined_result.warnings,
                "risk_factors": combined_result.risk_factors,
            },
        )

        logger.info(
            f"Loan application created: id={loan.id}, "
            f"risk_score={risk_score}, requires_review={combined_result.requires_review}"
        )

        # 7. Enqueue risk evaluation job
        await self.job_repo.enqueue(
            queue_name="risk_evaluation",
            payload={
                "loan_id": str(loan.id),
                "country_code": country_code,
                "amount_requested": str(amount_requested),
                "risk_score": risk_score,
            },
            priority=1 if combined_result.requires_review else 0,
        )

        # Enqueue audit job
        await self.job_repo.enqueue(
            queue_name="audit",
            payload={
                "entity_type": "loan_application",
                "entity_id": str(loan.id),
                "action": "CREATE",
                "actor_id": str(user_id) if user_id else None,
                "changes": {
                    "status": {"old": None, "new": LoanStatus.PENDING.value},
                },
            },
        )

        return loan

    async def get_loan_by_id(
        self,
        loan_id: UUID,
        include_history: bool = False,
        use_cache: bool = True,
    ) -> LoanApplication:
        """
        Get a loan application by ID.

        Args:
            loan_id: The loan UUID
            include_history: Whether to load status history
            use_cache: Whether to use cache

        Returns:
            LoanApplication

        Raises:
            LoanNotFoundError: If loan not found
        """
        cache_key = CacheKeys.loan(str(loan_id))

        # Try cache first
        if use_cache:
            try:
                cache = await get_cache()
                cached = await cache.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for loan {loan_id}")
                    # We still need to fetch from DB for the ORM object
                    # but we could skip if we stored full object
            except Exception as e:
                logger.warning(f"Cache error: {e}")

        # Fetch from database
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise LoanNotFoundError(str(loan_id))

        # Cache the loan data
        if use_cache:
            try:
                cache = await get_cache()
                await cache.set(
                    cache_key,
                    {
                        "id": str(loan.id),
                        "country_code": loan.country_code,
                        "status": loan.status.value,
                        "amount_requested": str(loan.amount_requested),
                        "risk_score": loan.risk_score,
                    },
                    ttl_seconds=CACHE_TTL_LOAN,
                )
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

        return loan

    async def list_loans(
        self,
        *,
        country_code: Optional[str] = None,
        status: Optional[LoanStatus] = None,
        requires_review: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[LoanApplication], int]:
        """
        List loan applications with filters.

        Args:
            country_code: Filter by country
            status: Filter by status
            requires_review: Filter by review requirement
            skip: Pagination offset
            limit: Maximum results

        Returns:
            Tuple of (loans, total_count)
        """
        loans = await self.loan_repo.list_with_filters(
            country_code=country_code,
            status=status,
            requires_review=requires_review,
            skip=skip,
            limit=limit,
        )

        total = await self.loan_repo.get_count(
            country_code=country_code,
            status=status,
            requires_review=requires_review,
        )

        return loans, total

    async def update_status(
        self,
        loan_id: UUID,
        new_status: LoanStatus,
        changed_by: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> LoanApplication:
        """
        Update the status of a loan application.

        Validates that the transition is allowed.

        Args:
            loan_id: The loan UUID
            new_status: The new status
            changed_by: User ID making the change
            reason: Reason for the change

        Returns:
            Updated LoanApplication

        Raises:
            LoanNotFoundError: If loan not found
            ValidationError: If transition is not allowed
        """
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise LoanNotFoundError(str(loan_id))

        current_status = loan.status

        # Validate transition
        allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
        if new_status not in allowed_transitions:
            raise ValidationError(
                message=f"Cannot transition from {current_status.value} to {new_status.value}",
                errors=[
                    f"Invalid status transition. "
                    f"Allowed: {[s.value for s in allowed_transitions]}"
                ],
            )

        # Update status
        updated = await self.loan_repo.update_status(
            loan_id=loan_id,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
        )

        logger.info(
            f"Loan status updated: id={loan_id}, "
            f"{current_status.value} -> {new_status.value}"
        )

        # Enqueue audit job
        await self.job_repo.enqueue(
            queue_name="audit",
            payload={
                "entity_type": "loan_application",
                "entity_id": str(loan_id),
                "action": "STATUS_CHANGE",
                "actor_id": str(changed_by) if changed_by else None,
                "changes": {
                    "status": {
                        "old": current_status.value,
                        "new": new_status.value,
                    },
                },
            },
        )

        # Enqueue notification if approved/rejected
        if new_status in (LoanStatus.APPROVED, LoanStatus.REJECTED):
            await self.job_repo.enqueue(
                queue_name="notifications",
                payload={
                    "loan_id": str(loan_id),
                    "notification_type": f"loan_{new_status.value.lower()}",
                    "country_code": loan.country_code,
                },
                priority=2,  # High priority for user notifications
            )

        # Invalidate cache
        try:
            cache = await get_cache()
            # Delete loan cache
            await cache.delete(CacheKeys.loan(str(loan_id)))
            # Delete stats cache
            await cache.delete(CacheKeys.loan_stats(loan.country_code))
            await cache.delete(CacheKeys.loan_stats(None))
            # Delete list caches (pattern-based)
            await cache.delete_pattern("loans:*")
            logger.debug(f"Cache invalidated for loan {loan_id}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")

        return updated

    async def get_status_history(
        self,
        loan_id: UUID,
    ) -> Sequence[Any]:
        """
        Get the status history for a loan.

        Args:
            loan_id: The loan UUID

        Returns:
            List of status history records
        """
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise LoanNotFoundError(str(loan_id))

        return await self.loan_repo.get_status_history(loan_id)

    async def get_statistics(
        self,
        country_code: Optional[str] = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Get loan statistics.

        Args:
            country_code: Optional country filter
            use_cache: Whether to use cache

        Returns:
            Dictionary with statistics
        """
        cache_key = CacheKeys.loan_stats(country_code)

        # Try cache first
        if use_cache:
            try:
                cache = await get_cache()
                cached = await cache.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for stats {country_code or 'all'}")
                    return cached
            except Exception as e:
                logger.warning(f"Cache error: {e}")

        # Fetch from database
        stats = await self.loan_repo.get_statistics(country_code)

        # Cache the results
        if use_cache:
            try:
                cache = await get_cache()
                await cache.set(cache_key, stats, ttl_seconds=CACHE_TTL_STATS)
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

        return stats
