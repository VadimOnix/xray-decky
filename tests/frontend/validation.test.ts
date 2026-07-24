import { describe, expect, it } from 'vitest';

import { getValidationErrorMessage, validateVLESSURL } from '../../src/utils/validation';

describe('validateVLESSURL', () => {
  it.each([
    ['vless://uuid@example.com:443?security=reality#name'],
    ['VLESS://uuid@example.com:443'],
    ['trojan://password@example.com:443'],
    ['ss://YWVzLTI1Ni1nY206cGFzcw@example.com:8388'],
    ['hysteria2://password@example.com:443'],
    ['hy2://password@example.com:443'],
    ['tuic://uuid:password@example.com:443'],
    ['vmess://eyJhZGQiOiJleGFtcGxlLmNvbSJ9'],
    ['https://sub.example.com/link'],
    ['http://sub.example.com/link'],
  ])('accepts %s', (url) => {
    expect(validateVLESSURL(url)).toBe(true);
  });

  it('accepts a bare base64 subscription blob', () => {
    expect(validateVLESSURL('dmxlc3M6Ly91dWlkQGV4YW1wbGUuY29tOjQ0Mw==')).toBe(true);
  });

  it('trims surrounding whitespace before matching', () => {
    expect(validateVLESSURL('  vless://uuid@example.com:443  ')).toBe(true);
  });

  it.each([
    ['', 'empty string'],
    ['   ', 'whitespace only'],
    ['not a link', 'free text'],
    ['vless://', 'scheme with no body'],
    ['vless://uuid@example.com', 'missing port'],
    ['vless://uuid@example.com:notaport', 'non-numeric port'],
    ['trojan://example.com:443', 'no credentials'],
    ['ftp://example.com/sub', 'unsupported scheme'],
    ['c2hvcnQ=', 'base64 blob under the length floor'],
  ])('rejects %s (%s)', (url) => {
    expect(validateVLESSURL(url)).toBe(false);
  });

  it('rejects non-string input defensively', () => {
    // The QAM passes text-input values straight through; a null slipping in
    // must not throw inside the panel's onChange path.
    expect(validateVLESSURL(undefined as unknown as string)).toBe(false);
    expect(validateVLESSURL(null as unknown as string)).toBe(false);
  });
});

describe('getValidationErrorMessage', () => {
  it('falls back to a generic message when the backend sent none', () => {
    expect(getValidationErrorMessage()).toBe('Invalid share link format');
    expect(getValidationErrorMessage('')).toBe('Invalid share link format');
  });

  it('expands known backend errors into actionable text', () => {
    expect(getValidationErrorMessage('Invalid VLESS URL format')).toContain('subscription URL');
    expect(getValidationErrorMessage('Failed to fetch subscription')).toContain(
      'internet connection'
    );
  });

  it('passes unknown backend errors through unchanged', () => {
    expect(getValidationErrorMessage('Server refused the connection')).toBe(
      'Server refused the connection'
    );
  });
});
