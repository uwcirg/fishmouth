import requests
from flask import current_app

def extract_resource(questionnaire_response: dict) -> dict:
    """
    Calls HAPI FHIR $extract operation.
    Assumes input is a QuestionnaireResponse.
    """

    base_url = current_app.config["HAPI_BASE_URL"]
    timeout = current_app.config["HAPI_TIMEOUT"]

    url = f"{base_url}/QuestionnaireResponse/$extract"

    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
    }

    payload = questionnaire_response

    resp = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=timeout,
    )

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        current_app.logger.error("FHIR extract failed: %s", resp.text)
        raise

    return resp.json()
