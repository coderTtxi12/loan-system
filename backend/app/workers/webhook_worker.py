"""Webhook worker for sending outgoing notifications."""
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.workers.base import BaseWorker

logger = logging.getLogger(__name__)

# Webhook endpoint templates by country
WEBHOOK_ENDPOINTS = {
    "ES": "{base_url}/webhooks/loan-update",
    "MX": "{base_url}/webhooks/loan-update",
    "CO": "{base_url}/webhooks/loan-update",
    "BR": "{base_url}/webhooks/loan-update",
}

# Simulated webhook endpoints for MVP
SIMULATED_ENDPOINTS = {
    "ES": "https://httpbin.org/post",  # Echo service for testing
    "MX": "https://httpbin.org/post",
    "CO": "https://httpbin.org/post",
    "BR": "https://httpbin.org/post",
}


class WebhookWorker(BaseWorker):
    """
    Worker for processing outgoing webhook notifications.

    Sends notifications to external systems when loan status changes.
    Implements retry with exponential backoff.
    """

    def __init__(self, worker_id: Optional[str] = None):
        super().__init__(
            queue_name="notifications",
            worker_id=worker_id or "webhook-worker",
            poll_interval=1.0,
        )
        self.http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        return self.http_client

    def _sign_payload(self, payload: str) -> str:
        """
        Create HMAC signature for webhook payload.

        Args:
            payload: JSON payload string

        Returns:
            HMAC-SHA256 signature
        """
        return hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _get_endpoint(self, country_code: str) -> str:
        """
        Get webhook endpoint for a country.

        Args:
            country_code: ISO 2-letter country code

        Returns:
            Webhook URL
        """
        # In production, use real endpoints
        # For MVP, use simulated endpoints
        if settings.DEBUG:
            return SIMULATED_ENDPOINTS.get(country_code, SIMULATED_ENDPOINTS["ES"])

        base_url = getattr(
            settings,
            f"BANKING_PROVIDER_{country_code}_URL",
            settings.BANKING_PROVIDER_ES_URL,
        )
        template = WEBHOOK_ENDPOINTS.get(country_code, WEBHOOK_ENDPOINTS["ES"])
        return template.format(base_url=base_url)

    async def process(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Process an outgoing webhook job.

        Args:
            job_id: The job ID
            payload: Job payload containing:
                - loan_id: UUID of the loan
                - notification_type: Type of notification
                - country_code: Country code
                - Additional data specific to notification type

        Returns:
            Result with webhook response
        """
        loan_id = payload.get("loan_id")
        notification_type = payload.get("notification_type")
        country_code = payload.get("country_code", "ES")

        if not loan_id or not notification_type:
            raise ValueError("loan_id and notification_type are required")

        logger.info(
            f"[WebhookWorker] Sending {notification_type} notification "
            f"for loan {loan_id} to {country_code}"
        )

        # Build webhook payload
        webhook_payload = {
            "event_type": notification_type,
            "loan_reference": loan_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                k: v
                for k, v in payload.items()
                if k not in ("loan_id", "notification_type", "country_code")
            },
        }

        import json
        payload_str = json.dumps(webhook_payload, sort_keys=True)
        signature = self._sign_payload(payload_str)

        # Get endpoint
        endpoint = self._get_endpoint(country_code)

        # Send webhook
        client = await self._get_client()

        try:
            response = await client.post(
                endpoint,
                json=webhook_payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Source": "loan-system",
                },
            )

            success = 200 <= response.status_code < 300

            logger.info(
                f"[WebhookWorker] Webhook sent to {endpoint}: "
                f"status={response.status_code}, success={success}"
            )

            return {
                "loan_id": loan_id,
                "notification_type": notification_type,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": success,
                "sent_at": datetime.utcnow().isoformat(),
            }

        except httpx.RequestError as e:
            logger.error(f"[WebhookWorker] Request failed: {e}")
            raise  # Will trigger retry

        except Exception as e:
            logger.error(f"[WebhookWorker] Unexpected error: {e}")
            raise

    async def stop(self) -> None:
        """Stop the worker and cleanup."""
        if self.http_client:
            await self.http_client.aclose()
            self.http_client = None
        await super().stop()
