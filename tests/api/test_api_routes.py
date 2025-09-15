import pytest
import json
from unittest.mock import patch, Mock, MagicMock
import os

# Mock dependencies before imports
with patch.dict('sys.modules', {
    'dotenv': MagicMock(),
    'azure': MagicMock(),
    'azure.identity': MagicMock(),
    'azure.ai': MagicMock(),
    'azure.ai.projects': MagicMock(),
    'azure.ai.agents': MagicMock(),
    'azure.ai.agents.models': MagicMock(),
    'azure.purview': MagicMock(),
    'azure.purview.catalog': MagicMock(),
}):
    # Import blueprints first
    from api.health_routes import health_bp
    from api.query_routes import query_bp
    from api.thread_routes import thread_bp
    
    # Then import the actual app with mocked dependencies
    with patch('app.connected_agent_service') as mock_app_service, \
         patch('app.setup_logging') as mock_logging, \
         patch('app.settings') as mock_app_settings:
        
        mock_app_service.cleanup.return_value = None
        mock_logging.return_value = None
        mock_app_settings.FLASK_HOST = '0.0.0.0'
        mock_app_settings.FLASK_PORT = 5000
        mock_app_settings.FLASK_DEBUG = False
        
        from app import app


class TestAPIHealthRoutes:
    """Test cases for health API routes"""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(health_bp)
        app.config['TESTING'] = True
        return app.test_client()

    @patch('api.health_routes.connected_agent_service')
    @patch('api.health_routes.settings')
    def test_health_check_endpoint(self, mock_settings, mock_service, client):
        """Test the health check endpoint"""
        # Mock service health status
        mock_service.get_health_status.return_value = {
            'service': 'Connected Agent Service',
            'initialized': True,
            'agents_created': 3,
            'main_agent_ready': True,
            'project_client_ready': True
        }
        
        # Mock settings validation
        mock_settings.validate.return_value = {
            'valid': True,
            'missing_variables': [],
            'fabric_enabled': True,
            'genie_configured': True
        }
        
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'
        assert 'connected_agent_service' in data
        assert 'configuration' in data
        
        mock_service.get_health_status.assert_called_once()
        mock_settings.validate.assert_called_once()

    @patch('api.health_routes.settings')
    def test_config_endpoint(self, mock_settings, client):
        """Test the configuration endpoint"""
        # Mock settings
        mock_settings.ENABLE_FABRIC_AGENT = True
        mock_settings.DATABRICKS_INSTANCE = 'test.databricks.com'
        mock_settings.GENIE_SPACE_ID = 'test-space-id'
        mock_settings.DATABRICKS_AUTH_TOKEN = 'test-token'
        
        response = client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['fabric_agent_enabled'] is True
        assert data['genie_configured'] is True

    @patch('api.health_routes.settings')
    def test_config_endpoint_genie_not_configured(self, mock_settings, client):
        """Test configuration endpoint when Genie is not configured"""
        mock_settings.ENABLE_FABRIC_AGENT = False
        mock_settings.DATABRICKS_INSTANCE = None
        mock_settings.GENIE_SPACE_ID = None
        mock_settings.DATABRICKS_AUTH_TOKEN = None
        
        response = client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['fabric_agent_enabled'] is False
        assert data['genie_configured'] is False


