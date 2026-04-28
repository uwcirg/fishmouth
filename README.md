# fishmouth

Lightweight service with single intent: to receive restful API calls
from FHIR subscriptions or external applications.

POSTs to /event shall include a FHIR resource as content-type `application+fhir`
The contained resource will be passed to the configured APP_FHIR_URL `$extract` process,
and the resulting bundle will inturn get POSTed to the UPSTREAM_FHIR_URL

## Tests
This project uses `py.test` to manage testing. To trigger a test run, invoke `py.test` without arguments:

    py.test

## License
BSD
