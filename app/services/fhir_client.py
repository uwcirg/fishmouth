import os

import requests
from requests.auth import HTTPBasicAuth
from flask import current_app, g


def extract_resource(resource: dict) -> dict:
    """ POST resource to APP FHIR $extract operation.

    :return: server response.json
    """
    base_url = current_app.config["APP_FHIR_URL"]
    timeout = current_app.config["APP_FHIR_TIMEOUT"]
    resource_type = resource["resourceType"]
    id = resource.get("id", "")
    url = f"{base_url}/{resource_type}/{id}/$extract"
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
    }
    resp = requests.post(
        url,
        json={"resourceType": "Parameters"},
        headers=headers,
        timeout=timeout,
    )

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        current_app.logger.error("FHIR extract failed: %s", resp.text)
        raise ValueError(resp.text)

    return resp.json()


def request_resource_upstream(http_verb: str, resource: dict) -> dict:
    """request resource(s) to/from UPSTREAM FHIR server

    Possible configuration requires secondary service call to app with search authorization.
    Depending on configuration, the endpoint may depend on `http_verb`.

    :return: server response.json
    """
    if http_verb.lower() == "get" or current_app.config["UPSTREAM_SEARCH_URL"] is None:
        base_url = current_app.config["UPSTREAM_FHIR_URL"]
        user = current_app.config["UPSTREAM_FHIR_USER"]
        password = current_app.config["UPSTREAM_FHIR_PASSWORD"]
    else:
        base_url = current_app.config["UPSTREAM_SEARCH_URL"]
        user, password = None, None
    timeout = current_app.config["UPSTREAM_FHIR_TIMEOUT"]
    headers = {}
    # Use definition of EPIC_CLIENT_ID as switch for adding additional
    # Epic specific headers
    epic_client_id = os.getenv("EPIC_CLIENT_ID")
    if epic_client_id:
        headers["Epic-Client-ID"] = epic_client_id
        headers["Epic-MyChartUser-IDType"] = "External"
        # The single request global `g` will contain the patient_wpr only after successful
        # APP:UPSTREAM patient linkage.  See map_resource.lookup_identified_patient()
        if g.get("patient_wpr"):
            headers["Epic-MyChartUser-ID"] = g.get("patient_wpr")

    return request_resource(
        http_verb=http_verb,
        resource=resource,
        headers=headers,
        base_url=base_url,
        timeout=timeout,
        user=user,
        password=password)


def request_resource_app_fhir(http_verb: str, resource: dict) -> dict:
    """request resource(s) to/from APP FHIR server

    :return: server response.json
    """
    base_url = current_app.config["APP_FHIR_URL"]
    timeout = current_app.config["APP_FHIR_TIMEOUT"]
    return request_resource(
        http_verb=http_verb,
        resource=resource,
        headers={},
        base_url=base_url,
        timeout=timeout,
        user=None,
        password=None)


def request_resource(
        http_verb: str,
        resource: dict,
        headers: dict,
        base_url: str,
        timeout: int,
        user: str | None,
        password: str | None) -> dict:
    resource_type = resource["resourceType"]
    url = f"{base_url}"
    params = None
    if resource_type != "Bundle":
        url = f"{base_url}/{resource_type}"
        if resource.get("id"):
            url += f"/{resource['id']}"
        if resource.get("identifier"):
            params = {
                "identifier": '|'.join((
                    resource['identifier'][0]["system"],
                    resource['identifier'][0]["value"]
                ))
            }
    if "Content-Type" not in headers:
        headers["Content-Type"] = "application/fhir+json"
    if "Accept" not in headers:
        headers["Accept"] = "application/fhir+json"
    basic_auth = None
    if user and password:
        basic_auth = HTTPBasicAuth(user, password)
    request_func = getattr(requests, http_verb.lower())
    resp = request_func(
        url,
        auth=basic_auth,
        params=params,
        json=resource,
        headers=headers,
        timeout=timeout,
    )

    try:
        resp.raise_for_status()
    except requests.HTTPError:
        current_app.logger.error(f"FHIR POST to {url} failed: {resp.text}")
        raise

    current_app.logger.info(f"FHIR POST to {url} succeeded: {resp.json()}")
    return resp.json()
