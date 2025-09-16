import json
from types import SimpleNamespace

import pytest

from backend.services.catalog_service import CatalogService


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_parse_agent_from_description():
    service = CatalogService()
    assert service.parse_agent_from_description("Agent: Genie") == "Genie"
    assert service.parse_agent_from_description("no agent here") is None
    assert service.parse_agent_from_description(None) is None


def test_search_catalog_builds_results(monkeypatch):
    service = CatalogService()

    class DummyCredential:
        def get_token(self, scope):
            assert scope == "https://purview.azure.net/.default"
            return SimpleNamespace(token="token-value")

    def fake_post(url, json, headers):
        assert headers["Authorization"] == "Bearer token-value"
        payload = {
            "value": [
                {
                    "displayText": "Sales Report",
                    "userDescription": "Agent: rag_agent",
                    "id": "asset-1",
                    "contact": [{"id": "c53c736b-8469-409c-9dcc-b3a61953d4dd"}],
                },
                {
                    "displayText": "Marketing Data",
                    "userDescription": None,
                    "id": "asset-2",
                    "contact": [],
                },
            ]
        }
        return DummyResponse(payload)

    monkeypatch.setattr("backend.services.catalog_service.AzureCliCredential", DummyCredential)
    monkeypatch.setattr("backend.services.catalog_service.requests.post", fake_post)

    result = service.search_catalog("sales")

    assert result["status"] == "success"
    assert result["assets_found"] == 2
    assets = {asset["name"]: asset for asset in result["results"]}
    assert assets["Sales Report"]["connected_agent"] == "rag_agent"
    # Contact id is mapped through the contacts dictionary
    assert assets["Sales Report"]["contact"] == "Aymen Furter (aymen.furter@microsoft.com)"
    assert assets["Marketing Data"]["contact"] is None
