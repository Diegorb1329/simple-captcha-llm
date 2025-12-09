"""
Fetch the raw HTML of the SAT certificate recovery page and print it.

Usage:
  python fetch_html.py
  python fetch_html.py --url https://example.com

Note: The SAT server uses weak DH keys, so we lower the SSL security level.
"""

from __future__ import annotations

import argparse
import ssl
import sys
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


DEFAULT_URL = (
    "https://portalsat.plataforma.sat.gob.mx/RecuperacionDeCertificados/"
    "faces/recuperaRFC.xhtml"
)


class LegacySSLAdapter(HTTPAdapter):
    """HTTP adapter for legacy servers with weak DH keys and cert issues."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        # Lower security level to allow weak DH params
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        # Disable certificate verification (required for some gov sites)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def fetch_html(url: str, timeout: int = 15) -> str:
    """Return the HTML for the given URL or raise an error."""
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    session = requests.Session()
    session.mount("https://", LegacySSLAdapter())
    resp = session.get(url, headers=headers, timeout=timeout, verify=False)
    resp.raise_for_status()
    return resp.text


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download and print HTML of the SAT recovery page."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Target URL to fetch (defaults to SAT recovery page).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Request timeout in seconds (default: 15).",
    )
    args = parser.parse_args(argv)

    try:
        html = fetch_html(args.url, timeout=args.timeout)
    except Exception as exc:  # pragma: no cover - simple CLI guard
        print(f"Error fetching HTML: {exc}", file=sys.stderr)
        return 1

    print(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

