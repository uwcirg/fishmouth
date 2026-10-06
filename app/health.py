from flask import Blueprint, current_app, jsonify
import requests

bp = Blueprint("health", __name__)


@bp.route("/health/live")
def live():
    return jsonify({"status": "ok"}), 200


@bp.route("/health/ready")
def ready():
    base = current_app.config["APP_FHIR_URL"]
    response = requests.get(f"{base}/metadata")
    response.raise_for_status()

    base = current_app.config["UPSTREAM_FHIR_URL"]
    response = requests.get(f"{base}/metadata")
    response.raise_for_status()

    # only test search, if it is configured
    base = current_app.config["UPSTREAM_SEARCH_URL"]
    if base:
        response = requests.get(f"{base}/metadata")
        response.raise_for_status()

    return jsonify({"status": "ready"}), 200
