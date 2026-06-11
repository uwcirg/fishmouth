import requests
from requests.auth import HTTPBasicAuth
from flask import current_app


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
        raise

    return resp.json()


def post_resource_upstream(resource: dict) -> dict:
    """POST resource(s) to UPSTREAM FHIR server

    :return: server response.json
    """
    base_url = current_app.config["UPSTREAM_FHIR_URL"]
    timeout = current_app.config["UPSTREAM_FHIR_TIMEOUT"]
    user = current_app.config["UPSTREAM_FHIR_USER"]
    password = current_app.config["UPSTREAM_FHIR_PASSWORD"]
    return post_resource(resource, base_url, timeout, user, password)


def post_resource_app_fhir(resource: dict) -> dict:
    """POST resource(s) to APP FHIR server

    :return: server response.json
    """
    base_url = current_app.config["APP_FHIR_URL"]
    timeout = current_app.config["APP_FHIR_TIMEOUT"]
    return post_resource(
        resource=resource,
        base_url=base_url,
        timeout=timeout,
        user=None,
        password=None)


def post_resource(
        resource: dict,
        base_url: str,
        timeout: int,
        user: str | None,
        password: str | None) -> dict:
    resource_type = resource["resourceType"]
    url = f"{base_url}"
    if resource_type != "Bundle":
        url = f"{base_url}/{resource_type}"
    headers = {
        "Content-Type": "application/fhir+json",
        "Accept": "application/fhir+json",
    }
    basic_auth = None
    if user and password:
        basic_auth = HTTPBasicAuth(user, password)
    resp = requests.post(
        url,
        auth=basic_auth,
        json=resource,
        headers=headers,
        timeout=timeout,
    )

    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        current_app.logger.error(f"FHIR POST to {url} failed: {resp.text}")
        raise

    current_app.logger.info(f"FHIR POST to {url} succeeded: {resp.json()}")
    return resp.json()


