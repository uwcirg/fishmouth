from flask import current_app
import json

from .fhir_client import extract_resource, post_resource_upstream, post_resource_app_fhir
from .map_resource import map_patient_references


def update_identifier(resource, system, value):
    """Add or update identifier field with given system|value

    :param resource: resource to gain identifier, or have value updated.
    :param system: identifier system to add or update with given value.
    :param value: new value to add.

    :return: updated identifier(s).
    """
    identifiers = resource.get("identifier", [])
    updated = False
    for identifier in identifiers:
        if identifier["system"] == system:
            identifier["value"] = value
            updated = True
            break

    if not updated:
        identifiers.append({"system": system, "value": value})
    resource["identifier"] = identifiers
    return resource


def unprocessable_entity(message):
    """Wrapper to generate response dict for unprocessable entity"""
    return dict(response={
        "status": "422 Unprocessable Entity",
        "outcome": {
            "resourceType": "OperationalOutcome",
            "issue": [
                {
                    "severity": "error",
                    "details": {
                        "text": message
                    }
                }
            ]
        }
    })


def entry_from_bundle(bundle):
    """Extract single response from bundle"""
    if not bundle.get("resourceType") == "Bundle":
        return unprocessable_entity(f"response lookup failed in {bundle}")
    if len(bundle["entry"]) != 1:
        return unprocessable_entity(f"response lookup failed in {bundle}")
    return bundle["entry"][0]


def process_questionnaire_response(resource):
    """Given a QuestionnaireResponse, react as requested

    :return: response dict conformant to transaction-response bundle
    """
    assert(resource["resourceType"] == "QuestionnaireResponse")
    try:
        extracted = extract_resource(resource)
    except Exception as e:
        try:
            error_data = json.loads(str(e))
            msg = f'FHIR $extract failed {error_data["issue"][0]["diagnostics"]}'
        except (json.JSONDecodeError, KeyError, IndexError) as x:
            msg = f"FHIR $extract failed: {e} ; could not parse error: {x}"
        current_app.logger.exception(msg)
        return unprocessable_entity(msg)

    # single QuestionnaireResponse will likely generate many Observations
    for resource in extracted.get("entry", []):
        resource = resource.get("resource")  # remove nested bundle format

        # Map any contained Patient references to UPSTREAM ids.
        mapped_resource = map_patient_references(resource)

        remote_id = None
        try:
            results = post_resource_upstream(mapped_resource)
            remote_id = results["id"]
        except Exception as e:
            msg = f"FHIR UPSTREAM POST failed {e}"
            current_app.logger.exception(msg)

        if resource.get("resourceType") and resource["resourceType"] in (
                current_app.config["EXTRACTED_RESOURCES_PERSISTED_IN_APP_FHIR"]):
            if remote_id:
                resource = update_identifier(
                    resource=resource,
                    system=current_app.config["UPSTREAM_FHIR_URL"],
                    value=remote_id)

            post_resource_app_fhir(resource)

    # given the mismatch between a single QuestionnaireResponse and
    # potentially many Observations, return the success/failure of
    # the extraction process alone.
    return dict(response={"status": "200 OK"})