class TestAPIQueryRoutes:
    """Test cases for query API routes"""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(query_bp)
        app.config['TESTING'] = True
        return app.test_client()

    @patch('api.query_routes.connected_agent_service')
    def test_analyze_query_endpoint(self, mock_service, client):
        """Test the analyze query endpoint"""
        mock_service.analyze_purview.return_value = {
            'success': True,
            'purview': 'Found 2 relevant data assets. Primary agent: genie',
            'catalog_results': {
                'status': 'success',
                'assets_found': 2,
                'results': [{'name': 'sales_data', 'connected_agent': 'genie'}]
            },
            'confidence': 0.8
        }
        
        response = client.post('/api/analyze', 
                             json={'query': 'show me sales data'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['purview'] == 'Found 2 relevant data assets. Primary agent: genie'
        
        mock_service.analyze_purview.assert_called_once_with('show me sales data')

    @patch('api.query_routes.connected_agent_service')
    def test_route_query_endpoint(self, mock_service, client):
        """Test the route query endpoint"""
        mock_service.process_query.return_value = {
            'success': True,
            'response': 'Here is your sales analysis',
            'annotations': [],
            'metadata': {
                'query': 'analyze sales',
                'tools_called': ['search_catalog', 'handoff_genie_agent'],
                'thread_id': 'thread-123',
                'run_id': 'run-456'
            }
        }
        
        response = client.post('/api/route',
                             json={'query': 'analyze sales', 'thread_id': 'thread-123'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['response'] == 'Here is your sales analysis'
        
        mock_service.process_query.assert_called_once_with('analyze sales', 'thread-123')

    @patch('api.query_routes.connected_agent_service')
    def test_process_query_endpoint(self, mock_service, client):
        """Test the process query endpoint (end-to-end)"""
        # Mock processing result
        mock_service.process_query.return_value = {
            'success': True,
            'response': 'Sales analysis complete',
            'annotations': [{'type': 'file_citation', 'file_name': 'sales.pdf'}],
            'metadata': {
                'query': 'sales analysis',
                'tools_called': ['search_catalog'],
                'thread_id': 'thread-789',
                'run_id': 'run-101'
            }
        }
        
        # Mock analysis result
        mock_service.analyze_purview.return_value = {
            'purview': 'Found sales data assets',
            'catalog_results': {'assets_found': 1},
            'confidence': 0.9
        }
        
        response = client.post('/api/process',
                             json={'query': 'sales analysis', 'thread_id': 'thread-789'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['query'] == 'sales analysis'
        assert data['purview_analysis'] == 'Found sales data assets'
        assert data['response'] == 'Sales analysis complete'
        assert len(data['annotations']) == 1
        assert 'metadata' in data
        assert 'analysis_metadata' in data

    @patch('api.query_routes.genie_agent_service')
    def test_process_query_direct_genie(self, mock_genie_service, client):
        """Test direct query processing with Genie agent"""
        mock_genie_service.handoff_genie_agent.return_value = json.dumps({
            'status': 'success',
            'response': 'SQL query result: 150 records',
            'conversation_id': 'conv-123',
            'generated_query': 'SELECT COUNT(*) FROM sales'
        })
        
        response = client.post('/api/process-direct',
                             json={'query': 'count sales records', 'agent': 'genie'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['response'] == 'SQL query result: 150 records'
        assert data['metadata']['agent_used'] == 'genie'
        assert data['metadata']['direct_call'] is True
        
        mock_genie_service.handoff_genie_agent.assert_called_once_with('count sales records')

    @patch('api.query_routes.connected_agent_service')
    def test_process_query_direct_other_agent(self, mock_service, client):
        """Test direct query processing with other agents"""
        mock_service.process_query_direct.return_value = {
            'success': True,
            'response': 'Web search results',
            'annotations': [],
            'metadata': {
                'query': 'current weather',
                'agent_used': 'web_agent',
                'direct_call': True,
                'thread_id': 'thread-web',
                'run_id': 'run-web'
            }
        }
        
        response = client.post('/api/process-direct',
                             json={'query': 'current weather', 'agent': 'web'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['response'] == 'Web search results'
        
        mock_service.process_query_direct.assert_called_once_with('current weather', 'web_agent', None)


class TestAPIThreadRoutes:
    """Test cases for thread API routes"""

    @pytest.fixture
    def client(self):
        """Create a test client using the real Flask app"""
        app.config['TESTING'] = True
        return app.test_client()

    def test_get_thread_messages(self, client):
        """Test getting thread messages"""
        from services.connected_agent_service import connected_agent_service
        from api.thread_routes import connected_agent_service as route_service
        
        print(f"DEBUG: Service instances are same: {connected_agent_service is route_service}")
        print(f"DEBUG: Service ID: {id(connected_agent_service)}")
        print(f"DEBUG: Route Service ID: {id(route_service)}")
        
        # Mock the method directly on the instance
        expected_response = {
            'success': True,
            'messages': [
                {
                    'id': 'msg-1',
                    'role': 'user',
                    'content': 'Hello',
                    'annotations': [],
                    'created_at': '2024-01-01T10:00:00Z',
                    'thread_id': 'thread-123'
                },
                {
                    'id': 'msg-2',
                    'role': 'assistant',
                    'content': 'How can I help?',
                    'annotations': [],
                    'created_at': '2024-01-01T10:01:00Z',
                    'thread_id': 'thread-123'
                }
            ],
            'thread_id': 'thread-123',
            'message_count': 2
        }
        
        with patch.object(connected_agent_service, 'get_thread_messages', return_value=expected_response) as mock_method:
            print(f"DEBUG: Mock object: {mock_method}")
            print(f"DEBUG: Mock return value: {mock_method.return_value}")
            
            response = client.get('/api/thread/thread-123/messages')
            
            print(f"DEBUG: Mock called: {mock_method.called}")
            print(f"DEBUG: Mock call count: {mock_method.call_count}")
            
            assert response.status_code == 200
            data = json.loads(response.data)
            print(f"DEBUG: Actual response data: {data}")  # Debug output
            assert data['success'] is True
            assert data['thread_id'] == 'thread-123'
            assert data['message_count'] == 2
            assert len(data['messages']) == 2
            
            mock_method.assert_called_once_with('thread-123')