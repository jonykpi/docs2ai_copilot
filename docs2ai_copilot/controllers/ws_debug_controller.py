import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class Docs2AIWsDebugController(http.Controller):
    """Collect WebSocket debug logs coming from the frontend."""

    @http.route(
        "/docs2ai/ws/log",
        type="http",
        auth="user",
        methods=["POST"],
        csrf=False,
    )
    def log_ws_event(self, **_kwargs):
        payload = {}
        raw_body = request.httprequest.data
        if raw_body:
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (ValueError, json.JSONDecodeError):
                payload = {"raw_body": raw_body.decode("utf-8", errors="ignore")}

        level = (payload.get("level") or "info").lower()
        message = payload.get("message") or "Frontend WS log"
        metadata = payload.get("metadata") or {}
        user = request.env.user
        log_line = (
            f"[Docs2AI WS] user={user.id}({user.login}) level={level} message={message} metadata={metadata}"
        )

        if level == "error":
            _logger.error(log_line)
        elif level in ("warning", "warn"):
            _logger.warning(log_line)
        else:
            _logger.info(log_line)

        return request.make_json_response({"status": "ok"})





