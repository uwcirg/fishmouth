import copy

VALID_QR = {
    "resourceType": "QuestionnaireResponse",
    "id": "example-1",
    "status": "completed",
    "questionnaire": "Questionnaire/example",
    "item": [
        {
            "linkId": "1",
            "answer": [
                {"valueString": "test answer"}
            ]
        }
    ]
}

VALID_QR_ONLY_ID = VALID_QR.copy()
for unwanted in ("status", "questionnaire", "item"):
    VALID_QR_ONLY_ID.pop(unwanted)

SUBSCRIPTION_NOTIFICATION = {
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
                "id": VALID_QR["id"],
            }
        }
    ]
}

MOCK_EXTRACT_RESPONSE = {
    "resourceType": "Bundle",
    "type": "collection",
    "entry": [
        {
            "resource": {
                "resourceType": "Observation",
                "status": "final"
            }
        }
    ]
}

MOCK_POST_RESPONSE ={
  "resourceType": "Bundle",
  "type": "transaction-response",
  "entry": [
    {
        "response": {
        "status": "200 OK",
        },
    },
    {
      "response": {
        "status": "200 OK",
      }
    }
  ]
}

def test_event_success(client, mocker):
    """Confirm valid submission calls expected functions """

    mock_extract = mocker.patch(
        "app.services.process_resource.extract_resource",
        return_value=MOCK_EXTRACT_RESPONSE
    )
    mock_upstream_post = mocker.patch(
        "app.services.process_resource.post_resource_upstream",
        return_value=MOCK_POST_RESPONSE
    )

    resp = client.post("/extract-n-post", json=SUBSCRIPTION_NOTIFICATION)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data == MOCK_POST_RESPONSE

    # Ensure extract was called with payload
    mock_extract.assert_called_once_with(VALID_QR_ONLY_ID)


def test_event_invalid_content_type(client):
    resp = client.post("/extract-n-post", data="not json")

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Expected JSON"


def test_event_missing_resource_type(client):
    resp = client.post("/extract-n-post", json={})

    assert resp.status_code == 400
    assert "Invalid JSON" in resp.get_json()["error"]


def test_event_unsupported_resource_type(client):
    with_unsupported = copy.deepcopy(SUBSCRIPTION_NOTIFICATION)
    with_unsupported['entry'][1] = dict(resource={"resourceType": "Patient"})
    resp = client.post("/extract-n-post", json=with_unsupported)

    assert resp.status_code == 200
    # expect 2nd entry to include error details (1st is SubscriptionStatus entry)
    assert resp.json["entry"][1]["response"]["status"] == "501 Not Implemented"


def test_event_extract_failure(client, mocker):
    """
    Simulate downstream extract failure
    """

    mocker.patch(
        "app.services.process_resource.extract_resource",
        side_effect=Exception("boom")
    )

    resp = client.post("/extract-n-post", json=SUBSCRIPTION_NOTIFICATION)

    # The response should reflect the error and contain error details for the entry
    assert resp.status_code == 422

    data = resp.get_json()
    # should see two response entries.
    # - first for SubscriptionStatus (valid)
    # - second for QuestionnaireResponse (mocked exception)
    assert len(data['entry']) == 2
    assert data['entry'][0]['response']['status'] == '200 OK'
    assert data['entry'][1]['response']['status'] == '422 Unprocessable Entity'
    assert data['entry'][1]['response']['outcome']['issue'][0]['details']['text'].startswith(
        "FHIR $extract failed: boom")



def test_extract_http_layer(client, mocker):
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = MOCK_EXTRACT_RESPONSE
    mock_resp.raise_for_status.return_value = None

    mock_post = mocker.patch(
        "app.services.fhir_client.requests.post",
        return_value=mock_resp
    )

    resp = client.post("/extract-n-post", json=SUBSCRIPTION_NOTIFICATION)

    assert resp.status_code == 200
    assert mock_post.call_count == 2
