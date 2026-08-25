import os
import json

class Config:
    APP_FHIR_URL = os.getenv("APP_FHIR_URL", "http://localhost:8080/fhir")
    APP_FHIR_TIMEOUT = int(os.getenv("APP_FHIR_TIMEOUT", "10"))
    APP_MRN_SYSTEM = os.getenv("APP_MRN_SYSTEM")

    DEBUG_DUMP_HEADERS = os.getenv("DEBUG_DUMP_HEADERS")
    DEBUG_DUMP_REQUEST = os.getenv("DEBUG_DUMP_REQUEST")

    EXTRACTED_RESOURCES_PERSISTED_IN_APP_FHIR = json.loads(
        os.getenv("EXTRACTED_RESOURCES_PERSISTED_IN_APP_FHIR", "[]"))

    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", 'http')

    # EPIC_CLIENT_ID is part of UPSTREAM, but distinct as a switch for
    # additional EPIC specific headers, when defined
    EPIC_CLIENT_ID = os.getenv("EPIC_CLIENT_ID")
    EPIC_WPR_SYSTEM = os.getenv("EPIC_WPR_SYSTEM", "urn:oid:1.2.840.114350.1.13.136.3.7.2.878082")

    UPSTREAM_FHIR_URL = os.getenv("UPSTREAM_FHIR_URL", "http://localhost:8080/fhir")
    UPSTREAM_FHIR_TIMEOUT = int(os.getenv("UPSTREAM_FHIR_TIMEOUT", "10"))
    UPSTREAM_FHIR_USER = os.getenv("UPSTREAM_FHIR_USER")
    UPSTREAM_FHIR_PASSWORD = os.getenv("UPSTREAM_FHIR_PASSWORD")
    UPSTREAM_MRN_SYSTEM = os.getenv("UPSTREAM_MRN_SYSTEM")

    # Install may use separate service for search vs write.
    UPSTREAM_SEARCH_URL = os.getenv("UPSTREAM_SEARCH_URL")
