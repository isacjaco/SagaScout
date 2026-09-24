"""Tests for the FastAPI application."""

from sagascout.api import health


def test_health_endpoint():
    """Test that the health endpoint returns the correct status and version."""
    result = health()
    assert result == {"status": "ok", "version": "0.1.0"}
