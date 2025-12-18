"""Loans API Router."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.api.v1.loans.schemas import (
    LoanCreateRequest,
    LoanDetailResponse,
    LoanListResponse,
    LoanResponse,
    LoanStatisticsResponse,
    LoanStatusHistoryResponse,
    LoanStatusUpdateRequest,
)
from app.core.exceptions import (
    CountryNotSupportedError,
    LoanNotFoundError,
    ValidationError,
)
from app.models.loan import LoanStatus
from app.services.loan_service import LoanService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/loans", tags=["Loans"])


@router.post(
    "",
    response_model=LoanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create loan application",
    description="Create a new loan application. Validates document and applies country-specific business rules.",
)
async def create_loan(
    db: DbSession,
    current_user: CurrentUser,
    request: LoanCreateRequest,
) -> LoanResponse:
    """
    Create a new loan application.

    Process:
    1. Validates country is supported
    2. Validates document format
    3. Fetches banking information
    4. Applies business rules
    5. Creates the application
    6. Enqueues background jobs
    """
    service = LoanService(db)

    try:
        loan = await service.create_loan_application(
            country_code=request.country_code,
            document_type=request.document_type,
            document_number=request.document_number,
            full_name=request.full_name,
            amount_requested=request.amount_requested,
            monthly_income=request.monthly_income,
            user_id=current_user.id,
        )

        logger.info(f"Loan created: {loan.id} by user {current_user.id}")
        return LoanResponse.from_orm_with_decryption(loan)

    except CountryNotSupportedError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": e.message, "errors": e.errors},
        )


@router.get(
    "",
    response_model=LoanListResponse,
    summary="List loan applications",
    description="Get paginated list of loan applications with optional filters.",
)
async def list_loans(
    db: DbSession,
    current_user: CurrentUser,
    country_code: Optional[str] = Query(
        None,
        description="Filter by country code",
        examples=["ES"],
    ),
    status_filter: Optional[LoanStatus] = Query(
        None,
        alias="status",
        description="Filter by status",
    ),
    requires_review: Optional[bool] = Query(
        None,
        description="Filter by review requirement",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> LoanListResponse:
    """
    List loan applications with filters and pagination.
    """
    service = LoanService(db)

    skip = (page - 1) * page_size

    loans, total = await service.list_loans(
        country_code=country_code.upper() if country_code else None,
        status=status_filter,
        requires_review=requires_review,
        skip=skip,
        limit=page_size,
    )

    return LoanListResponse.from_results(
        items=list(loans),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/statistics",
    response_model=LoanStatisticsResponse,
    summary="Get loan statistics",
    description="Get statistics about loan applications.",
)
async def get_statistics(
    db: DbSession,
    current_user: CurrentUser,
    country_code: Optional[str] = Query(
        None,
        description="Filter by country code",
    ),
) -> LoanStatisticsResponse:
    """
    Get loan statistics.
    """
    service = LoanService(db)

    stats = await service.get_statistics(
        country_code=country_code.upper() if country_code else None,
    )

    return LoanStatisticsResponse(**stats)


@router.get(
    "/{loan_id}",
    response_model=LoanDetailResponse,
    summary="Get loan application",
    description="Get a specific loan application by ID.",
)
async def get_loan(
    db: DbSession,
    current_user: CurrentUser,
    loan_id: UUID,
) -> LoanDetailResponse:
    """
    Get a loan application by ID.
    """
    service = LoanService(db)

    try:
        loan = await service.get_loan_by_id(loan_id)
        # Create base response with decryption
        base_response = LoanResponse.from_orm_with_decryption(loan)
        return LoanDetailResponse(
            **base_response.model_dump(),
            banking_info=loan.banking_info,
            extra_data=loan.extra_data,
        )
    except LoanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application {loan_id} not found",
        )


@router.get(
    "/{loan_id}/history",
    response_model=list[LoanStatusHistoryResponse],
    summary="Get loan status history",
    description="Get the status change history for a loan application.",
)
async def get_loan_history(
    db: DbSession,
    current_user: CurrentUser,
    loan_id: UUID,
) -> list[LoanStatusHistoryResponse]:
    """
    Get status history for a loan.
    """
    service = LoanService(db)

    try:
        history = await service.get_status_history(loan_id)
        return [LoanStatusHistoryResponse.model_validate(h) for h in history]
    except LoanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application {loan_id} not found",
        )


@router.patch(
    "/{loan_id}/status",
    response_model=LoanResponse,
    summary="Update loan status",
    description="Update the status of a loan application. Only valid transitions are allowed.",
)
async def update_loan_status(
    db: DbSession,
    current_user: CurrentUser,
    loan_id: UUID,
    request: LoanStatusUpdateRequest,
) -> LoanResponse:
    """
    Update loan application status.

    Valid transitions:
    - PENDING -> VALIDATING, CANCELLED
    - VALIDATING -> IN_REVIEW, APPROVED, REJECTED
    - IN_REVIEW -> APPROVED, REJECTED
    - APPROVED -> DISBURSED, CANCELLED
    - DISBURSED -> COMPLETED
    """
    service = LoanService(db)

    try:
        # Check if user can approve (ANALYST or ADMIN)
        if request.status in (LoanStatus.APPROVED, LoanStatus.REJECTED):
            if not current_user.can_approve_loans:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only analysts can approve or reject loans",
                )

        loan = await service.update_status(
            loan_id=loan_id,
            new_status=request.status,
            changed_by=current_user.id,
            reason=request.reason,
        )

        logger.info(
            f"Loan {loan_id} status updated to {request.status.value} "
            f"by user {current_user.id}"
        )

        return LoanResponse.from_orm_with_decryption(loan)

    except LoanNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan application {loan_id} not found",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": e.message, "errors": e.errors},
        )
