"""Health check blueprint."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/live")
def live():
    """Liveness probe."""
    return jsonify({"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


@health_bp.get("/ready")
def ready():
    """Readiness probe. Future checks can include DB/cache connectivity."""
    checks = {
        "firestore": "deferred",
        "websocket_gateway": "deferred",
    }
    return (
        jsonify(
            {
                "status": "ready",
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ),
        200,
    )


