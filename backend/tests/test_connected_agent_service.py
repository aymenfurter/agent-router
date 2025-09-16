import json
from types import SimpleNamespace

import pytest

from backend.services.connected_agent_service import ConnectedAgentService


class StubAgent:
    def __init__(self, agent_id):
        self.id = agent_id


class RecordingProjectClient:
    def __init__(self):
        self.deleted_agents = []
        self.vector_stores_deleted = []
        self.files_deleted = []
        self.messages_created = []
        self.message_list = []
        self.thread_to_return = SimpleNamespace(id="thread-1")

        class Threads:
            def __init__(self, outer):
                self.outer = outer

            def get(self, thread_id):
                if thread_id == "existing":
                    return SimpleNamespace(id=thread_id)
                raise RuntimeError("missing thread")

            def create(self):
                return self.outer.thread_to_return

        class Messages:
            def __init__(self, outer):
                self.outer = outer

            def create(self, **kwargs):
                self.outer.messages_created.append(kwargs)

            def list(self, thread_id):
                return list(self.outer.message_list)

        class Runs:
            def __init__(self, outer):
                self.outer = outer
                self.created_runs = []
                self.get_responses = []
                self.submitted = []

            def create(self, **kwargs):
                run = SimpleNamespace(id="run-created", status="queued")
                self.created_runs.append(kwargs)
                return run

            def get(self, thread_id, run_id):
                return self.get_responses.pop(0)

            def submit_tool_outputs(self, **kwargs):
                self.submitted.append(kwargs)

        class RunSteps:
            def __init__(self, outer):
                self.outer = outer
                self.steps = []

            def list(self, thread_id, run_id):
                return list(self.steps)

        class Agents:
            def __init__(self, outer):
                self.outer = outer
                self.threads = Threads(outer)
                self.messages = Messages(outer)
                self.runs = Runs(outer)
                self.run_steps = RunSteps(outer)

            def delete_agent(self, agent_id):
                self.outer.deleted_agents.append(agent_id)

            class VectorStores:
                def __init__(self, outer):
                    self.outer = outer

                def delete(self, vector_store_id):
                    self.outer.vector_stores_deleted.append(vector_store_id)

            class Files:
                def __init__(self, outer):
                    self.outer = outer

                def delete(self, file_id):
                    self.outer.files_deleted.append(file_id)

        agents = Agents(self)
        agents.vector_stores = agents.VectorStores(self)
        agents.files = agents.Files(self)
        self.agents = agents


@pytest.fixture
def service():
    return ConnectedAgentService()


def test_initialize_creates_agents(monkeypatch, service):
    created_agents = {}

    class DummyAIProjectClient:
        def __init__(self, endpoint, credential):
            self.endpoint = endpoint
            self.credential = credential

    class DummyAgentFactory:
        def __init__(self, project_client):
            assert isinstance(project_client, DummyAIProjectClient)

        def create_fabric_agent(self):
            return StubAgent("fabric-1")

        def create_web_agent(self):
            return StubAgent("web-1")

        def create_rag_agent(self):
            return StubAgent("rag-1"), {"vector_store": StubAgent("vs-1"), "file": StubAgent("file-1")}

        def create_routing_agent(self, connected_agents, search_fn, genie_fn):
            created_agents["connected"] = dict(connected_agents)
            return StubAgent("main-1")

    class DummyMessageProcessor:
        def __init__(self, project_client):
            self.project_client = project_client

    monkeypatch.setattr("backend.services.connected_agent_service.AIProjectClient", DummyAIProjectClient)
    monkeypatch.setattr("backend.services.connected_agent_service.DefaultAzureCredential", lambda: "creds")
    monkeypatch.setattr("backend.services.connected_agent_service.AgentFactory", DummyAgentFactory)
    monkeypatch.setattr("backend.services.connected_agent_service.MessageProcessor", DummyMessageProcessor)

    assert service.initialize() is True
    assert service._initialized is True
    assert list(service.connected_agents.keys()) == ["fabric_agent", "web_agent", "rag_agent"]
    assert service.main_agent.id == "main-1"
    assert "rag_agent" in created_agents["connected"]


