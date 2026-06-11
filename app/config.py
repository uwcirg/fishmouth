import os
import json

class Config:
    APP_FHIR_URL = os.getenv("APP_FHIR_URL", "http://localhost:8080/fhir")
    APP_FHIR_TIMEOUT = int(os.getenv("APP_FHIR_TIMEOUT", "10"))
    APP_MRN_SYSTEM = os.getenv("APP_MRN_SYSTEM")

    EXTRACTED_RESOURCES_PERSISTED_IN_APP_FHIR = json.loads(
        os.getenv("EXTRACTED_RESOURCES_PERSISTED_IN_APP_FHIR", "[]"))

    UPSTREAM_FHIR_URL = os.getenv("UPSTREAM_FHIR_URL", "http://localhost:8080/fhir")
    UPSTREAM_FHIR_TIMEOUT = int(os.getenv("UPSTREAM_FHIR_TIMEOUT", "10"))
    UPSTREAM_FHIR_USER = os.getenv("UPSTREAM_FHIR_USER")
    UPSTREAM_FHIR_PASSWORD = os.getenv("UPSTREAM_FHIR_PASSWORD")
    UPSTREAM_MRN_SYSTEM = os.getenv("UPSTREAM_MRN_SYSTEM")
