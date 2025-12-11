"""Socket.IO event handlers for real-time updates."""
import logging
from typing import Any, Optional

import socketio

logger = logging.getLogger(__name__)

# Create Socket.IO server with async mode
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],  # Will be configured from settings
    logger=False,
    engineio_logger=False,
)


class LoanNamespace(socketio.AsyncNamespace):
    """
    Socket.IO namespace for loan-related events.

    Rooms:
    - country:{code} - All loans for a specific country
    - loan:{id} - Single loan updates
    - all - All loan updates
    """

    def __init__(self, namespace: str = "/loans"):
        super().__init__(namespace)
        self.connected_clients: dict[str, dict[str, Any]] = {}

    async def on_connect(self, sid: str, environ: dict) -> bool:
        """
        Handle client connection.

        Args:
            sid: Session ID
            environ: WSGI environment

        Returns:
            True to accept connection
        """
        logger.info(f"Client connected: {sid}")
        self.connected_clients[sid] = {
            "rooms": set(),
            "connected_at": environ.get("REQUEST_METHOD"),
        }
        # Join the 'all' room by default
        await self.enter_room(sid, "all")
        return True

    async def on_disconnect(self, sid: str) -> None:
        """
        Handle client disconnection.

        Args:
            sid: Session ID
        """
        logger.info(f"Client disconnected: {sid}")
        if sid in self.connected_clients:
            del self.connected_clients[sid]

    async def on_subscribe_country(self, sid: str, data: dict) -> dict:
        """
        Subscribe to updates for a specific country.

        Args:
            sid: Session ID
            data: {"country_code": "ES"}

        Returns:
            Subscription confirmation
        """
        country_code = data.get("country_code", "").upper()
        if not country_code or len(country_code) != 2:
            return {"error": "Invalid country code"}

        room = f"country:{country_code}"
        await self.enter_room(sid, room)

        if sid in self.connected_clients:
            self.connected_clients[sid]["rooms"].add(room)

        logger.debug(f"Client {sid} subscribed to {room}")
        return {"subscribed": room}

    async def on_unsubscribe_country(self, sid: str, data: dict) -> dict:
        """
        Unsubscribe from country updates.

        Args:
            sid: Session ID
            data: {"country_code": "ES"}

        Returns:
            Unsubscription confirmation
        """
        country_code = data.get("country_code", "").upper()
        room = f"country:{country_code}"
        await self.leave_room(sid, room)

        if sid in self.connected_clients:
            self.connected_clients[sid]["rooms"].discard(room)

        logger.debug(f"Client {sid} unsubscribed from {room}")
        return {"unsubscribed": room}

    async def on_subscribe_loan(self, sid: str, data: dict) -> dict:
        """
        Subscribe to updates for a specific loan.

        Args:
            sid: Session ID
            data: {"loan_id": "uuid"}

        Returns:
            Subscription confirmation
        """
        loan_id = data.get("loan_id")
        if not loan_id:
            return {"error": "loan_id required"}

        room = f"loan:{loan_id}"
        await self.enter_room(sid, room)

        if sid in self.connected_clients:
            self.connected_clients[sid]["rooms"].add(room)

        logger.debug(f"Client {sid} subscribed to {room}")
        return {"subscribed": room}

    async def on_unsubscribe_loan(self, sid: str, data: dict) -> dict:
        """
        Unsubscribe from loan updates.

        Args:
            sid: Session ID
            data: {"loan_id": "uuid"}

        Returns:
            Unsubscription confirmation
        """
        loan_id = data.get("loan_id")
        room = f"loan:{loan_id}"
        await self.leave_room(sid, room)

        if sid in self.connected_clients:
            self.connected_clients[sid]["rooms"].discard(room)

        logger.debug(f"Client {sid} unsubscribed from {room}")
        return {"unsubscribed": room}


# Create namespace instance
loan_namespace = LoanNamespace("/loans")

# Register namespace
sio.register_namespace(loan_namespace)


# Helper functions for emitting events
async def emit_loan_created(
    loan_id: str,
    country_code: str,
    loan_data: dict,
) -> None:
    """
    Emit event when a new loan is created.

    Args:
        loan_id: The loan UUID
        country_code: Country code
        loan_data: Loan details
    """
    event_data = {
        "event": "loan_created",
        "loan_id": loan_id,
        "country_code": country_code,
        "data": loan_data,
    }

    # Emit to all, country room, and loan room
    await sio.emit("loan_created", event_data, namespace="/loans", room="all")
    await sio.emit(
        "loan_created",
        event_data,
        namespace="/loans",
        room=f"country:{country_code}",
    )

    logger.debug(f"Emitted loan_created for {loan_id}")


async def emit_loan_updated(
    loan_id: str,
    country_code: str,
    changes: dict,
) -> None:
    """
    Emit event when a loan is updated.

    Args:
        loan_id: The loan UUID
        country_code: Country code
        changes: Dictionary of changes
    """
    event_data = {
        "event": "loan_updated",
        "loan_id": loan_id,
        "country_code": country_code,
        "changes": changes,
    }

    # Emit to relevant rooms
    await sio.emit("loan_updated", event_data, namespace="/loans", room="all")
    await sio.emit(
        "loan_updated",
        event_data,
        namespace="/loans",
        room=f"country:{country_code}",
    )
    await sio.emit(
        "loan_updated",
        event_data,
        namespace="/loans",
        room=f"loan:{loan_id}",
    )

    logger.debug(f"Emitted loan_updated for {loan_id}")


async def emit_status_changed(
    loan_id: str,
    country_code: str,
    old_status: str,
    new_status: str,
) -> None:
    """
    Emit event when loan status changes.

    Args:
        loan_id: The loan UUID
        country_code: Country code
        old_status: Previous status
        new_status: New status
    """
    event_data = {
        "event": "status_changed",
        "loan_id": loan_id,
        "country_code": country_code,
        "old_status": old_status,
        "new_status": new_status,
    }

    # Emit to relevant rooms
    await sio.emit("status_changed", event_data, namespace="/loans", room="all")
    await sio.emit(
        "status_changed",
        event_data,
        namespace="/loans",
        room=f"country:{country_code}",
    )
    await sio.emit(
        "status_changed",
        event_data,
        namespace="/loans",
        room=f"loan:{loan_id}",
    )

    logger.info(f"Emitted status_changed for {loan_id}: {old_status} -> {new_status}")
