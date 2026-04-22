import os

class Config:
    HAPI_BASE_URL = os.getenv("HAPI_BASE_URL", "http://localhost:8080/fhir")
    HAPI_TIMEOUT = int(os.getenv("HAPI_TIMEOUT", "10"))