def test_initialize_short_circuits_when_already_initialized(monkeypatch, service):
    service._initialized = True

    def fail_ai_client(*args, **kwargs):
        raise AssertionError("should not be called")

    monkeypatch.setattr("backend.services.connected_agent_service.AIProjectClient", fail_ai_client)

    assert service.initialize() is True


def test_analyze_purview_varies_with_results(service):
    service._search_catalog = lambda query: json.dumps({
        "assets_found": 1,
        "results": [{"connected_agent": "genie"}]
    })
    success = service.analyze_purview("sales")
    assert success["success"] is True
    assert "Primary agent" in success["purview"]
    assert success["confidence"] == 0.8

    service._search_catalog = lambda query: json.dumps({"assets_found": 0, "results": []})
    no_assets = service.analyze_purview("weather")
    assert "No relevant data assets" in no_assets["purview"]
    assert no_assets["confidence"] == 0.3


def prepare_service_with_project_client(service):
    project_client = RecordingProjectClient()
    service.project_client = project_client
    service._initialized = True
    service.message_processor = SimpleNamespace(
        extract_message_with_annotations=lambda message: {"content": "assistant reply", "annotations": ["note"]},
        format_thread_messages=lambda messages, thread_id: [
            {"id": message.id, "role": message.role, "content": "assistant reply", "annotations": [],
             "created_at": message.created_at, "thread_id": thread_id}
            for message in reversed(messages)
        ],
    )
    return project_client


def test_process_query_direct_unknown_agent(service):
    service._initialized = True
    result = service.process_query_direct("hello", "missing")
    assert result["success"] is False
    assert "Unknown agent" in result["error"]


def test_process_query_direct_succeeds(monkeypatch, service):
    project_client = prepare_service_with_project_client(service)
    service.connected_agents = {"web_agent": StubAgent("web-1")}

    def fake_get_or_create(thread_id=None):
        return SimpleNamespace(id="thread-1")

    def fake_execute_agent_run(thread_id, agent_id):
        return SimpleNamespace(id="run-1", status="completed")

    def fake_extract_response(thread_id):
        return "final response", ["note"]

    service._get_or_create_thread = fake_get_or_create
    service._execute_agent_run = fake_execute_agent_run
    service._extract_response_from_thread = fake_extract_response

    result = service.process_query_direct("hi", "web_agent")
    assert result["metadata"]["agent_used"] == "web_agent"
    assert result["response"] == "final response"
    assert project_client.messages_created[0]["content"] == "hi"


def test_process_query_combines_tool_details(service):
    project_client = prepare_service_with_project_client(service)

    service._get_or_create_thread = lambda thread_id=None: SimpleNamespace(id="thread-2")
    service._execute_routing_run = lambda thread_id: (
        SimpleNamespace(id="run-2", status="completed"), ["tool_a"]
    )
    service._extract_response_from_thread = lambda thread_id: ("answer", [])
    service._extract_run_details = lambda thread_id, run_id: (["rag_agent"], ["tool_b"])

    result = service.process_query("find data")
    metadata = result["metadata"]
    assert metadata["tools_called"] == ["tool_a", "tool_b"]
    assert metadata["connected_agents_called"] == ["rag_agent"]
    assert project_client.messages_created[0]["role"] == "user"


def test_get_thread_messages_returns_formatted(service):
    project_client = prepare_service_with_project_client(service)
    project_client.message_list = [SimpleNamespace(id="msg", role="assistant", created_at=1)]

    result = service.get_thread_messages("thread-1")
    assert result["message_count"] == 1
    assert result["messages"][0]["thread_id"] == "thread-1"


def test_get_health_status(service):
    health = service.get_health_status()
    assert health["service"] == "Connected Agent Service"
    assert health["initialized"] is False


