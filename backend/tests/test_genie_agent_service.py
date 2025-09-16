import json
from types import SimpleNamespace

import pytest

from backend.services.genie_agent_service import GenieAgentService


class DummyResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("request failed")

    def json(self):
        return self._payload


@pytest.fixture
def configured_service():
    service = GenieAgentService()
    service.databricks_instance = "test.cloud"
    service.genie_space_id = "space"
    service.auth_token = "token"
    return service


def test_handoff_genie_agent_missing_configuration():
    service = GenieAgentService()
    service.databricks_instance = None
    response = json.loads(service.handoff_genie_agent("query"))
    assert response["status"] == "error"
    assert "Missing Genie configuration" in response["message"]


def test_handoff_genie_agent_success(monkeypatch, configured_service):
    post_called = False
    status_calls = {"count": 0}

    def fake_post(url, headers, json):
        nonlocal post_called
        post_called = True
        assert json == {"content": "give me data"}
        return DummyResponse({
            "conversation": {"id": "conv-1"},
            "message": {"id": "msg-1"},
        })

    def fake_get(url, headers):
        if "query-result" in url:
            return DummyResponse({
                "statement_response": {
                    "result": {
                        "data_array": [["a", 1], ["b", 2]],
                        "schema": {"columns": [{"name": "col1"}, {"name": "col2"}]},
                    }
                }
            })

        status_calls["count"] += 1
        if status_calls["count"] == 1:
            return DummyResponse({"status": "RUNNING"})
        return DummyResponse({
            "status": "COMPLETED",
            "attachments": [
                {
                    "text": {"content": "analysis"},
                    "query": {
                        "query": "SELECT * FROM table",
                        "description": "description",
                        "query_result_metadata": {"row_count": 12},
                    },
                    "attachment_id": "att-1",
                }
            ],
        })

    monkeypatch.setattr("backend.services.genie_agent_service.requests.post", fake_post)
    monkeypatch.setattr("backend.services.genie_agent_service.requests.get", fake_get)
    monkeypatch.setattr("backend.services.genie_agent_service.time.sleep", lambda _: None)

    payload = json.loads(configured_service.handoff_genie_agent("give me data"))

    assert post_called is True
    assert payload["status"] == "success"
    assert payload["response"].startswith("analysis")
    assert "col1" in payload["response"]
    assert payload["generated_query"] == "SELECT * FROM table"
    assert payload["row_count"] == 12


def test_handoff_genie_agent_non_completed_status(monkeypatch, configured_service):
    def fake_post(url, headers, json):
        return DummyResponse({
            "conversation": {"id": "conv-2"},
            "message": {"id": "msg-2"},
        })

    def fake_get(url, headers):
        return DummyResponse({"status": "FAILED"})

    monkeypatch.setattr("backend.services.genie_agent_service.requests.post", fake_post)
    monkeypatch.setattr("backend.services.genie_agent_service.requests.get", fake_get)
    monkeypatch.setattr("backend.services.genie_agent_service.time.sleep", lambda _: None)

    payload = json.loads(configured_service.handoff_genie_agent("failing"))
    assert payload["status"] == "error"
    assert "FAILED" in payload["message"]
