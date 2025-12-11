"""Webhooks API Router."""
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.api.v1.webhooks.schemas import (
    BankingWebhookPayload,
    WebhookEventResponse,
    WebhookResponse,
)
from app.core.config import settings
from app.models.loan import LoanApplication, LoanStatus
from app.models.webhook_event import WebhookEvent
from app.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """
    Verify HMAC-SHA256 signature of webhook payload.

    Args:
        payload: Raw request body
        signature: Signature from header
        secret: Webhook secret key

    Returns:
        True if signature is valid
    """
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected, signature)


@router.post(
    "/banking/{country_code}",
    response_model=WebhookResponse,
    summary="Receive banking webhook",
    description="Endpoint for receiving webhooks from banking providers. Requires valid HMAC signature.",
)
async def receive_banking_webhook(
    db: DbSession,
    request: Request,
    country_code: str,
    payload: BankingWebhookPayload,
    x_webhook_signature: Optional[str] = Header(
        None,
        description="HMAC-SHA256 signature of the payload",
    ),
) -> WebhookResponse:
    """
    Receive and process webhooks from banking providers.

    Process:
    1. Verify HMAC signature
    2. Store webhook event
    3. Find related loan
    4. Process event (update loan, enqueue jobs)
    """
    country_code = country_code.upper()

    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    if not x_webhook_signature:
        logger.warning(f"Webhook received without signature from {country_code}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature",
        )

    if not verify_webhook_signature(body, x_webhook_signature, settings.WEBHOOK_SECRET):
        logger.warning(f"Invalid webhook signature from {country_code}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # Create webhook event record
    webhook_event = WebhookEvent(
        source=f"banking_provider_{country_code}",
        event_type=payload.event_type,
        payload=payload.model_dump(mode="json"),
        signature=x_webhook_signature,
        processed=False,
    )
    db.add(webhook_event)

    # Try to find related loan
    loan: Optional[LoanApplication] = None
    try:
        # Try to parse as UUID first
        loan_id = UUID(payload.loan_reference)
        result = await db.execute(
            select(LoanApplication).where(LoanApplication.id == loan_id)
        )
        loan = result.scalar_one_or_none()
    except ValueError:
        # Not a UUID, try document_hash
        result = await db.execute(
            select(LoanApplication).where(
                LoanApplication.document_hash == payload.loan_reference
            )
        )
        loan = result.scalar_one_or_none()

    if loan:
        webhook_event.loan_id = loan.id

    # Process the webhook
    processed = False
    message = "Webhook received and queued for processing"

    try:
        if loan and payload.event_type == "status_update" and payload.status:
            # Map external status to our status
            status_mapping = {
                "approved": LoanStatus.APPROVED,
                "rejected": LoanStatus.REJECTED,
                "verified": LoanStatus.VALIDATING,
                "disbursed": LoanStatus.DISBURSED,
            }

            new_status = status_mapping.get(payload.status.lower())
            if new_status and loan.status != new_status:
                # Update loan status
                loan.status = new_status
                if new_status in (LoanStatus.APPROVED, LoanStatus.REJECTED, LoanStatus.DISBURSED):
                    loan.processed_at = datetime.utcnow()

                db.add(loan)
                processed = True
                message = f"Loan {loan.id} status updated to {new_status.value}"

                logger.info(f"Webhook updated loan {loan.id} to {new_status.value}")

        elif loan and payload.event_type == "risk_assessment" and payload.risk_score is not None:
            # Update risk score
            loan.risk_score = payload.risk_score
            db.add(loan)
            processed = True
            message = f"Loan {loan.id} risk score updated to {payload.risk_score}"

            logger.info(f"Webhook updated loan {loan.id} risk score to {payload.risk_score}")

        # Mark webhook as processed
        webhook_event.processed = processed
        webhook_event.processed_at = datetime.utcnow() if processed else None

        # Enqueue audit job
        job_repo = JobRepository(db)
        await job_repo.enqueue(
            queue_name="audit",
            payload={
                "entity_type": "webhook_event",
                "entity_id": str(webhook_event.id),
                "action": "WEBHOOK_RECEIVED",
                "changes": {
                    "source": webhook_event.source,
                    "event_type": payload.event_type,
                    "loan_id": str(loan.id) if loan else None,
                    "processed": processed,
                },
            },
        )

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        webhook_event.processing_error = str(e)
        message = f"Webhook received but processing failed: {str(e)}"

    await db.flush()

    logger.info(
        f"Webhook received: source={webhook_event.source}, "
        f"type={payload.event_type}, processed={processed}"
    )

    return WebhookResponse(
        event_id=webhook_event.id,
        processed=processed,
        message=message,
    )


@router.get(
    "/events",
    response_model=list[WebhookEventResponse],
    summary="List webhook events",
    description="List recent webhook events (requires authentication).",
)
async def list_webhook_events(
    db: DbSession,
    source: Optional[str] = None,
    processed: Optional[bool] = None,
    limit: int = 50,
) -> list[WebhookEventResponse]:
    """
    List webhook events with optional filters.

    Note: This endpoint doesn't require auth for simplicity,
    but in production should be protected.
    """
    query = select(WebhookEvent).order_by(WebhookEvent.created_at.desc()).limit(limit)

    if source:
        query = query.where(WebhookEvent.source == source)

    if processed is not None:
        query = query.where(WebhookEvent.processed == processed)

    result = await db.execute(query)
    events = result.scalars().all()

    return [WebhookEventResponse.model_validate(e) for e in events]