def test_cleanup_removes_resources(service):
    project_client = RecordingProjectClient()
    service.project_client = project_client
    service.main_agent = StubAgent("main")
    service.connected_agents = {"web": StubAgent("web-id")}
    service.cleanup_resources = {"vector_store": StubAgent("vs"), "file": StubAgent("file")}

    service.cleanup()

    assert project_client.deleted_agents == ["main", "web-id"]
    assert project_client.vector_stores_deleted == ["vs"]
    assert project_client.files_deleted == ["file"]


def test_extract_response_from_thread_picks_first_assistant(service):
    project_client = prepare_service_with_project_client(service)
    service.project_client.message_list = [
        SimpleNamespace(role="user"),
        SimpleNamespace(role="assistant", content=[SimpleNamespace(text=SimpleNamespace(value="ignore"))]),
    ]

    response, annotations = service._extract_response_from_thread("thread-1")
    assert response == "assistant reply"
    assert annotations == ["note"]


def test_extract_response_from_thread_handles_missing(service):
    project_client = prepare_service_with_project_client(service)
    service.project_client.message_list = [SimpleNamespace(role="user")]

    response, annotations = service._extract_response_from_thread("thread-1")
    assert response == "No response generated"
    assert annotations == []


def test_extract_run_details_collects_tools(service):
    project_client = prepare_service_with_project_client(service)

    connected_call = SimpleNamespace(
        type="connected_agent",
        connected_agent={"name": "rag_agent"},
    )
    function_call = SimpleNamespace(
        type="function",
        function=SimpleNamespace(name="handoff_genie_agent"),
    )
    search_call = SimpleNamespace(
        type="function",
        function=SimpleNamespace(name="_search_catalog"),
    )
    project_client.agents.run_steps.steps = [
        SimpleNamespace(step_details=SimpleNamespace(tool_calls=[connected_call, function_call, search_call]))
    ]

    connected, tools = service._extract_run_details("thread", "run")
    assert connected == ["rag_agent"]
    assert tools == ["handoff_genie_agent(...)"]


def test_get_or_create_thread_returns_existing(service):
    service.project_client = RecordingProjectClient()
    thread = service._get_or_create_thread("existing")
    assert thread.id == "existing"

    thread = service._get_or_create_thread("missing")
    assert thread.id == "thread-1"


def test_execute_agent_run_advances_until_complete(monkeypatch, service):
    service.project_client = RecordingProjectClient()
    responses = [SimpleNamespace(id="run-created", status="in_progress"), SimpleNamespace(id="run-created", status="completed")]
    service.project_client.agents.runs.get_responses = responses
    monkeypatch.setattr("backend.services.connected_agent_service.time.sleep", lambda _: None)

    run = service._execute_agent_run("thread-1", "agent-1")
    assert run.status == "completed"


def test_execute_routing_run_handles_tool_calls(monkeypatch, service):
    service.project_client = RecordingProjectClient()
    service.main_agent = StubAgent("main-1")
    service._search_catalog = lambda query: json.dumps({"assets_found": 0})
    monkeypatch.setattr(
        "backend.services.connected_agent_service.genie_agent_service",
        SimpleNamespace(handoff_genie_agent=lambda query: json.dumps({"status": "success"}))
    )
    monkeypatch.setattr("backend.services.connected_agent_service.time.sleep", lambda _: None)

    tool_calls = [
        SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(name="_search_catalog", arguments=json.dumps({"query": "catalog"}))
        ),
        SimpleNamespace(
            id="call-2",
            function=SimpleNamespace(name="handoff_genie_agent", arguments=json.dumps({"query": "sales"}))
        ),
    ]
    required_action = SimpleNamespace(submit_tool_outputs=SimpleNamespace(tool_calls=tool_calls))
    responses = [
        SimpleNamespace(id="run-created", status="requires_action", required_action=required_action),
        SimpleNamespace(id="run-created", status="completed"),
    ]
    service.project_client.agents.runs.get_responses = responses

    run, tools = service._execute_routing_run("thread-1")
    assert run.status == "completed"
    assert tools == ["search_catalog('catalog')", "handoff_genie_agent('sales')"]
    submitted = service.project_client.agents.runs.submitted[0]
    assert submitted["thread_id"] == "thread-1"
    assert len(submitted["tool_outputs"]) == 2
