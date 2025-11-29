"""Register strict security headers for every HTTP response."""

from __future__ import annotations

from flask import Flask

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.socket.io; style-src 'self' 'unsafe-inline'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; connect-src 'self' ws://localhost:* wss://localhost:* ws://127.0.0.1:* wss://127.0.0.1:*;",
}


def register_security_headers(app: Flask) -> None:
    """Attach after_request hook."""

    @app.after_request
    def _set_headers(response):
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


