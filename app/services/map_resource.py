"""Manage mapping of Patient identifiers between multiple FHIR servers"""
from flask import current_app
import requests

from .fhir_client import request_resource_app_fhir, request_resource_upstream

# Module level global, caches looked up patient values between systems
# Keyed by the APP_FHIR Patient.id, maps to tuple values:
#   ( <UPSTREAM_FHIR Patient.id>, <UPSTREAM_FHIR WPR identifier value> )
PATIENT_MAP = {}

def app_fhir_url():
    return current_app.config.get('APP_FHIR_URL')
def app_mrn_system():
    return current_app.config.get('APP_MRN_SYSTEM')
def epic_wpr_system():
    return current_app.config.get('EPIC_WPR_SYSTEM')
def upstream_fhir_url():
    return current_app.config.get('UPSTREAM_FHIR_URL')
def upstream_mrn_system():
    return current_app.config.get('UPSTREAM_MRN_SYSTEM')


def extract_identifier_value(identifiers, system):
    for ident in identifiers:
        if ident.get("system") == system:
            return ident["value"]


def lookup_identified_patient(patient_id):
    """Given an APP_FHIR patient_id, return the corresponding Patient
    identifier from the UPSTREAM_FHIR server
    """
    global PATIENT_MAP
    if patient_id in PATIENT_MAP:
        return PATIENT_MAP[patient_id]

    patient = {"resourceType": "Patient", "id": patient_id}
    app_patient = request_resource_app_fhir("get", patient)
    assert app_patient["resourceType"] == "Patient"
    app_mrn = extract_identifier_value(app_patient["identifier"], app_mrn_system())

    if not app_mrn:
        msg = f"APP Patient({patient_id}) does not have an MRN identifier"
        current_app.logger.warning(msg)
        raise ValueError(msg)

    upstream_patient = {
        "resourceType": "Patient",
        "identifier": [{"system": upstream_mrn_system(), "value": app_mrn}]
    }
    # search returns a bundle - contents of exactly 1 indicates a match
    bundle = request_resource_upstream("get", upstream_patient)
    assert bundle["resourceType"] == "Bundle"
    total = bundle.get("total") or len(bundle["entry"])
    if total == 0:
        current_app.logger.warning(f"No match for Patient identifier {app_mrn} found on UPSTREAM_FHIR server")
        raise ValueError("Can't find matching Patient on UPSTREAM_FHIR server")
    if total > 1:
        # NB: writing to error log but simply returning first in case of multiple matches
        current_app.logger.warning(
            f"multiple patient matches for MRN {app_mrn} ; guessing first!")
    match = bundle['entry'][0]['resource']
    assert match['resourceType'] == 'Patient'
    # store in local cache
    epic_wpr = extract_identifier_value(match["identifier"], epic_wpr_system())
    PATIENT_MAP[patient_id] = (match['id'], epic_wpr)
    return PATIENT_MAP[patient_id]


def map_patient_references(resource):
    """Map the contained references between FHIR servers

    Given a resource with references to a Patient on the APP_FHIR server,
    lookup the matching UPSTREAM_FHIR server Patient with matching identifiers
    and replace all contained Patient references with their corresponding
    UPSTREAM_FHIR identifiers.

    """
    subject_id = None
    subject_reference = resource.get("subject", {}).get("reference", "")
    if subject_reference.startswith("Patient"):
        subject_id = subject_reference[len("Patient")+1:]

    if not subject_id:
        current_app.logger.warning(f"Patient reference not found in resource {resource}")
        return resource

    mapped_id, _ = lookup_identified_patient(patient_id=subject_id)
    mapped_resource = resource.copy()
    mapped_resource.update({"subject": f"Patient/{mapped_id}"})
    return mapped_resource
