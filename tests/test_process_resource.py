from app.services.process_resource import update_identifier

OBSERVATION = {
  "resourceType": "Observation",
  "id": "observation-with-multiple-ids",
  "identifier": [
    {
      "use": "official",
      "system": "urn:oid:1.2.3.4.5",
      "value": "ACC-987654321",
      "type": {
        "coding": [
          {
            "system": "http://hl7.org",
            "code": "PLAC",
            "display": "Placer Identifier"
          }
        ]
      }
    },
    {
      "use": "secondary",
      "system": "http://hospital.org",
      "value": "LAB-123456",
      "type": {
        "coding": [
          {
            "system": "http://hl7.org",
            "code": "FILL",
            "display": "Filler Identifier"
          }
        ]
      }
    }
  ],
  "status": "final",
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "15074-8",
        "display": "Glucose [Moles/volume] in Blood"
      }
    ]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "valueQuantity": {
    "value": 5.5,
    "unit": "mmol/L",
    "system": "http://unitsofmeasure.org",
    "code": "mmol/L"
  }
}


def test_update_empty_identifiers():
    obs = OBSERVATION.copy()
    obs.pop("identifier")
    obs = update_identifier(obs, "system", "value")
    assert len(obs["identifier"]) == 1


def test_update_identifiers():
    obs = OBSERVATION.copy()
    obs = update_identifier(obs, "http://hospital.org", "new-value")
    assert len(obs["identifier"]) == len(OBSERVATION["identifier"])
    for id in obs["identifier"]:
        if id["system"] == "http://hospital.org":
            assert id["value"] == "new-value"
