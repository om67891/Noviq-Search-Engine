"""
Tests for SSRF protection.

Verifies that the SSRF guard blocks private/internal network addresses
and allows legitimate public addresses.
"""
import pytest
from app.discovery.ssrf_guard import validate_url, SSRFError, guard


class TestSSRFGuard:
    """Test cases for SSRF URL validation."""

    # --- Blocked cases ---

    def test_localhost_http_blocked(self):
        ok, reason = validate_url("http://localhost/admin")
        assert not ok
        assert "blocked" in reason.lower() or "loopback" in reason.lower() or "private" in reason.lower() or "localhost" in reason.lower()

    def test_localhost_https_blocked(self):
        ok, reason = validate_url("https://localhost:8080/secret")
        assert not ok

    def test_127_0_0_1_blocked(self):
        ok, reason = validate_url("http://127.0.0.1/")
        assert not ok

    def test_127_loopback_range_blocked(self):
        ok, reason = validate_url("http://127.255.255.255/")
        assert not ok

    def test_10_x_private_blocked(self):
        ok, reason = validate_url("http://10.0.0.1/internal")
        assert not ok

    def test_192_168_private_blocked(self):
        ok, reason = validate_url("http://192.168.1.1/router")
        assert not ok

    def test_172_16_private_blocked(self):
        ok, reason = validate_url("http://172.16.0.1/")
        assert not ok

    def test_169_254_metadata_blocked(self):
        # AWS/GCP metadata endpoint
        ok, reason = validate_url("http://169.254.169.254/latest/meta-data/")
        assert not ok

    def test_ftp_scheme_blocked(self):
        ok, reason = validate_url("ftp://example.com/file.txt")
        assert not ok
        assert "scheme" in reason.lower() or "not allowed" in reason.lower()

    def test_file_scheme_blocked(self):
        ok, reason = validate_url("file:///etc/passwd")
        assert not ok

    def test_empty_url_blocked(self):
        ok, reason = validate_url("")
        assert not ok

    def test_no_hostname_blocked(self):
        ok, reason = validate_url("http:///path")
        assert not ok

    # --- Allowed cases ---

    def test_public_http_allowed(self):
        ok, reason = validate_url("http://example.com/page")
        assert ok, f"Expected ok but got: {reason}"

    def test_public_https_allowed(self):
        ok, reason = validate_url("https://reuters.com/world/")
        assert ok, f"Expected ok but got: {reason}"

    def test_guard_raises_on_localhost(self):
        with pytest.raises(SSRFError):
            guard("http://127.0.0.1/secret")

    def test_guard_passes_on_public(self):
        # Should not raise
        guard("https://example.com/")
