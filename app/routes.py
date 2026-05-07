from flask import Blueprint, request, jsonify, current_app
from .services.process_resource import process_questionnaire_response

bp = Blueprint("api", __name__)

@bp.route("/extract-n-post", methods=["POST"])
def extract_n_post():
    """
    Given a FHIR resource bundle of type `subscription-notification`,
    triggers $extract on APP_FHIR server, and subsequently posts the
    results to the UPSTREAM_FHIR_URL endpoint.

    :return: transaction-response bundle, with ordered entries with the
      status of each respective entry or exception details.
    """
    if not request.is_json:
        return jsonify({"error": "Expected JSON"}), 400
    resource = request.get_json()
    resource_type = resource.get("resourceType")
    bundle_type = resource.get("type")
    entries = resource.get("entry", [])
    if not resource_type or resource_type != "Bundle" or bundle_type != "subscription-notification":
        return jsonify({"error": "Invalid; expecting Bundle of type `subscription-notification`"}), 400

    current_app.logger.info(f"Received event containing {len(entries)} entries")

    results_bundle = {
        "resourceType": "Bundle",
        "type": "transaction-response",
    }
    entry_results = []
    for entry in entries:
        entry_type = entry["resource"].get("resourceType")
        # skip over SubscriptionStatus
        if entry_type == "SubscriptionStatus":
            entry_results.append({"response": {"status": "200 OK"}})
            continue

        # Only know how to process QuestionnaireResponse, for now
        if entry_type != "QuestionnaireResponse":
            entry_results.append({"response": {"status": "501 Not Implemented"}})
            continue

        result = process_questionnaire_response(entry["resource"])
        entry_results.append(result)

    results_bundle.update(entry=entry_results)
    return jsonify(results_bundle)
