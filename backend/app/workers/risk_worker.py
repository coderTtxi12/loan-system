"""Risk evaluation worker for processing loan risk assessments."""
import logging
from typing import Any, Optional
from uuid import UUID

from app.db.session import async_session_maker
from app.models.loan import LoanStatus
from app.repositories.job_repository import JobRepository
from app.repositories.loan_repository import LoanRepository
from app.sockets.handlers import emit_status_changed
from app.workers.base import BaseWorker

logger = logging.getLogger(__name__)


# Risk score thresholds for automatic decisions
RISK_THRESHOLD_APPROVE = 300  # Score <= 300: Auto-approve
RISK_THRESHOLD_REJECT = 700  # Score >= 700: Auto-reject
# Scores between 300-700: Require manual review


class RiskEvaluationWorker(BaseWorker):
    """
    Worker for processing risk evaluation jobs.

    Analyzes loan applications and updates their status based on risk score:
    - risk_score <= 300: Auto-approve (low risk)
    - risk_score >= 700: Auto-reject (high risk)
    - 300 < risk_score < 700: Send to manual review
    """

    def __init__(self, worker_id: Optional[str] = None):
        super().__init__(
            queue_name="risk_evaluation",
            worker_id=worker_id or "risk-worker",
            poll_interval=1.0,
        )

    async def process(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process a risk evaluation job.

        Args:
            job_id: The job ID
            payload: Job payload containing:
                - loan_id: UUID of the loan
                - country_code: Country code
                - amount_requested: Loan amount
                - risk_score: Calculated risk score

        Returns:
            Result data with decision made
        """
        loan_id_str = payload.get("loan_id")
        risk_score = payload.get("risk_score", 500)
        country_code = payload.get("country_code", "")

        if not loan_id_str:
            raise ValueError("loan_id is required in payload")

        loan_id = UUID(loan_id_str)

        logger.info(
            f"[RiskWorker] Evaluating loan {loan_id} with risk_score={risk_score}"
        )

        async with async_session_maker() as session:
            loan_repo = LoanRepository(session)

            # Get current loan
            loan = await loan_repo.get_by_id(loan_id)
            if not loan:
                raise ValueError(f"Loan {loan_id} not found")

            # Only process loans in PENDING status
            if loan.status != LoanStatus.PENDING:
                logger.warning(
                    f"[RiskWorker] Loan {loan_id} is not PENDING "
                    f"(status={loan.status.value}), skipping"
                )
                return {
                    "skipped": True,
                    "reason": f"Loan status is {loan.status.value}",
                }

            # Determine new status based on risk score
            old_status = loan.status
            new_status: LoanStatus
            decision_reason: str

            if risk_score <= RISK_THRESHOLD_APPROVE:
                new_status = LoanStatus.APPROVED
                decision_reason = f"Auto-approved: risk_score {risk_score} <= {RISK_THRESHOLD_APPROVE}"
            elif risk_score >= RISK_THRESHOLD_REJECT:
                new_status = LoanStatus.REJECTED
                decision_reason = f"Auto-rejected: risk_score {risk_score} >= {RISK_THRESHOLD_REJECT}"
            else:
                new_status = LoanStatus.IN_REVIEW
                decision_reason = f"Manual review required: risk_score {risk_score} between thresholds"

            # First transition to VALIDATING, then to final status
            await loan_repo.update_status(
                loan_id=loan_id,
                new_status=LoanStatus.VALIDATING,
                reason="Risk evaluation started",
            )

            # Then update to final status
            await loan_repo.update_status(
                loan_id=loan_id,
                new_status=new_status,
                reason=decision_reason,
            )

            await session.commit()

            logger.info(
                f"[RiskWorker] Loan {loan_id}: {old_status.value} -> {new_status.value} "
                f"({decision_reason})"
            )

            # Emit Socket.IO event
            try:
                await emit_status_changed(
                    loan_id=str(loan_id),
                    country_code=country_code,
                    old_status=old_status.value,
                    new_status=new_status.value,
                )
            except Exception as e:
                logger.warning(f"[RiskWorker] Failed to emit status change: {e}")

            # Enqueue notification job if approved/rejected
            if new_status in (LoanStatus.APPROVED, LoanStatus.REJECTED):
                job_repo = JobRepository(session)
                await job_repo.enqueue(
                    queue_name="notifications",
                    payload={
                        "loan_id": str(loan_id),
                        "notification_type": f"loan_{new_status.value.lower()}",
                        "country_code": country_code,
                        "risk_score": risk_score,
                    },
                    priority=2,
                )
                await session.commit()

            return {
                "loan_id": str(loan_id),
                "old_status": old_status.value,
                "new_status": new_status.value,
                "risk_score": risk_score,
                "decision_reason": decision_reason,
            }
