from flask import Blueprint, request, jsonify, current_app
from .services.fhir_client import extract_resource, post_resource_upstream

bp = Blueprint("api", __name__)

@bp.route("/event", methods=["POST"])
def handle_event():
    """
    Receives a FHIR resource (typically QuestionnaireResponse)
    and triggers $extract on remote HAPI server.
    """

    if not request.is_json:
        return jsonify({"error": "Expected JSON"}), 400

    resource = request.get_json()

    resource_type = resource.get("resourceType")
    if not resource_type:
        return jsonify({"error": "Missing resourceType"}), 400

    current_app.logger.info("Received event for resourceType=%s", resource_type)

    # Only allow QuestionnaireResponse for now
    if resource_type != "QuestionnaireResponse":
        return jsonify({"error": "Unsupported resourceType"}), 400

    try:
        extracted = extract_resource(resource)
    except Exception as e:
        current_app.logger.exception("FHIR $extract failed {e}")
        return jsonify({
            "error": "FHIR extract failed",
            "details": str(e)
        }), 502

    try:
        results = post_resource_upstream(extracted)
    except Exception as e:
        current_app.logger.exception("FHIR UPSTREAM POST failed {e}")
        return jsonify({
            "error": "FHIR UPSTREAM POST failed",
            "details": str(e)
        }), 502

    return jsonify(results)
