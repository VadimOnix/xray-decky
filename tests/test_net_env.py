"""Tests for backend.src.net_env (Decky sandbox network-environment repair)."""

import ssl
from unittest.mock import patch

from backend.src import net_env


# --- clean_subprocess_env ---


def test_clean_env_drops_every_sandbox_variable():
    dirty = {
        "PATH": "/usr/bin",
        "LD_LIBRARY_PATH": "/tmp/_MEIabc",
        "LD_PRELOAD": "/tmp/_MEIabc/libz.so",
        "SSL_CERT_FILE": "/tmp/_MEIabc/certifi/cacert.pem",
        "SSL_CERT_DIR": "/tmp/_MEIabc/certs",
        "CURL_CA_BUNDLE": "/tmp/_MEIabc/certifi/cacert.pem",
        "REQUESTS_CA_BUNDLE": "/tmp/_MEIabc/certifi/cacert.pem",
        "OPENSSL_CONF": "/tmp/_MEIabc/openssl.cnf",
    }
    cleaned = net_env.clean_subprocess_env(dirty)
    assert cleaned == {"PATH": "/usr/bin"}
    # The caller's mapping is never mutated.
    assert "LD_LIBRARY_PATH" in dirty


def test_clean_env_is_a_noop_on_an_already_clean_environment():
    clean = {"PATH": "/usr/bin", "HOME": "/root"}
    assert net_env.clean_subprocess_env(clean) == clean


def test_clean_env_defaults_to_the_process_environment():
    with patch.dict("os.environ", {"LD_PRELOAD": "/tmp/_MEIabc/x.so"}, clear=False):
        assert "LD_PRELOAD" not in net_env.clean_subprocess_env()


# --- system_ca_bundle ---


def test_system_ca_bundle_picks_the_first_existing_candidate():
    net_env.system_ca_bundle.cache_clear()
    present = net_env.CA_BUNDLE_CANDIDATES[-1]
    with patch("os.path.isfile", lambda p: p == present):
        assert net_env.system_ca_bundle() == present
    net_env.system_ca_bundle.cache_clear()


def test_system_ca_bundle_is_none_when_no_candidate_exists():
    net_env.system_ca_bundle.cache_clear()
    with patch("os.path.isfile", lambda _p: False):
        assert net_env.system_ca_bundle() is None
    net_env.system_ca_bundle.cache_clear()


# --- client_ssl_context ---


def test_client_ssl_context_pins_the_system_bundle():
    """
    The context must not be left to read SSL_CERT_FILE/SSL_CERT_DIR, which the
    sandbox may point at a path that verifies nothing.
    """
    loaded = []

    class _Ctx:
        def load_verify_locations(self, cafile=None, **_kw):
            loaded.append(cafile)

    with patch.object(net_env, "system_ca_bundle", lambda: "/etc/ssl/ca.pem"):
        with patch("ssl.create_default_context", lambda: _Ctx()):
            ctx = net_env.client_ssl_context()

    assert ctx is not None
    assert loaded == ["/etc/ssl/ca.pem"]


def test_client_ssl_context_falls_back_to_default_when_no_bundle_found():
    with patch.object(net_env, "system_ca_bundle", lambda: None):
        ctx = net_env.client_ssl_context()
    # Still a usable context — never None, or callers would silently downgrade.
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_client_ssl_context_survives_an_unreadable_bundle():
    def _boom(cafile=None, **_kw):
        raise OSError("unreadable")

    class _Ctx:
        verify_mode = ssl.CERT_REQUIRED
        load_verify_locations = staticmethod(_boom)

    with patch.object(net_env, "system_ca_bundle", lambda: "/etc/ssl/ca.pem"):
        with patch("ssl.create_default_context", lambda: _Ctx()):
            assert net_env.client_ssl_context() is not None
