"""
Connection Manager - Manages proxy connection state and lifecycle.

This module tracks the current connection status, manages xray-core process,
and handles connection state transitions.
"""

import time
from typing import Optional, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from settings import SettingsManager


class ConnectionStatus(Enum):
    """Connection status enumeration."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    BLOCKED = "blocked"


class ConnectionState:
    """
    Manages the current connection state.

    Tracks:
    - Connection status
    - Process information (xray-core PID)
    - Timestamps
    - Error information
    - Active configuration
    """

    def __init__(self):
        self.status: ConnectionStatus = ConnectionStatus.DISCONNECTED
        self.connected_at: Optional[float] = None
        self.disconnected_at: Optional[float] = None
        self.error_message: Optional[str] = None
        self.error_code: Optional[str] = None
        self.xray_process_id: Optional[int] = None
        self.xray_config_path: Optional[str] = None
        self.active_config: Optional[Dict[str, Any]] = None
        self.bytes_sent: int = 0
        self.bytes_received: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert connection state to dictionary for API responses."""
        result = {
            "status": self.status.value,
            "bytesSent": self.bytes_sent,
            "bytesReceived": self.bytes_received,
        }

        if self.connected_at:
            result["connectedAt"] = int(self.connected_at)
            if self.status == ConnectionStatus.CONNECTED:
                result["uptime"] = int(time.time() - self.connected_at)

        if self.disconnected_at:
            result["disconnectedAt"] = int(self.disconnected_at)

        if self.error_message:
            result["errorMessage"] = self.error_message

        if self.error_code:
            result["errorCode"] = self.error_code

        if self.xray_process_id:
            result["processId"] = self.xray_process_id

        if self.xray_config_path:
            result["configPath"] = self.xray_config_path

        return result

    def set_connecting(self):
        """Set status to connecting."""
        self.status = ConnectionStatus.CONNECTING
        self.error_message = None
        self.error_code = None

    def set_connected(self, process_id: int, config_path: str, config: Dict[str, Any]):
        """Set status to connected."""
        self.status = ConnectionStatus.CONNECTED
        self.connected_at = time.time()
        self.disconnected_at = None
        self.xray_process_id = process_id
        self.xray_config_path = config_path
        self.active_config = config
        self.error_message = None
        self.error_code = None

    def set_disconnected(self):
        """Set status to disconnected."""
        self.status = ConnectionStatus.DISCONNECTED
        self.disconnected_at = time.time()
        self.xray_process_id = None
        self.xray_config_path = None
        self.active_config = None

    def set_error(self, error_message: str, error_code: Optional[str] = None):
        """Set status to error."""
        self.status = ConnectionStatus.ERROR
        self.error_message = error_message
        self.error_code = error_code
        self.disconnected_at = time.time()
        self.xray_process_id = None

    def set_blocked(self):
        """Set status to blocked (kill switch active)."""
        self.status = ConnectionStatus.BLOCKED


# Global connection state instance
_connection_state = ConnectionState()


def get_connection_state() -> ConnectionState:
    """Get the global connection state instance."""
    return _connection_state


def load_connection_state_from_settings(settings: "SettingsManager") -> None:
    """
    Load connection state from SettingsManager on plugin startup.

    Args:
        settings: SettingsManager instance
    """
    try:
        saved_state = settings.getSetting("connectionState", {})
        status_str = saved_state.get("status", "disconnected")

        # Map string status to enum
        status_map = {
            "disconnected": ConnectionStatus.DISCONNECTED,
            "connecting": ConnectionStatus.CONNECTING,
            "connected": ConnectionStatus.CONNECTED,
            "error": ConnectionStatus.ERROR,
            "blocked": ConnectionStatus.BLOCKED,
        }

        _connection_state.status = status_map.get(
            status_str, ConnectionStatus.DISCONNECTED
        )

        # Note: Process ID and config path are not persisted (recreated on restart)
        # Only status is persisted for UI restoration
    except Exception as e:
        print(f"Warning: Failed to load connection state from settings: {e}")
        # Default to disconnected on error
        _connection_state.status = ConnectionStatus.DISCONNECTED
