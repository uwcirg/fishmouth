from copy import deepcopy

from app.services.map_resource import map_patient_references
from app.services.process_resource import (
    patch_observation_vital_signs,
    update_identifier,
)

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
  },
  "performer": [
    {
      "reference": "Patient/example",
    }
  ],
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


def test_update_references(mocker):
    mocker.patch(
        "app.services.map_resource.lookup_identified_patient",
        return_value=("mapped", None)
    )
    obs = map_patient_references(OBSERVATION)
    assert obs != OBSERVATION
    assert obs["subject"] == {"reference": "Patient/mapped"}
    assert obs["performer"] == [{"reference": "Patient/mapped"}]

def test_observation_add_vitals():
    improved = patch_observation_vital_signs(OBSERVATION)
    assert improved["category"] == [
        {"coding": [
            {"system": "http://hl7.org/fhir/observation-category", "code": "vital-signs"}]
        }
    ]


def test_observation_already_present_vitals():
    with_vitals = patch_observation_vital_signs(OBSERVATION)
    # second call shouldn't add again..
    improved = patch_observation_vital_signs(with_vitals)
    assert improved["category"] == [
        {"coding": [
            {"system": "http://hl7.org/fhir/observation-category", "code": "vital-signs"}]
        }
    ]

