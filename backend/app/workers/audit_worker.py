"""Audit worker for logging entity changes."""
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.db.session import async_session_maker
from app.models.audit import AuditLog
from app.workers.base import BaseWorker

logger = logging.getLogger(__name__)


class AuditWorker(BaseWorker):
    """
    Worker for processing audit log jobs.

    Creates audit log entries for entity changes including:
    - Loan creation and updates
    - Status changes
    - Webhook events
    """

    def __init__(self, worker_id: Optional[str] = None):
        super().__init__(
            queue_name="audit",
            worker_id=worker_id or "audit-worker",
            poll_interval=0.5,  # Process audit logs quickly
        )

    async def process(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process an audit log job.

        Args:
            job_id: The job ID
            payload: Job payload containing:
                - entity_type: Type of entity (loan_application, user, etc.)
                - entity_id: UUID of the entity
                - action: Action performed (CREATE, UPDATE, DELETE, etc.)
                - actor_id: Optional user ID who performed the action
                - changes: Dictionary of changes made
                - ip_address: Optional IP address
                - user_agent: Optional user agent

        Returns:
            Result with created audit log ID
        """
        entity_type = payload.get("entity_type")
        entity_id_str = payload.get("entity_id")
        action = payload.get("action")
        actor_id_str = payload.get("actor_id")
        changes = payload.get("changes", {})
        ip_address = payload.get("ip_address")
        user_agent = payload.get("user_agent")

        if not entity_type or not entity_id_str or not action:
            raise ValueError("entity_type, entity_id, and action are required")

        entity_id = UUID(entity_id_str)
        actor_id = UUID(actor_id_str) if actor_id_str else None

        logger.debug(
            f"[AuditWorker] Creating audit log: {entity_type}/{entity_id} - {action}"
        )

        async with async_session_maker() as session:
            # Create audit log entry
            audit_log = AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor_id=actor_id,
                actor_type="USER" if actor_id else "SYSTEM",
                changes=changes,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            session.add(audit_log)
            await session.commit()
            await session.refresh(audit_log)

            logger.info(
                f"[AuditWorker] Audit log created: id={audit_log.id}, "
                f"entity={entity_type}/{entity_id}, action={action}"
            )

            return {
                "audit_log_id": audit_log.id,
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "action": action,
                "created_at": datetime.utcnow().isoformat(),
            }
