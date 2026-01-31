"""
TLS certificate utilities for the import HTTPS server.

Generates and stores a self-signed certificate in DECKY_PLUGIN_RUNTIME_DIR
so the import page is served over HTTPS (secure context for Paste).
Uses OpenSSL via subprocess so no extra Python deps (e.g. cryptography) are
required in Decky Loader runtime.
Contract: specs/002-vless-import-qr (HTTPS for import page).
"""

from pathlib import Path
import os
import subprocess


def _openssl_binary() -> str:
    """Use system OpenSSL on Linux (Decky sandbox PATH has incompatible bundled openssl)."""
    if os.path.isfile("/usr/bin/openssl") and os.access("/usr/bin/openssl", os.X_OK):
        return "/usr/bin/openssl"
    return "openssl"


def ensure_cert_key(runtime_dir: Path) -> tuple[Path, Path]:
    """
    Ensure cert.pem and key.pem exist in runtime_dir. If missing, generate
    a self-signed certificate (valid 365 days) via OpenSSL and save both files.
    Returns (cert_path, key_path). Raises on failure.
    """
    runtime_dir = Path(runtime_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    cert_path = runtime_dir / "cert.pem"
    key_path = runtime_dir / "key.pem"

    if cert_path.is_file() and key_path.is_file():
        return (cert_path, key_path)

    # Generate with system OpenSSL; use clean env so loader uses system libssl
    # (Decky sandbox sets LD_LIBRARY_PATH/LD_PRELOAD → /tmp/_MEI* incompatible libs)
    env = os.environ.copy()
    env.pop("LD_LIBRARY_PATH", None)
    env.pop("LD_PRELOAD", None)

    cmd = [
        _openssl_binary(), "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", str(key_path),
        "-out", str(cert_path),
        "-days", "365",
        "-nodes",
        "-subj", "/CN=localhost/O=Xray Decky Import",
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(runtime_dir),
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"OpenSSL cert generation failed: {result.stderr or result.stdout or 'unknown'}"
        )

    return (cert_path, key_path)
