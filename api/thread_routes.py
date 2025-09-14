from flask import Blueprint, jsonify

from services.connected_agent_service import connected_agent_service

thread_bp = Blueprint("thread", __name__, url_prefix="/api")


@thread_bp.route("/thread/<thread_id>/messages", methods=["GET"])
def get_thread_messages(thread_id):
    """Get all messages from a specific thread"""
    result = connected_agent_service.get_thread_messages(thread_id)
    return jsonify(result)
