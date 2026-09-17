from app.services.map_resource import lookup_identified_patient

APP_PATIENT = {
  "resourceType": "Patient",
  "id": "example-patient-1",
  "identifier": [
    {
      "use": "official",
      "type": {
        "text": "Medical Record Number"
      },
      "system": "http://hospital.org/mrn",
      "value": "MRN-001"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Doe",
      "given": ["John", "D"]
    }
  ],
  "gender": "male",
  "birthDate": "1980-01-01"
}

UPSTREAM_PATIENT = {
  "resourceType": "Patient",
  "id": "example-patient-2",
  "identifier": [
    {
      "use": "official",
      "type": {
        "text": "Medical Record Number"
      },
      "system": "http://other.hospital.example.org/mrn",
      "value": "MRN-001"
    }
  ],
  "name": [
    {
      "use": "official",
      "family": "Doe",
      "given": ["John", "D"]
    }
  ],
  "gender": "male",
  "birthDate": "1980-01-01"
}


def test_lookup_patient(mocker):
    mocker.patch("app.services.map_resource.app_fhir_url", return_value="http://example.org")
    mocker.patch("app.services.map_resource.app_mrn_system", return_value="http://hospital.org/mrn")
    mocker.patch("app.services.map_resource.upstream_fhir_url", return_value="http://other.example.org")
    mocker.patch("app.services.map_resource.upstream_mrn_system", return_value="http://other.hospital.org/mrn")
    mocker.patch("app.services.map_resource.epic_wpr_system", return_value="0.1.1.0")
    mocker.patch("app.services.map_resource.flask_g", return_value=dict())

    # return APP_PATIENT from app_fhir resource lookup
    mocker.patch("app.services.map_resource.request_resource_app_fhir", return_value=APP_PATIENT)

    # return bundle containing UPSTREAM_PATIENT from upstream resource lookup
    launch_call_response  = {
        "resourceType": "Bundle",
        "entry": [ dict(resource=UPSTREAM_PATIENT) ]
    }
    mocker.patch("app.services.map_resource.request_resource_upstream", return_value=launch_call_response)
    mapped_id, _ = lookup_identified_patient(APP_PATIENT["id"])
    assert mapped_id == UPSTREAM_PATIENT["id"]
