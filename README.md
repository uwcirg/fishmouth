# fishmouth

Lightweight service with single intent: to receive restful API calls
from FHIR subscriptions or external applications.

POSTs to `/extract-n-post` shall include a FHIR resource Bundle of type
`subscription-notification` as content-type `application+fhir`.
The contained resource identifiers will be passed to the configured "APP_FHIR_URL" `$extract` process,
and the resulting bundle will inturn get be sent via `POST` to the "UPSTREAM_FHIR_URL"

## Subscription Notifications

Regardless of the flow (i.e. a direct RESTful call or as a registered
subscription event trigger), a FHIR `Bundle` resource of type
`subscription-notification` shall be POSTed to the `/extract-n-post` API.

      {
        "resourceType": "Bundle",
        "type": "subscription-notification",
        "entry": [
          {
            "resource": {
              "resourceType": "SubscriptionStatus",
              "status": "active",
              "type": "event-notification",
              "eventsSinceSubscriptionStart": 1,
              "subscription": {
                "reference": "Subscription/example"
              }
            }
          },
          {
            "resource": {
              "resourceType": "QuestionnaireResponse",
              "id": "qr-example-1",
            }
          }
        ]
      }


## Tests
This project uses `py.test` to manage testing. To trigger a test run, invoke `py.test` without arguments:

    py.test

## License
BSD
