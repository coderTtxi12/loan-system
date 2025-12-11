"""PostgreSQL LISTEN/NOTIFY listener for real-time events."""
import asyncio
import json
import logging
from typing import Any, Callable, Optional

import asyncpg

from app.core.config import settings
from app.sockets.handlers import emit_loan_updated, emit_status_changed

logger = logging.getLogger(__name__)


class PostgresListener:
    """
    Listens to PostgreSQL NOTIFY events and broadcasts to Socket.IO.

    Channels:
    - loan_changes: Triggered by loan INSERT/UPDATE
    """

    def __init__(self):
        self.connection: Optional[asyncpg.Connection] = None
        self.running = False
        self._callbacks: dict[str, list[Callable]] = {}

    def _get_connection_params(self) -> dict[str, Any]:
        """Parse DATABASE_URL to connection parameters."""
        # DATABASE_URL format: postgresql+asyncpg://user:pass@host:port/dbname
        url = settings.DATABASE_URL
        # Remove the driver prefix
        url = url.replace("postgresql+asyncpg://", "postgresql://")

        return {"dsn": url}

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        try:
            params = self._get_connection_params()
            self.connection = await asyncpg.connect(params["dsn"])
            logger.info("PostgreSQL listener connected")
        except Exception as e:
            logger.error(f"Failed to connect PostgreSQL listener: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        self.running = False
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info("PostgreSQL listener disconnected")

    def add_callback(self, channel: str, callback: Callable) -> None:
        """
        Add a callback for a channel.

        Args:
            channel: Channel name
            callback: Async callback function
        """
        if channel not in self._callbacks:
            self._callbacks[channel] = []
        self._callbacks[channel].append(callback)

    async def _handle_notification(
        self,
        connection: asyncpg.Connection,
        pid: int,
        channel: str,
        payload: str,
    ) -> None:
        """
        Handle incoming notification.

        Args:
            connection: Database connection
            pid: Process ID
            channel: Channel name
            payload: JSON payload
        """
        try:
            data = json.loads(payload)
            logger.debug(f"Received notification on {channel}: {data}")

            # Call registered callbacks
            if channel in self._callbacks:
                for callback in self._callbacks[channel]:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"Callback error for {channel}: {e}")

            # Handle loan_changes channel
            if channel == "loan_changes":
                await self._handle_loan_change(data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in notification: {e}")
        except Exception as e:
            logger.error(f"Error handling notification: {e}")

    async def _handle_loan_change(self, data: dict) -> None:
        """
        Handle loan change notification.

        Args:
            data: Notification payload
        """
        operation = data.get("operation")
        loan_id = data.get("loan_id")
        country_code = data.get("country_code")
        old_status = data.get("old_status")
        new_status = data.get("new_status")

        if not loan_id:
            return

        if old_status != new_status and old_status is not None:
            # Status changed
            await emit_status_changed(
                loan_id=str(loan_id),
                country_code=country_code or "",
                old_status=old_status,
                new_status=new_status,
            )
        elif operation in ("INSERT", "UPDATE"):
            # General update
            await emit_loan_updated(
                loan_id=str(loan_id),
                country_code=country_code or "",
                changes={"status": new_status} if new_status else {},
            )

    async def listen(self, channels: list[str]) -> None:
        """
        Start listening to channels.

        Args:
            channels: List of channel names to listen to
        """
        if not self.connection:
            await self.connect()

        self.running = True

        # Add notification handler
        await self.connection.add_listener(
            "loan_changes",
            self._handle_notification,
        )

        logger.info(f"Listening to PostgreSQL channels: {channels}")

        # Keep the connection alive
        while self.running:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    async def start(self) -> None:
        """Start the listener in the background."""
        await self.connect()
        asyncio.create_task(self.listen(["loan_changes"]))


# Global listener instance
pg_listener = PostgresListener()


async def start_pg_listener() -> None:
    """Start the PostgreSQL listener."""
    try:
        await pg_listener.start()
    except Exception as e:
        logger.warning(f"Could not start PostgreSQL listener: {e}")
        # Don't fail the application if listener fails


async def stop_pg_listener() -> None:
    """Stop the PostgreSQL listener."""
    await pg_listener.disconnect()
