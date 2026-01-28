/**
 * Validation utilities for frontend
 */

/**
 * Basic VLESS URL format validation (regex check before backend call)
 * 
 * @param url - VLESS URL to validate
 * @returns true if URL format looks valid, false otherwise
 */
export function validateVLESSURL(url: string): boolean {
  if (!url || typeof url !== "string") {
    return false;
  }

  const trimmed = url.trim();
  
  // Check if it's a VLESS URL pattern
  const vlessPattern = /^vless:\/\/[a-f0-9-]+@[^:]+:\d+/i;
  if (vlessPattern.test(trimmed)) {
    return true;
  }
  
  // Check if it might be a base64 subscription (basic check)
  // Base64 strings are typically longer and contain A-Z, a-z, 0-9, +, /, =
  const base64Pattern = /^[A-Za-z0-9+/=]+$/;
  if (base64Pattern.test(trimmed) && trimmed.length > 20) {
    return true; // Might be subscription, let backend validate
  }
  
  return false;
}

/**
 * Get a user-friendly error message for validation failures
 * 
 * @param error - Error message from backend
 * @returns User-friendly error message
 */
export function getValidationErrorMessage(error?: string): string {
  if (!error) {
    return "Invalid VLESS URL format";
  }
  
  // Map common error messages to user-friendly versions
  const errorMap: Record<string, string> = {
    "Invalid VLESS URL format": "Invalid VLESS URL format. Expected: vless://uuid@host:port?params#name",
    "Invalid UUID format": "Invalid UUID format in VLESS URL",
    "Port must be between 1 and 65535": "Port number must be between 1 and 65535",
    "Failed to fetch subscription": "Failed to fetch subscription. Please check your internet connection",
  };
  
  return errorMap[error] || error;
}
