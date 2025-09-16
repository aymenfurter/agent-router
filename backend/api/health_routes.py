from flask import Blueprint, jsonify
from backend.services.connected_agent_service import connected_agent_service
from backend.config.settings import settings

health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'connected_agent_service': connected_agent_service.get_health_status(),
        'configuration': settings.validate()
    })

@health_bp.route('/config')
def get_config():
    genie_configured = all([settings.DATABRICKS_INSTANCE, settings.GENIE_SPACE_ID, settings.DATABRICKS_AUTH_TOKEN])
    features = {
        'fabric_agent_enabled': settings.ENABLE_FABRIC_AGENT
    }
    return jsonify({
        'fabric_agent_enabled': settings.ENABLE_FABRIC_AGENT,
        'genie_configured': genie_configured,
        'features': {
            **features,
            'genie_configured': genie_configured
        }
    })
