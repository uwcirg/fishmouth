from flask import current_app
import json

from .fhir_client import extract_resource, request_resource_upstream, request_resource_app_fhir
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
    app_post_success, upstream_post_success = "n/a", "n/a"
    try:
        for resource in extracted.get("entry", []):
            resource = resource.get("resource")  # remove nested bundle format
            # $extract includes an ephemeral id that can't be included
            # when POSTing to either server - remove
            resource.pop("id")

            # Map any contained Patient references to UPSTREAM ids.
            mapped_resource = map_patient_references(resource)

            try:
                results = request_resource_upstream("post", mapped_resource)
                remote_id = results["id"]
                upstream_post_success = "success"
            except Exception as e:
                msg = f"FHIR UPSTREAM POST failed {e}"
                current_app.logger.exception(msg)
                # if upstream post fails, no value in persisting local
                raise e

            if resource.get("resourceType") and resource["resourceType"] in (
                    current_app.config["EXTRACTED_RESOURCES_PERSISTED_IN_APP_FHIR"]):
                resource = update_identifier(
                    resource=resource,
                    system=current_app.config["UPSTREAM_FHIR_URL"],
                    value=remote_id)

                request_resource_app_fhir("post", resource)
                app_post_success = "success"
    except Exception as e:
        current_app.logger.exception(e)
        return unprocessable_entity(str(e))

    # If no observations were extracted, treat as an error as clients
    # act on status to determine if the extraction was "successful"
    # NB 417 is intended to communicate the `Expect` request header
    # can't be fulfilled - using here to communicate the "Expectation
    # Failed" - namely that we expected to extract observations, but
    # none were found.
    if not len(extracted.get("entry", [])):
        current_app.logger.warning(
            f"nothing extracted from {resource}"
        )
        return dict(response={"status": "417 Expectation Failed"})

    # without hitting a short-circuit exit above, the extraction was
    # a success.  return details from extraction to reflect upstream
    current_app.logger.info(
        f"$extract produced {len(extracted.get('entry', []))} entries; "
        f"upstream POST {upstream_post_success} "
        f"app_FHIR POST {app_post_success} ")
    return dict(response={"status": "200 OK", "bundle": extracted})
