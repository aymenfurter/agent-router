from pathlib import Path
from typing import Any, Dict, Tuple

import requests
from azure.ai.agents.models import (
    BingGroundingTool,
    ConnectedAgentTool,
    FabricTool,
    FilePurpose,
    FileSearchTool,
    FunctionTool,
)
from azure.ai.projects import AIProjectClient

from config.settings import settings
from utils.logging_config import get_logger


class AgentFactory:

    def __init__(self, project_client: AIProjectClient):
        self.logger = get_logger(__name__)
        self.project_client = project_client

    def create_fabric_agent(self) -> Any:
        if not settings.ENABLE_FABRIC_AGENT or not settings.FABRIC_CONNECTION_ID:
            return None

        fabric_tool = FabricTool(connection_id=settings.FABRIC_CONNECTION_ID)
        return self.project_client.agents.create_agent(
            model=settings.MODEL_DEPLOYMENT_NAME,
            name="fabric-agent",
            instructions="You are a data analysis agent with access to Microsoft Fabric data sources.",
            tools=fabric_tool.definitions,
        )

    def create_web_agent(self) -> Any:
        bing_tool = BingGroundingTool(connection_id=settings.BING_CONNECTION_ID)
        return self.project_client.agents.create_agent(
            model=settings.MODEL_DEPLOYMENT_NAME,
            name="web-agent",
            instructions="You are a web search agent that finds current information from the internet using Bing Search.",
            tools=bing_tool.definitions,
        )

    def create_rag_agent(self) -> Tuple[Any, Dict[str, Any]]:
        doc_url = "https://download.microsoft.com/documents/uk/athome/SM_Learn_5MinEncarta_F.pdf"
        data_dir = Path("./data")
        data_dir.mkdir(exist_ok=True)
        file_path = data_dir / "encarta_guide.pdf"

        if not file_path.exists():
            response = requests.get(doc_url)
            with open(file_path, "wb") as f:
                f.write(response.content)

        file = self.project_client.agents.files.upload_and_poll(
            file_path=str(file_path), purpose=FilePurpose.AGENTS
        )

        vector_store = self.project_client.agents.vector_stores.create_and_poll(
            file_ids=[file.id], name="rag_vectorstore"
        )

        file_search = FileSearchTool(vector_store_ids=[vector_store.id])

        rag_agent = self.project_client.agents.create_agent(
            model=settings.MODEL_DEPLOYMENT_NAME,
            name="rag-agent",
            instructions="You are a RAG agent that searches documents to answer questions.",
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )

        return rag_agent, {"vector_store": vector_store, "file": file}

    def create_routing_agent(
        self, connected_agents: Dict[str, Any], search_function, genie_function
    ) -> Any:
        function_tool = FunctionTool(functions={search_function, genie_function})

        connected_tools = [
            ConnectedAgentTool(
                id=agent.id,
                name=agent_name,
                description=f"Delegate to {agent_name} based on the query and catalog results",
            )
            for agent_name, agent in connected_agents.items()
        ]

        all_tools = function_tool.definitions + [
            tool.definitions[0] for tool in connected_tools
        ]

        return self.project_client.agents.create_agent(
            model=settings.MODEL_DEPLOYMENT_NAME,
            name="purview_routing_agent",
            instructions="""You are a routing agent for Microsoft Purview.
            Your role is to help users find and access the right data sources and agents.

            WORKFLOW:
            1. ALWAYS start by using the search_catalog function to find relevant data assets via Purview (search single term-based like 'blog' or 'software')
            2. If the there are multiple possible assets that could match, ask clarifying questions such as ("From what business domain would you like to learn the sales?" or "From what timespan are you interested in?")
            3. Once a data asset was identified from the catalog results:
               - If genie agent is mentioned in the asset description, use the handoff_genie_agent function to process data questions
               - If there is a RAG agent associated with relevant assets, call the rag_agent
               - If there is a Fabric agent associated with relevant assets, call the fabric_agent
               - If only contact info is available, provide the contact details
               - If the query is off-topic and no relevant data assets are found, use the web_agent

            ROUTING DECISION LOGIC:
            - For data analysis queries with catalog assets mentioning "genie" → use handoff_genie_agent
            - For document/knowledge queries with RAG assets → use rag_agent
            - For structured data queries with Fabric assets → use fabric_agent
            - For weather, current events, general knowledge (no relevant catalog assets) → use web_agent
            - When no agents are available for catalog assets → provide contact info
            - When multiple data sources could match (for example, sources with the same name but different timespans, and the query does not specify a timespan), do not route directly. Instead, ask a clarifying question such as: "To find the right agent, could you clarify which of these data assets best fits your query?"

            CRITICAL INSTRUCTIONS FOR DATA PRESENTATION:
            - When handoff_genie_agent returns successful results, you MUST include the entire response text in your answer
            - If handoff_genie_agent provides data tables, SQL queries, or data samples, show ALL of it to the user
            - Never say "I have the data" or "data is available" - actually present the complete data response
            - Copy the full response text from handoff_genie_agent directly into your response to the user
            - Do NOT summarize, filter, or withhold any data that handoff_genie_agent provides

            IMPORTANT:
            - NEVER answer questions yourself. Always route to appropriate functions or connected agents
            - Use handoff_genie_agent function for data analysis queries when genie is mentioned in catalog results
            - Use connected agents (rag_agent, fabric_agent, web_agent) for document search, fabric data, or web search
            - Use web search for queries regarding recent topics (e.g. current events or weather)
            - Rely entirely on the search_catalog results to guide your routing decisions
            - Always provide contact info if an asset has no connected agent


            Always search the catalog first and let the API results guide your routing decisions. Present all data results directly to users.""",
            tools=all_tools,
        )
