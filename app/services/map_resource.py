"""Manage mapping of Patient identifiers between multiple FHIR servers"""
from flask import current_app
import requests


PATIENT_MAP = {}

def app_fhir_url():
    return current_app.config.get('APP_FHIR_URL')
def app_mrn_system():
    return current_app.config.get('APP_MRN_SYSTEM')
def upstream_fhir_url():
    return current_app.config.get('UPSTREAM_FHIR_URL')
def upstream_mrn_system():
    return current_app.config.get('UPSTREAM_MRN_SYSTEM')


def lookup_identified_patient(patient_id):
    """Given an APP_FHIR patient_id, return the corresponding Patient
    identifier from the UPSTREAM_FHIR server
    """
    if patient_id in PATIENT_MAP:
        return PATIENT_MAP[patient_id]

    request_url = f"{app_fhir_url()}/Patient/{patient_id}"
    response = requests.get(request_url)
    response.raise_for_status()
    app_patient = response.json()
    assert app_patient["resourceType"] == "Patient"
    app_mrn = None
    for ident in app_patient["identifier"]:
        if ident.get("system") == app_mrn_system():
            app_mrn = ident["value"]
            break

    if not app_mrn:
        msg = f"APP Patient({patient_id}) does not have an MRN identifier"
        current_app.logger.warning(msg)
        raise ValueError(msg)

    request_url = f"{upstream_fhir_url()}/Patient"
    params = {"identifier": f"{upstream_mrn_system()}|{app_mrn}"}
    response = requests.get(request_url, params=params)
    response.raise_for_status()
    # search returns a bundle - contents of exactly 1 indicates a match
    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    if bundle["total"] == 0:
        current_app.logger.warning(f"No match for Patient identifier {app_mrn} found on UPSTREAM_FHIR server")
        raise ValueError("Can't find matching Patient on UPSTREAM_FHIR server")
    if bundle['total'] > 1:
        # NB: writing to error log but simply returning first in case of multiple matches
        current_app.logger.warning(
            f"multiple patient matches for MRN {app_mrn} ; guessing first!")
    match = bundle['entry'][0]['resource']
    assert match['resourceType'] == 'Patient'
    # store in local cache
    PATIENT_MAP[patient_id] = match['id']
    return match['id']


def map_patient_references(resource):
    """Map the contained references between FHIR servers

    Given a resource with references to a Patient on the APP_FHIR server,
    lookup the matching UPSTREAM_FHIR server Patient with matching identifiers
    and replace all contained Patient references with their corresponding
    UPSTREAM_FHIR identifiers.

    """
    subject_id = None
    subject_reference = resource.get("subject", "")
    if subject_reference.startswith("Patient"):
        subject_id = subject_reference[len("Patient")+1:]

    if not subject_id:
        current_app.logger.warning(f"Patient reference not found in resource {resource}")
        return resource

    mapped_id = lookup_identified_patient(patient_id=subject_id)
    mapped_resource = resource.copy()
    mapped_resource.update({"subject": f"Patient/{mapped_id}"})
    return mapped_resource
