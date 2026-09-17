"""Manage mapping of Patient identifiers between multiple FHIR servers"""
from flask import current_app

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
def flask_g():
    from flask import g
    return g
def upstream_fhir_url():
    return current_app.config.get('UPSTREAM_FHIR_URL')
def upstream_mrn_system():
    return current_app.config.get('UPSTREAM_MRN_SYSTEM')


def extract_identifier_value(identifiers, system):
    for ident in identifiers:
        if ident.get("system") == system:
            return ident["value"]


def store_identifier_value(identifiers, system, value):
    for ident in identifiers:
        if ident.get("system") == system:
            ident["value"] = value
            return identifiers
    identifiers.append({"system": system, "value": value})
    return identifiers


def lookup_identified_patient(patient_id):
    """Given an APP_FHIR patient_id, return the corresponding Patient
    identifier from the UPSTREAM_FHIR server

    NB this function populates the single request global `g` with the
    `patient_wpr` once the patient linkage is confirmed.
    """
    global PATIENT_MAP
    if patient_id in PATIENT_MAP:
        flask_g()["patient_wpr"] = PATIENT_MAP[patient_id][1]
        return PATIENT_MAP[patient_id]

    def cache_upstream_result(source_patient, upstream_patient_id):
        """Store in local cache, persist UPSTREAM identifiers in APP FHIR server

        :param source_patient: Patient with identifiers (could be APP, as in previously cached,
          or UPSTREAM)
        :param upstream_patient_id: patient primary id on the UPSTREAM_FHIR server

        :returns matching PATIENT_MAP tuple, after storing values
        """
        app_patient_dirty = False
        known_upstream_id = extract_identifier_value(
            app_patient["identifier"],
            upstream_fhir_url())
        known_epic_wpr = extract_identifier_value(app_patient["identifier"], epic_wpr_system())
        epic_wpr = extract_identifier_value(source_patient["identifier"], epic_wpr_system())
        if known_upstream_id != upstream_patient_id:
            app_patient_dirty = True
            app_patient["identifier"] = store_identifier_value(
                identifiers=app_patient["identifier"],
                system=upstream_fhir_url(),
                value=upstream_patient_id)
        if known_epic_wpr != epic_wpr:
            app_patient_dirty = True
            app_patient["identifier"] = store_identifier_value(
                identifiers=app_patient["identifier"],
                system=epic_wpr_system(),
                value=epic_wpr)
        if app_patient_dirty:
            # persist app patient w/ cached upstream identifiers
            request_resource_app_fhir(http_verb="put", resource=app_patient)

        PATIENT_MAP[app_patient['id']] = (upstream_patient_id, epic_wpr)
        flask_g()["patient_wpr"] = epic_wpr
        return PATIENT_MAP[patient_id]

    patient_query = {"resourceType": "Patient", "id": patient_id}
    app_patient = request_resource_app_fhir("get", patient_query)
    assert app_patient["resourceType"] == "Patient"
    app_mrn = extract_identifier_value(app_patient["identifier"], app_mrn_system())

    if not app_mrn:
        msg = f"APP Patient({patient_id}) does not have an MRN identifier; can't continue"
        current_app.logger.warning(msg)
        raise ValueError(msg)

    upstream_pid = extract_identifier_value(app_patient["identifier"], upstream_fhir_url())
    if upstream_pid:
        # Add to local cache and return, given upstream identifiers are already known
        return cache_upstream_result(
            source_patient=app_patient,
            upstream_patient_id=upstream_pid)

    upstream_patient_query = {
        "resourceType": "Patient",
        "identifier": [{"system": upstream_mrn_system(), "value": app_mrn}]
    }

    # search on identifier returns a bundle
    bundle = request_resource_upstream("get", upstream_patient_query)
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

    return cache_upstream_result(
        source_patient=match,
        upstream_patient_id=match['id'])


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
