"""Socket.IO Package for real-time communication."""
from app.sockets.handlers import LoanNamespace, sio

__all__ = ["sio", "LoanNamespace"]
