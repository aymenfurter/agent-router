import json

from flask import Blueprint, jsonify, request

from services.connected_agent_service import connected_agent_service
from services.genie_agent_service import genie_agent_service

query_bp = Blueprint("query", __name__, url_prefix="/api")


@query_bp.route("/analyze", methods=["POST"])
def analyze_query():
    """Analyze query purview using Connected Agent Service"""
    query = request.get_json()["query"].strip()
    return jsonify(connected_agent_service.analyze_purview(query))


@query_bp.route("/route", methods=["POST"])
def route_query():
    """Route query to appropriate agent using Connected Agent Service"""
    data = request.get_json()
    return jsonify(
        connected_agent_service.process_query(
            data["query"].strip(), data.get("thread_id")
        )
    )


@query_bp.route("/process", methods=["POST"])
def process_query():
    """Process query end-to-end (single call, not duplicate processing)"""
    data = request.get_json()
    query = data["query"].strip()
    thread_id = data.get("thread_id")

    processing_result = connected_agent_service.process_query(query, thread_id)
    analysis_result = connected_agent_service.analyze_purview(query)

    return jsonify(
        {
            "success": processing_result.get("success", False),
            "query": query,
            "purview_analysis": analysis_result.get("purview", ""),
            "response": processing_result.get("response", ""),
            "annotations": processing_result.get("annotations", []),
            "metadata": processing_result.get("metadata", {}),
            "analysis_metadata": {
                "catalog_results": analysis_result.get("catalog_results", {}),
                "confidence": analysis_result.get("confidence", 0.0),
            },
        }
    )


@query_bp.route("/process-direct", methods=["POST"])
def process_query_direct():
    """Process query directly with a specific agent (manual mode)"""
    data = request.get_json()
    query, agent, thread_id = (
        data["query"].strip(),
        data["agent"].strip(),
        data.get("thread_id"),
    )

    if agent == "genie":
        result_data = json.loads(genie_agent_service.handoff_genie_agent(query))
        return jsonify(
            {
                "success": result_data.get("status") == "success",
                "response": result_data.get("response", ""),
                "annotations": [],
                "metadata": {
                    "query": query,
                    "agent_used": "genie",
                    "direct_call": True,
                    "thread_id": thread_id or "genie-session",
                    "genie_details": result_data,
                },
            }
        )

    agent_mapping = {"fabric": "fabric_agent", "rag": "rag_agent", "web": "web_agent"}
    return jsonify(
        connected_agent_service.process_query_direct(
            query, agent_mapping[agent], thread_id
        )
    )
