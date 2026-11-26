"""CORS con lista explícita de orígenes, sin comodines ni credenciales (AD-14, SECURITY-08)."""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS


def registrar(app: Flask, origenes: tuple[str, ...]) -> None:
    CORS(
        app,
        resources={r"/v1/*": {"origins": list(origenes)}},
        methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type", "User-Agent", "X-Amzn-Trace-Id"],
        expose_headers=["X-Request-Id"],
        supports_credentials=False,
        max_age=600,
    )
