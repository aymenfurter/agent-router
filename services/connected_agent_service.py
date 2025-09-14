import json
import time
from typing import Any, Dict

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from config.settings import settings
from services.agent_factory import AgentFactory
from services.catalog_service import catalog_service
from services.genie_agent_service import genie_agent_service
from services.message_processor import MessageProcessor
from utils.logging_config import get_logger


class ConnectedAgentService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.project_client = None
        self.main_agent = None
        self.connected_agents = {}
        self.cleanup_resources = {}
        self.agent_factory = None
        self.message_processor = None
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized:
            return True

        self.project_client = AIProjectClient(
            endpoint=settings.AZURE_AI_AGENT_ENDPOINT,
            credential=DefaultAzureCredential(),
        )

        self.agent_factory = AgentFactory(self.project_client)
        self.message_processor = MessageProcessor(self.project_client)

        self._create_all_agents()
        self._initialized = True
        return True

    def _create_all_agents(self):
        fabric_agent = self.agent_factory.create_fabric_agent()
        if fabric_agent:
            self.connected_agents["fabric_agent"] = fabric_agent

        self.connected_agents["web_agent"] = self.agent_factory.create_web_agent()

        rag_agent, cleanup_resources = self.agent_factory.create_rag_agent()
        self.connected_agents["rag_agent"] = rag_agent
        self.cleanup_resources = cleanup_resources

        self.main_agent = self.agent_factory.create_routing_agent(
            self.connected_agents,
            catalog_service.search_catalog,
            genie_agent_service.handoff_genie_agent,
        )

    def _search_catalog(self, query: str) -> str:
        return json.dumps(catalog_service.search_catalog(query))

    def _get_or_create_thread(self, thread_id: str = None):
        if thread_id:
            try:
                return self.project_client.agents.threads.get(thread_id)
            except Exception:
                pass
        return self.project_client.agents.threads.create()

    def _execute_agent_run(
        self, thread_id: str, agent_id: str, max_iterations: int = 30
    ):
        run = self.project_client.agents.runs.create(
            thread_id=thread_id, agent_id=agent_id
        )

        for _ in range(max_iterations):
            if run.status not in ["queued", "in_progress", "requires_action"]:
                break
            time.sleep(0.2)
            run = self.project_client.agents.runs.get(
                thread_id=thread_id, run_id=run.id
            )

        return run

    def _execute_routing_run(self, thread_id: str, max_iterations: int = 30):
        run = self.project_client.agents.runs.create(
            thread_id=thread_id, agent_id=self.main_agent.id
        )
        tools_called = []

        for _ in range(max_iterations):
            if run.status not in ["queued", "in_progress", "requires_action"]:
                break

            time.sleep(0.2)
            run = self.project_client.agents.runs.get(
                thread_id=thread_id, run_id=run.id
            )

            if run.status == "requires_action" and hasattr(run, "required_action"):
                tool_outputs = []
                tool_calls = getattr(
                    getattr(
                        getattr(run, "required_action", None),
                        "submit_tool_outputs",
                        None,
                    ),
                    "tool_calls",
                    [],
                )

                for tool_call in tool_calls:
                    if hasattr(tool_call, "function"):
                        func_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        if func_name in ["_search_catalog", "search_catalog"]:
                            query = args.get("query", "")
                            output = self._search_catalog(query)
                            tools_called.append(f"search_catalog('{query}')")
                        elif func_name == "handoff_genie_agent":
                            query = args.get("query", "")
                            output = genie_agent_service.handoff_genie_agent(query)
                            tools_called.append(f"handoff_genie_agent('{query}')")
                        else:
                            output = json.dumps(
                                {
                                    "status": "error",
                                    "message": f"Unknown function: {func_name}",
                                }
                            )

                        tool_outputs.append(
                            {"tool_call_id": tool_call.id, "output": output}
                        )

                if tool_outputs:
                    self.project_client.agents.runs.submit_tool_outputs(
                        thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                    )

        return run, tools_called

    def _extract_response_from_thread(self, thread_id: str) -> tuple:
        messages = list(self.project_client.agents.messages.list(thread_id=thread_id))
        for message in messages:
            if message.role == "assistant":
                message_data = self.message_processor.extract_message_with_annotations(
                    message
                )
                return message_data["content"], message_data["annotations"]
        return "No response generated", []

    def _extract_run_details(self, thread_id: str, run_id: str) -> tuple:
        connected_agents_called = []
        tools_called = []

        run_steps = list(
            self.project_client.agents.run_steps.list(
                thread_id=thread_id, run_id=run_id
            )
        )

        for step in run_steps:
            if hasattr(step, "step_details") and hasattr(
                step.step_details, "tool_calls"
            ):
                for tool_call in step.step_details.tool_calls:
                    if hasattr(tool_call, "type"):
                        if tool_call.type == "connected_agent" and hasattr(
                            tool_call, "connected_agent"
                        ):
                            connected_agents_called.append(
                                tool_call.connected_agent.get("name", "unknown")
                            )
                        elif tool_call.type == "function" and hasattr(
                            tool_call, "function"
                        ):
                            func_name = tool_call.function.name
                            if func_name != "_search_catalog":
                                tools_called.append(f"{func_name}(...)")

        return connected_agents_called, tools_called

    def process_query_direct(
        self, query: str, agent_name: str, thread_id: str = None
    ) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        if agent_name not in self.connected_agents:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}",
                "response": f"Agent '{agent_name}' is not available",
            }

        thread = self._get_or_create_thread(thread_id)
        self.project_client.agents.messages.create(
            thread_id=thread.id, role="user", content=query
        )
        run = self._execute_agent_run(thread.id, self.connected_agents[agent_name].id)
        response_text, annotations = self._extract_response_from_thread(thread.id)

        return {
            "success": True,
            "response": response_text,
            "annotations": annotations,
            "metadata": {
                "query": query,
                "agent_used": agent_name,
                "direct_call": True,
                "run_status": run.status,
                "thread_id": thread.id,
                "run_id": run.id,
            },
        }

    def process_query(self, query: str, thread_id: str = None) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        thread = self._get_or_create_thread(thread_id)
        self.project_client.agents.messages.create(
            thread_id=thread.id, role="user", content=query
        )
        run, tools_called = self._execute_routing_run(thread.id)
        response_text, annotations = self._extract_response_from_thread(thread.id)
        connected_agents_called, additional_tools = self._extract_run_details(
            thread.id, run.id
        )
        tools_called.extend(additional_tools)

        return {
            "success": True,
            "response": response_text,
            "annotations": annotations,
            "metadata": {
                "query": query,
                "run_status": run.status,
                "tools_called": tools_called,
                "connected_agents_called": connected_agents_called,
                "thread_id": thread.id,
                "run_id": run.id,
            },
        }

    def analyze_purview(self, query: str) -> Dict[str, Any]:
        catalog_results = self._search_catalog(query)
        catalog_data = json.loads(catalog_results)

        if catalog_data.get("assets_found", 0) > 0:
            assets = catalog_data.get("results", [])
            agent_types = [
                asset["connected_agent"]
                for asset in assets
                if asset.get("connected_agent")
            ]

            if agent_types:
                purview_analysis = f"Found {len(assets)} relevant data assets. Primary agent: {agent_types[0]}"
            else:
                purview_analysis = (
                    f"Found {len(assets)} data assets but no connected agents available"
                )
        else:
            purview_analysis = "No relevant data assets found in catalog. Query may require web search."

        return {
            "success": True,
            "purview": purview_analysis,
            "catalog_results": catalog_data,
            "confidence": 0.8 if catalog_data.get("assets_found", 0) > 0 else 0.3,
        }

    def get_thread_messages(self, thread_id: str) -> Dict[str, Any]:
        if not self._initialized:
            self.initialize()

        messages = list(self.project_client.agents.messages.list(thread_id=thread_id))
        formatted_messages = self.message_processor.format_thread_messages(
            messages, thread_id
        )

        return {
            "success": True,
            "messages": formatted_messages,
            "thread_id": thread_id,
            "message_count": len(formatted_messages),
        }

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "service": "Connected Agent Service",
            "initialized": self._initialized,
            "agents_created": len(self.connected_agents),
            "main_agent_ready": self.main_agent is not None,
            "project_client_ready": self.project_client is not None,
        }

    def cleanup(self):
        if self.main_agent and self.project_client:
            self.project_client.agents.delete_agent(self.main_agent.id)

        if self.connected_agents and self.project_client:
            for agent in self.connected_agents.values():
                self.project_client.agents.delete_agent(agent.id)

        if self.cleanup_resources and self.project_client:
            if self.cleanup_resources.get("vector_store"):
                self.project_client.agents.vector_stores.delete(
                    self.cleanup_resources["vector_store"].id
                )
            if self.cleanup_resources.get("file"):
                self.project_client.agents.files.delete(
                    self.cleanup_resources["file"].id
                )


connected_agent_service = ConnectedAgentService()
