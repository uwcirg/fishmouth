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

    app_call_response = mocker.Mock()
    app_call_response.json.return_value = APP_PATIENT
    launch_call_response = mocker.Mock()
    launch_call_response.json.return_value = {
        "resourceType": "Bundle",
        "total": 1,
        "entry": [ dict(resource=UPSTREAM_PATIENT) ]
    }
    requests_mock = mocker.patch("app.services.map_resource.requests.get")
    requests_mock.side_effect = [app_call_response, launch_call_response]
    mapped_id = lookup_identified_patient(APP_PATIENT["id"])
    assert mapped_id == UPSTREAM_PATIENT["id"]
