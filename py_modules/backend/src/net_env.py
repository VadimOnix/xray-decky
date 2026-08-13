"""
Repairs the network environment the Decky plugin sandbox hands us.

Decky Loader ships as a PyInstaller bundle. Its bootloader exports
``LD_LIBRARY_PATH``/``LD_PRELOAD`` pointing into the extracted ``/tmp/_MEI*``
directory, and PyInstaller-packaged launchers also export ``SSL_CERT_FILE`` /
``SSL_CERT_DIR`` at their bundled certifi copy. Plugin backends are spawned as
child processes, so they inherit all of it.

Both halves break TLS, in different ways:

* the bundled ``libssl.so.3`` is older than SteamOS's — running any system
  binary that links OpenSSL under that ``LD_LIBRARY_PATH`` dies with
  ``version 'OPENSSL_3.2.0' not found`` before it opens a socket;
* a CA path that does not resolve to real roots makes certificate
  verification fail for every client, while leaving *server* TLS (which needs
  no CA store) working — so the plugin's own HTTPS admin panel keeps serving
  while every outbound HTTPS request fails.

Either way the signature is the same and easy to misread: plain HTTP works,
every HTTPS request fails instantly, and the failure looks like a bad URL.

``xray_downloader`` and ``singbox_downloader`` already scrubbed the two ``LD_*``
variables before spawning curl; this module is the shared and complete version
of that fix, plus the client-side CA pinning that in-process aiohttp needs.
"""

import os
import ssl
from functools import lru_cache
from typing import Dict, Mapping, Optional

# Variables the Decky/PyInstaller sandbox exports that redirect a child process
# (or this one) at the bundle's libraries and CA material instead of the
# system's. Dropping them is always safe: the system defaults are what every
# other program on the device already uses.
SANDBOX_ENV_VARS = (
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "CURL_CA_BUNDLE",
    "REQUESTS_CA_BUNDLE",
    "OPENSSL_CONF",
)

# Where distributions keep the concatenated trust store. SteamOS (Arch) uses the
# first entry; the rest keep this working if the plugin is ever run elsewhere.
CA_BUNDLE_CANDIDATES = (
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
    "/etc/ssl/ca-bundle.pem",
    "/etc/ssl/cert.pem",
)


def clean_subprocess_env(env: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """
    A copy of ``env`` (default: this process's environment) with the sandbox
    overrides removed, for handing to system binaries such as curl or openssl.
    """
    source = os.environ if env is None else env
    return {k: v for k, v in source.items() if k not in SANDBOX_ENV_VARS}


@lru_cache(maxsize=1)
def system_ca_bundle() -> Optional[str]:
    """Path to the system trust store, or None if no known location exists."""
    for candidate in CA_BUNDLE_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return None


def client_ssl_context() -> ssl.SSLContext:
    """
    A verifying SSL context pinned to the system trust store.

    Pinned explicitly rather than left to the default, because the default
    reads ``SSL_CERT_FILE``/``SSL_CERT_DIR`` — the very variables the sandbox
    may have pointed somewhere useless. Always returns a verifying context:
    falling back to an unverified one would turn a connection error into a
    silent downgrade.
    """
    context = ssl.create_default_context()
    bundle = system_ca_bundle()
    if bundle:
        try:
            context.load_verify_locations(cafile=bundle)
        except OSError as e:
            # Keep the default trust material rather than failing the request.
            print(f"Xray Decky Plugin: could not load {bundle}: {type(e).__name__}")
    return context
