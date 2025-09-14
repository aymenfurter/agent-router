import json
import logging
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()


class GenieAgentService:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.databricks_instance = os.getenv("DATABRICKS_INSTANCE")
        self.genie_space_id = os.getenv("GENIE_SPACE_ID")
        self.auth_token = os.getenv("DATABRICKS_AUTH_TOKEN")

    def is_configured(self) -> bool:
        return all([self.databricks_instance, self.genie_space_id, self.auth_token])

    def handoff_genie_agent(self, query: str) -> str:
        if not self.is_configured():
            return json.dumps(
                {"status": "error", "message": "Missing Genie configuration"}
            )

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

        start_url = f"https://{self.databricks_instance}/api/2.0/genie/spaces/{self.genie_space_id}/start-conversation"
        start_response = requests.post(
            start_url, headers=headers, json={"content": query}
        )
        start_response.raise_for_status()
        start_data = start_response.json()

        conversation_id = start_data["conversation"]["id"]
        message_id = start_data["message"]["id"]

        status_url = f"https://{self.databricks_instance}/api/2.0/genie/spaces/{self.genie_space_id}/conversations/{conversation_id}/messages/{message_id}"

        for _ in range(60):
            time.sleep(0.5)
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data.get("status") in ["COMPLETED", "FAILED", "CANCELLED"]:
                break

        if status_data.get("status") != "COMPLETED":
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Genie query failed with status: {status_data.get('status')}",
                }
            )

        attachments = status_data.get("attachments", [])
        text_response = "No response generated"
        generated_query = None
        query_description = None
        row_count = None
        attachment_id = None

        for attachment in attachments:
            if "text" in attachment and attachment["text"]:
                text_content = attachment["text"].get("content", "")
                if text_content:
                    text_response = text_content

            if "query" in attachment and attachment["query"]:
                query_info = attachment["query"]
                generated_query = query_info.get("query", "")
                query_description = query_info.get("description", "")
                row_count = query_info.get("query_result_metadata", {}).get("row_count")
                attachment_id = attachment.get("attachment_id")

        if generated_query and text_response == "No response generated":
            text_response = (
                f"{query_description}\n\nGenerated SQL:\n{generated_query}"
                if query_description
                else f"Generated SQL query:\n{generated_query}"
            )
            if row_count is not None:
                text_response += f"\n\nTotal rows: {row_count}"

        if attachment_id and generated_query:
            results_url = f"https://{self.databricks_instance}/api/2.0/genie/spaces/{self.genie_space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}"
            results_response = requests.get(results_url, headers=headers)

            if results_response.status_code == 200:
                query_results = results_response.json()
                result_data = query_results.get("statement_response", {}).get(
                    "result"
                ) or query_results.get("result")

                if result_data and "data_array" in result_data:
                    rows = result_data["data_array"][:10]
                    schema = result_data.get("schema", {}).get("columns", [])

                    text_response += "\n\nFirst 10 rows:"

                    if schema:
                        headers_line = " | ".join(
                            [
                                col.get("name", f"col_{i}")
                                for i, col in enumerate(schema)
                            ]
                        )
                        text_response += f"\n{headers_line}\n{'-' * len(headers_line)}"

                    for row in rows:
                        if isinstance(row, list):
                            text_response += f"\n{' | '.join([str(val) if val is not None else 'NULL' for val in row])}"

                    if row_count and row_count > 10:
                        text_response += f"\n\n... showing 10 of {row_count} total rows"

        return json.dumps(
            {
                "status": "success",
                "response": text_response,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "generated_query": generated_query,
                "row_count": row_count,
            }
        )


genie_agent_service = GenieAgentService()
