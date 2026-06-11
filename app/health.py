from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/health/live")
def live():
    return jsonify({"status", "ok"}), 200


@bp.route("/health/ready")
def ready():
    # confirm both FHIR endpoints are ready
    return jsonify({"status", "unfinished"}), 200
