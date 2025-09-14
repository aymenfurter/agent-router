import pytest
import json
import os
from unittest.mock import patch, Mock, MagicMock
import responses

# Mock all external dependencies at module level
mock_modules = [
    'azure', 'azure.identity', 'azure.ai', 'azure.ai.projects', 
    'azure.ai.agents', 'azure.ai.agents.models', 'azure.purview',
    'azure.purview.catalog', 'openai', 'fastapi', 'uvicorn', 'pydantic',
    'dotenv'
]

for module in mock_modules:
    if module not in globals():
        globals()[module] = MagicMock()

# Set up proper mocking before imports
with patch.dict('sys.modules', {module: MagicMock() for module in mock_modules}):
    from services.connected_agent_service import ConnectedAgentService
    from services.catalog_service import CatalogService
    from services.genie_agent_service import GenieAgentService


class TestIntegrationConnectedAgentService:
    """Integration tests for ConnectedAgentService with mocked external dependencies"""
    
    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """Setup environment variables for testing"""
        env_vars = {
            'AZURE_AI_AGENT_ENDPOINT': 'https://test.endpoint.com',
            'MODEL_DEPLOYMENT_NAME': 'test-model',
            'PURVIEW_ENDPOINT': 'https://test-purview.endpoint.com',
            'BING_CONNECTION_ID': 'test-bing-id',
            'FABRIC_CONNECTION_ID': 'test-fabric-id',
            'ENABLE_FABRIC_AGENT': 'true',
            'DATABRICKS_INSTANCE': 'test.databricks.com',
            'GENIE_SPACE_ID': 'test-space-id',
            'DATABRICKS_AUTH_TOKEN': 'test-token'
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
        return env_vars
    
    @pytest.fixture
    def mock_project_client(self):
        """Create a comprehensive mock for AIProjectClient"""
        client = Mock()
        
        # Mock agents
        client.agents = Mock()
        client.agents.create_agent.return_value = Mock(id='agent-123')
        client.agents.threads = Mock()
        client.agents.messages = Mock()
        client.agents.runs = Mock()
        client.agents.files = Mock()
        client.agents.vector_stores = Mock()
        client.agents.run_steps = Mock()
        
        # Mock thread operations
        client.agents.threads.create.return_value = Mock(id='thread-456')
        client.agents.threads.get.return_value = Mock(id='thread-456')
        
        # Mock message operations
        client.agents.messages.create.return_value = Mock(id='msg-789')
        client.agents.messages.list.return_value = []
        
        # Mock run operations
        mock_run = Mock(id='run-101', status='completed')
        client.agents.runs.create.return_value = mock_run
        client.agents.runs.get.return_value = mock_run
        client.agents.runs.submit_tool_outputs.return_value = mock_run
        
        # Mock file operations
        mock_file = Mock(id='file-123', filename='test.pdf')
        client.agents.files.upload_and_poll.return_value = mock_file
        client.agents.files.get.return_value = mock_file
        
        # Mock vector store operations
        mock_vector_store = Mock(id='vs-456')
        client.agents.vector_stores.create_and_poll.return_value = mock_vector_store
        
        return client
    
    @patch('services.connected_agent_service.DefaultAzureCredential')
    @patch('services.connected_agent_service.AIProjectClient')
    def test_initialize_service(self, mock_ai_client, mock_credential, mock_env_vars):
        """Test service initialization process"""
        # Setup mocks
        mock_credential.return_value = Mock()
        mock_ai_client.return_value = Mock()
        
        service = ConnectedAgentService()
        assert service._initialized is False
        
        # Initialize service
        result = service.initialize()
        
        assert result is True
        assert service._initialized is True
        assert service.project_client is not None
        assert service.agent_factory is not None
        assert service.message_processor is not None
        
        mock_ai_client.assert_called_once()
        mock_credential.assert_called_once()
    
    @patch('services.connected_agent_service.DefaultAzureCredential')
    @patch('services.connected_agent_service.AIProjectClient')
    def test_get_health_status(self, mock_ai_client, mock_credential, mock_env_vars):
        """Test health status reporting"""
        mock_credential.return_value = Mock()
        mock_ai_client.return_value = Mock()
        
        service = ConnectedAgentService()
        health_status = service.get_health_status()
        
        assert health_status['service'] == 'Connected Agent Service'
        assert health_status['initialized'] is False
        assert health_status['agents_created'] == 0
        assert health_status['main_agent_ready'] is False
        assert health_status['project_client_ready'] is False
        
        # Initialize and check again
        service.initialize()
        health_status = service.get_health_status()
        
        assert health_status['initialized'] is True
        assert health_status['project_client_ready'] is True
    
    @responses.activate
    @patch('services.connected_agent_service.DefaultAzureCredential')
    @patch('services.connected_agent_service.AIProjectClient')
    @patch('services.connected_agent_service.catalog_service')
    def test_analyze_purview_with_results(self, mock_catalog, mock_ai_client, mock_credential, mock_env_vars):
        """Test Purview analysis with catalog results"""
        # Setup mocks
        mock_credential.return_value = Mock()
        mock_ai_client.return_value = Mock()
        
        # Mock catalog service response
        mock_catalog.search_catalog.return_value = {
            'status': 'success',
            'assets_found': 2,
            'results': [
                {'name': 'Sales DB', 'connected_agent': 'genie'},
                {'name': 'Docs', 'connected_agent': 'rag'}
            ]
        }
        
        service = ConnectedAgentService()
        result = service.analyze_purview("sales data")
        
        assert result['success'] is True
        assert result['confidence'] == 0.8
        assert 'Found 2 relevant data assets' in result['purview']
        assert result['catalog_results']['assets_found'] == 2
        
        mock_catalog.search_catalog.assert_called_once_with("sales data")
    
    @responses.activate
    @patch('services.connected_agent_service.DefaultAzureCredential')
    @patch('services.connected_agent_service.AIProjectClient')
    @patch('services.connected_agent_service.catalog_service')
    def test_analyze_purview_no_results(self, mock_catalog, mock_ai_client, mock_credential, mock_env_vars):
        """Test Purview analysis with no catalog results"""
        # Setup mocks
        mock_credential.return_value = Mock()
        mock_ai_client.return_value = Mock()
        
        # Mock empty catalog response
        mock_catalog.search_catalog.return_value = {
            'status': 'success',
            'assets_found': 0,
            'results': []
        }
        
        service = ConnectedAgentService()
        result = service.analyze_purview("unknown query")
        
        assert result['success'] is True
        assert result['confidence'] == 0.3
        assert 'No relevant data assets found' in result['purview']
    
    @patch('services.connected_agent_service.requests')
    def test_genie_integration_service(self, mock_requests):
        """Test integration with Genie service"""
        # Mock successful Genie response
        mock_start_response = Mock()
        mock_start_response.json.return_value = {
            'conversation': {'id': 'conv-123'},
            'message': {'id': 'msg-456'}
        }
        mock_start_response.raise_for_status.return_value = None
        
        mock_status_response = Mock()
        mock_status_response.json.return_value = {
            'status': 'COMPLETED',
            'attachments': [{
                'text': {'content': 'Query result: 100 records found'}
            }]
        }
        mock_status_response.raise_for_status.return_value = None
        
        mock_requests.post.return_value = mock_start_response
        mock_requests.get.return_value = mock_status_response
        
        # Test with environment variables
        with patch.dict(os.environ, {
            'DATABRICKS_INSTANCE': 'test.databricks.com',
            'GENIE_SPACE_ID': 'test-space-id',
            'DATABRICKS_AUTH_TOKEN': 'test-token'
        }):
            genie_service = GenieAgentService()
            result = genie_service.handoff_genie_agent("SELECT COUNT(*) FROM sales")
            
            result_data = json.loads(result)
            assert result_data['status'] == 'success'
            assert 'Query result: 100 records found' in result_data['response']
    
    def test_service_singleton_behavior(self):
        """Test that the connected_agent_service is properly accessible"""
        from services.connected_agent_service import connected_agent_service
        assert connected_agent_service is not None
        assert isinstance(connected_agent_service, ConnectedAgentService)


class TestEndToEndWorkflow:
    """End-to-end workflow tests with full mocking"""
    
    @pytest.fixture
    def mock_full_environment(self, monkeypatch):
        """Setup complete test environment"""
        env_vars = {
            'AZURE_AI_AGENT_ENDPOINT': 'https://test.endpoint.com',
            'MODEL_DEPLOYMENT_NAME': 'test-model',
            'PURVIEW_ENDPOINT': 'https://test-purview.endpoint.com',
            'BING_CONNECTION_ID': 'test-bing-id',
            'DATABRICKS_INSTANCE': 'test.databricks.com',
            'GENIE_SPACE_ID': 'test-space-id',
            'DATABRICKS_AUTH_TOKEN': 'test-token'
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
    
    @responses.activate
    @patch('services.connected_agent_service.DefaultAzureCredential')
    @patch('services.connected_agent_service.AIProjectClient')
    def test_query_processing_workflow(self, mock_ai_client, mock_credential, mock_full_environment):
        """Test complete query processing workflow"""
        # Setup AI client mock
        mock_client = Mock()
        mock_ai_client.return_value = mock_client
        
        # Mock agent creation
        mock_agent = Mock(id='routing-agent-123')
        mock_client.agents.create_agent.return_value = mock_agent
        
        # Mock thread operations
        mock_thread = Mock(id='thread-456')
        mock_client.agents.threads.create.return_value = mock_thread
        mock_client.agents.messages.create.return_value = Mock(id='msg-789')
        
        # Mock run operations
        mock_run = Mock(id='run-101', status='completed')
        mock_client.agents.runs.create.return_value = mock_run
        mock_client.agents.runs.get.return_value = mock_run
        
        # Mock messages list for response extraction
        mock_message = Mock()
        mock_message.role = 'assistant'
        mock_message.content = [Mock()]
        mock_message.content[0].text.value = 'Here is your analysis result'
        mock_message.file_citation_annotations = []
        mock_message.url_citation_annotations = []
        mock_client.agents.messages.list.return_value = [mock_message]
        
        # Mock run steps for metadata
        mock_client.agents.run_steps.list.return_value = []
        
        # Mock file and vector store operations
        mock_file = Mock(id='file-123')
        mock_client.agents.files.upload_and_poll.return_value = mock_file
        mock_vector_store = Mock(id='vs-456')
        mock_client.agents.vector_stores.create_and_poll.return_value = mock_vector_store
        
        # Create and initialize service
        service = ConnectedAgentService()
        service.initialize()
        
        # Process a query
        with patch('services.connected_agent_service.catalog_service') as mock_catalog:
            mock_catalog.search_catalog.return_value = {
                'status': 'success',
                'assets_found': 1,
                'results': [{'name': 'Sales DB', 'connected_agent': 'genie'}]
            }
            
            result = service.process_query("analyze sales data")
            
            assert result['success'] is True
            assert result['response'] == 'Here is your analysis result'
            assert 'metadata' in result
            assert result['metadata']['query'] == 'analyze sales data'
    
    def test_configuration_validation_workflow(self, mock_full_environment):
        """Test configuration validation across services"""
        from config.settings import Settings
        
        with patch('config.settings.load_dotenv'):
            settings = Settings()
            validation = settings.validate()
            
            assert validation['valid'] is True
            assert validation['genie_configured'] is True
            assert len(validation['missing_variables']) == 0
    
    @responses.activate
    def test_catalog_service_integration(self):
        """Test catalog service integration with proper mocking"""
        # Mock Purview API response
        responses.add(
            responses.POST,
            'https://test-purview.endpoint.com/datamap/api/search/query?api-version=2023-09-01',
            json={
                'value': [
                    {
                        'id': 'asset-1',
                        'displayText': 'Test Database',
                        'userDescription': 'Test data with agent: genie'
                    }
                ]
            },
            status=200
        )
        
        # Mock Azure CLI credential
        with patch('services.catalog_service.AzureCliCredential') as mock_cred, \
             patch('services.catalog_service.settings') as mock_settings:
            
            mock_settings.PURVIEW_ENDPOINT = 'https://test-purview.endpoint.com'
            mock_token = Mock(token='test-token')
            mock_cred.return_value.get_token.return_value = mock_token
            
            catalog = CatalogService()
            result = catalog.search_catalog("test query")
            
            assert result['status'] == 'success'
            assert result['assets_found'] == 1
            assert result['results'][0]['connected_agent'] == 'genie'