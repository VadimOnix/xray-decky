/**
 * Validation utilities for frontend
 */

/**
 * Basic share-link format validation (regex check before backend call).
 * Accepts vless://, vmess://, trojan://, ss:// and base64 subscriptions.
 *
 * @param url - Share link to validate
 * @returns true if the format looks valid, false otherwise
 */
export function validateVLESSURL(url: string): boolean {
  if (!url || typeof url !== 'string') {
    return false;
  }

  const trimmed = url.trim();

  // Links with credentials/host parts (details validated by the backend)
  const linkPatterns = [
    /^vless:\/\/.+@.+:\d+/i,
    /^trojan:\/\/.+@.+:\d+/i,
    /^ss:\/\/.+/i,
    /^(hysteria2|hy2|tuic):\/\/.+@.+:\d+/i,
    // vmess is a base64-encoded JSON payload
    /^vmess:\/\/[A-Za-z0-9+/=_-]+$/i,
    // subscription URL, fetched by the backend
    /^https?:\/\/.+/i,
  ];
  if (linkPatterns.some((pattern) => pattern.test(trimmed))) {
    return true;
  }

  // Check if it might be a base64 subscription (basic check)
  // Base64 strings are typically longer and contain A-Z, a-z, 0-9, +, /, =
  const base64Pattern = /^[A-Za-z0-9+/=_-]+$/;
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
    return 'Invalid share link format';
  }

  // Map common error messages to user-friendly versions
  const errorMap: Record<string, string> = {
    'Invalid VLESS URL format':
      'Invalid share link. Expected: vless://, vmess://, trojan://, ss://, a subscription URL (https://) or base64 subscription',
    'Invalid UUID format': 'Invalid UUID format in VLESS URL',
    'Port must be between 1 and 65535': 'Port number must be between 1 and 65535',
    'Failed to fetch subscription':
      'Failed to fetch subscription. Please check your internet connection',
  };

  return errorMap[error] || error;
}
