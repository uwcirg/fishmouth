from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest

from .services.process_resource import process_questionnaire_response

bp = Blueprint("api", __name__)

@bp.route("/extract-n-post", methods=["POST"])
def extract_n_post():
    """
    Given a FHIR resource bundle of type `subscription-notification`,
    triggers $extract on APP_FHIR server, and subsequently posts the
    results to the UPSTREAM_FHIR_URL endpoint.

    In the event of an error, the process short circuits and returns the
    appropriate status code and message.

    In the event of success, the return bundle will include ordered entries
    matching the sequence of the given resource bundle, including extracted
    resources.

    :return: transaction-response bundle, with ordered entries with the
      status of each respective entry or exception details.
    """
    if not request.is_json:
        return jsonify({"error": "Expected JSON"}), 400
    resource = request.get_json(silent=True)
    if not resource:
        return jsonify({"error": "Invalid JSON"}), 400
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
    status = 200
    for entry in entries:
        if status != 200:
            break
        entry_type = entry["resource"].get("resourceType")
        # skip over SubscriptionStatus
        if entry_type == "SubscriptionStatus":
            entry_results.append({"response": {"status": "200 OK"}})
            continue

        # Only know how to process QuestionnaireResponse, for now
        if entry_type != "QuestionnaireResponse":
            entry_results.append({"response": {"status": "501 Not Implemented"}})
            status = 501
            break

        result = process_questionnaire_response(entry["resource"])
        status = int(result["response"]["status"].split()[0])
        if "bundle" in result["response"]:
            entry_results.append({"response": result["response"]["bundle"]})
        else:
            entry_results.append(result)

    results_bundle.update(entry=entry_results)
    return jsonify(results_bundle), status


@bp.route("/settings")
def settings():
    config_settings = {}
    for key in current_app.config:
        if "password" in key.lower():
            continue
        config_settings[key] = str(current_app.config[key])
    return jsonify(config_settings)


@bp.before_app_request
def before_request():
        if current_app.config.get("DEBUG_DUMP_HEADERS"):
            current_app.logger.debug(
                "{0.remote_addr} {0.method} {0.path} {0.headers}".format(request))
        if current_app.config.get("DEBUG_DUMP_REQUEST"):
            output = "{0.remote_addr} {0.method} {0.path}"
            if request.data:
                output += " {data}"
            if request.args:
                output += " {0.args}"
            if request.form:
                output += " {0.form}"
            current_app.logger.debug(output.format(
                request,
                data=request.get_data(as_text=True),
            ))


@bp.errorhandler(BadRequest)
def handle_bad_request(error):
    current_app.logger.error(f"Bad Request; internal error: {error.description}")
    return jsonify({"error": "Bad Request"}), 400
