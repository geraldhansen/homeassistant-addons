import logging
import os
from dataclasses import asdict
from pathlib import Path

from flask import Flask, jsonify, request, Response, send_from_directory

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def create_app(coordinator, log_buffer):
    app = Flask(__name__, static_folder=None)

    # ------------------------------------------------------------------ #
    # Pages                                                                #
    # ------------------------------------------------------------------ #

    @app.route("/")
    def index():
        html = (STATIC_DIR / "index.html").read_text()
        ingress_path = request.headers.get("X-Ingress-Path", "")
        html = html.replace("__INGRESS_PATH__", ingress_path)
        return Response(html, content_type="text/html")

    @app.route("/static/<path:filename>")
    def static_files(filename):
        return send_from_directory(STATIC_DIR, filename)

    # ------------------------------------------------------------------ #
    # API                                                                  #
    # ------------------------------------------------------------------ #

    @app.route("/api/status")
    def api_status():
        state = coordinator.get_state()
        if not coordinator.config.is_s3_configured():
            state["warning"] = "S3 is not configured. Go to Settings to enter your bucket details."
        return jsonify(state)

    @app.route("/api/backup", methods=["POST"])
    def api_backup():
        body = request.get_json(silent=True) or {}
        return jsonify(coordinator.create_backup(body.get("name")))

    @app.route("/api/sync", methods=["POST"])
    def api_sync():
        return jsonify(coordinator.sync())

    @app.route("/api/upload/<slug>", methods=["POST"])
    def api_upload(slug):
        return jsonify(coordinator.upload_to_s3(slug))

    @app.route("/api/ha/<slug>", methods=["DELETE"])
    def api_delete_ha(slug):
        return jsonify(coordinator.delete_from_ha(slug))

    @app.route("/api/s3/<slug>", methods=["DELETE"])
    def api_delete_s3(slug):
        return jsonify(coordinator.delete_from_s3(slug))

    @app.route("/api/settings")
    def api_get_settings():
        data = asdict(coordinator.config)
        if data.get("s3_secret_key"):
            data["s3_secret_key_set"] = True
        return jsonify(data)

    @app.route("/api/settings", methods=["POST"])
    def api_save_settings():
        logger.debug("/api/settings called with body: %s", request.get_json())
        from .config import Config
        body = request.get_json(silent=True) or {}
        test_only = body.pop("test_only", False)

        current = asdict(coordinator.config)
        # Keep existing secret if not provided
        if not body.get("s3_secret_key") and current.get("s3_secret_key"):
            body["s3_secret_key"] = current["s3_secret_key"]

        new_config = Config(**{
            k: v for k, v in {**current, **body}.items()
            if k in Config.__dataclass_fields__
        })

        if test_only:
            from .s3_client import S3Client
            return jsonify(S3Client(new_config).test_connection())

        new_config.save()
        coordinator.reload_config(new_config)
        logger.info("Settings saved and reloaded")
        return jsonify({"ok": True})

    @app.route("/api/logs")
    def api_logs():
        return jsonify(log_buffer.get_logs())

    @app.errorhandler(Exception)
    def handle_error(e):
        logger.error("Unhandled error: %s", e)
        return jsonify({"error": str(e)}), 500

    return app
