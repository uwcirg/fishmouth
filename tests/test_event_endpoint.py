VALID_QR = {
    "resourceType": "QuestionnaireResponse",
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
        "status": "201 Created",
        "location": "Observation/123/_history/1",
        "lastModified": "2026-04-28T12:00:00Z"
      }
    }
  ]
}

def test_event_success(client, mocker):
    """
    Happy path:
    - valid QuestionnaireResponse
    - mock $extract returns Bundle
    """

    mock_extract = mocker.patch(
        "app.routes.extract_resource",
        return_value=MOCK_EXTRACT_RESPONSE
    )
    mock_upstream_post = mocker.patch(
        "app.routes.post_resource_upstream",
        return_value=MOCK_POST_RESPONSE
    )

    resp = client.post("/event", json=VALID_QR)

    assert resp.status_code == 200

    data = resp.get_json()
    assert data == MOCK_POST_RESPONSE

    # Ensure extract was called with payload
    mock_extract.assert_called_once_with(VALID_QR)


def test_event_invalid_content_type(client):
    resp = client.post("/event", data="not json")

    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Expected JSON"


def test_event_missing_resource_type(client):
    resp = client.post("/event", json={})

    assert resp.status_code == 400
    assert "resourceType" in resp.get_json()["error"]


def test_event_unsupported_resource_type(client):
    resp = client.post("/event", json={
        "resourceType": "Patient"
    })

    assert resp.status_code == 400
    assert "Unsupported" in resp.get_json()["error"]


def test_event_extract_failure(client, mocker):
    """
    Simulate downstream HAPI failure
    """

    mocker.patch(
        "app.routes.extract_resource",
        side_effect=Exception("boom")
    )

    resp = client.post("/event", json=VALID_QR)

    assert resp.status_code == 502

    data = resp.get_json()
    assert data["error"] == "FHIR extract failed"
    assert "boom" in data["details"]


def test_extract_http_layer(client, mocker):
    mock_resp = mocker.Mock()
    mock_resp.json.return_value = MOCK_EXTRACT_RESPONSE
    mock_resp.raise_for_status.return_value = None

    mock_post = mocker.patch(
        "app.services.fhir_client.requests.post",
        return_value=mock_resp
    )

    resp = client.post("/event", json=VALID_QR)

    assert resp.status_code == 200
    assert mock_post.call_count == 2
