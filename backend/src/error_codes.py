"""
Error Codes and User-Friendly Messages

Centralized error handling with error codes and user-friendly messages.
"""

from typing import Dict, Optional, Any


# Error code constants
class ErrorCode:
    """Error code constants."""

    NO_CONFIG = "NO_CONFIG"
    INVALID_CONFIG = "INVALID_CONFIG"
    INVALID_URL = "INVALID_URL"
    NETWORK_ERROR = "NETWORK_ERROR"
    PRIVILEGES_INSUFFICIENT = "PRIVILEGES_INSUFFICIENT"
    PROCESS_FAILED = "PROCESS_FAILED"
    IPTABLES_FAILED = "IPTABLES_FAILED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    CONNECTION_FAILED = "CONNECTION_FAILED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTION_ACTIVE = "CONNECTION_ACTIVE"


# User-friendly error messages
ERROR_MESSAGES: Dict[str, str] = {
    ErrorCode.NO_CONFIG: "No VLESS configuration stored. Please import a configuration first.",
    ErrorCode.INVALID_CONFIG: "The stored VLESS configuration is invalid. Please import a new configuration.",
    ErrorCode.INVALID_URL: "Invalid VLESS URL format. Please check the URL and try again.",
    ErrorCode.NETWORK_ERROR: "Network operation failed. Please check your internet connection and try again.",
    ErrorCode.PRIVILEGES_INSUFFICIENT: "TUN mode requires elevated privileges. Please complete the installation steps to enable TUN mode.",
    ErrorCode.PROCESS_FAILED: "Failed to start xray-core process. Please check the configuration and try again.",
    ErrorCode.IPTABLES_FAILED: "Failed to configure firewall rules. Kill switch may not work correctly.",
    ErrorCode.UNKNOWN_ERROR: "An unexpected error occurred. Please try again or check the logs.",
    ErrorCode.CONNECTION_FAILED: "Failed to establish connection. Please check your configuration and network.",
    ErrorCode.VALIDATION_ERROR: "Configuration validation failed. Please check your VLESS URL format.",
    ErrorCode.NOT_CONNECTED: "System proxy requires active connection. Please connect first.",
    ErrorCode.CONNECTION_ACTIVE: "Disconnect before resetting configuration.",
}


def get_error_message(error_code: str, default: Optional[str] = None) -> str:
    """
    Get user-friendly error message for an error code.

    Args:
        error_code: Error code constant
        default: Default message if error code not found

    Returns:
        User-friendly error message
    """
    return ERROR_MESSAGES.get(error_code, default or "An error occurred.")


def create_error_response(
    error_code: str, custom_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        error_code: Error code constant
        custom_message: Optional custom error message

    Returns:
        Dictionary with success=False and error information
    """
    message = custom_message or get_error_message(error_code)
    return {
        "success": False,
        "error": message,
        "errorCode": error_code,
    }


def create_success_response(data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a standardized success response.

    Args:
        data: Optional additional data to include

    Returns:
        Dictionary with success=True and optional data
    """
    response = {"success": True}
    if data:
        response.update(data)
    return response
