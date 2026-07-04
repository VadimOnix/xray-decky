"""Tests for backend.src.refresh_scheduler (pure 'is a refresh due?' logic)."""

from backend.src.refresh_scheduler import (
    is_refresh_due,
    refresh_interval_hours,
)


def _sub(**extra):
    sub = {"url": "https://sub.example.com/s", "updatedAt": 1000}
    sub.update(extra)
    return sub


def test_refresh_interval_hours_reads_and_clamps():
    assert refresh_interval_hours(_sub(refreshIntervalHours=12)) == 12
    assert refresh_interval_hours(_sub(refreshIntervalHours=0)) == 0
    assert refresh_interval_hours(_sub()) == 0  # missing → disabled
    assert refresh_interval_hours(_sub(refreshIntervalHours=-5)) == 0
    assert refresh_interval_hours(_sub(refreshIntervalHours="bad")) == 0
    assert refresh_interval_hours(None) == 0


def test_not_due_when_disabled():
    # No interval configured → never due, however old.
    assert is_refresh_due(_sub(updatedAt=0), now=10**9) is False


def test_not_due_without_subscription_or_url():
    assert is_refresh_due(None, now=10**9) is False
    assert is_refresh_due({"refreshIntervalHours": 6}, now=10**9) is False  # no url


def test_due_only_after_interval_elapses():
    sub = _sub(updatedAt=1000, refreshIntervalHours=1)  # 1h = 3600s
    assert is_refresh_due(sub, now=1000 + 3599) is False
    assert is_refresh_due(sub, now=1000 + 3600) is True
    assert is_refresh_due(sub, now=1000 + 10000) is True


def test_missing_updated_at_is_due():
    # Missing/garbage updatedAt is treated as epoch 0, so any real "now" (well
    # past one interval) is due.
    sub = {"url": "https://s", "refreshIntervalHours": 6}
    assert is_refresh_due(sub, now=10**9) is True
    sub2 = {"url": "https://s", "refreshIntervalHours": 6, "updatedAt": "bad"}
    assert is_refresh_due(sub2, now=10**9) is True
