from flask import current_app
from .fhir_client import extract_resource, post_resource_upstream

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


def successful_entity(message):
    """Wrapper to generate response dict for successful entity"""
    return dict(response={
        "status": "200 OK",
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
        msg = f"FHIR extract failed {e}"
        current_app.logger.exception(msg)
        return unprocessable_entity(msg)

    # single QuestionnaireResponse will likely generate many Observations
    for resource in extracted.get("entry", []):
        resource = resource.get("resource")  # remove nested bundle format
        if resource.get("resourceType") and resource["resourceType"] in (
                current_app.config["EXTRACTED_RESOURCES_PERSISTED_IN_APP_FHIR"]):
            # TODO write resource resource to APP_FHIR
            raise NotImplementedError("Writing extracted resources incomplete")

        try:
            results = post_resource_upstream(resource)
        except Exception as e:
            msg = f"FHIR UPSTREAM POST failed {e}"
            current_app.logger.exception(msg)

    # given the mismatch between a single QuestionnaireResponse and
    # potentially many Observations, return the success/failure of
    # the extraction process alone.
    return dict(response={"status": "200 OK"})

