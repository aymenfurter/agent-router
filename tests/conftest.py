import os
import sys
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

# Mock external dependencies before imports
mock_modules = [
    'azure', 'azure.identity', 'azure.ai', 'azure.ai.projects', 
    'azure.ai.agents', 'azure.ai.agents.models', 'azure.purview', 
    'azure.purview.catalog', 'openai', 'fastapi', 'uvicorn', 'pydantic',
    'python-dotenv', 'dotenv'
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

# Specifically mock the classes we need
sys.modules['dotenv'].load_dotenv = Mock(return_value=True)

# Mock Azure AI Agent tools
sys.modules['azure.ai.agents.models'].ConnectedAgentTool = MagicMock()
sys.modules['azure.ai.agents.models'].FunctionTool = MagicMock()
sys.modules['azure.ai.agents.models'].FabricTool = MagicMock()
sys.modules['azure.ai.agents.models'].BingGroundingTool = MagicMock()
sys.modules['azure.ai.agents.models'].FileSearchTool = MagicMock()
sys.modules['azure.ai.agents.models'].FilePurpose = MagicMock()

# Mock requests globally to prevent any network calls during testing
import requests
original_get = requests.get
def mock_get(*args, **kwargs):
    if 'download.microsoft.com' in str(args[0]):
        # Mock the PDF download response
        mock_response = MagicMock()
        mock_response.content = b'Mock PDF content for testing'
        return mock_response
    return original_get(*args, **kwargs)

requests.get = mock_get

@pytest.fixture(autouse=True)
def mock_azure_dependencies():
    """Mock Azure dependencies to avoid authentication issues during testing"""
    with patch('azure.identity.DefaultAzureCredential') as mock_cred, \
         patch('azure.identity.AzureCliCredential') as mock_cli_cred, \
         patch('azure.ai.projects.AIProjectClient') as mock_client:
        
        # Setup mock credentials
        mock_cred.return_value = Mock()
        mock_cli_cred.return_value.get_token.return_value = Mock(token="test_token")
        
        # Setup mock AI project client
        mock_client.return_value = Mock()
        
        # Mock the connected agent service methods with default responses
        from services.connected_agent_service import connected_agent_service
        
        # Mock common service methods  
        # Note: catalog_service is excluded from global mocking to avoid conflicts with individual test patches
        with patch.object(connected_agent_service, 'get_health_status') as mock_health, \
             patch.object(connected_agent_service, 'get_thread_messages') as mock_messages, \
             patch.object(connected_agent_service, 'analyze_purview') as mock_analyze, \
             patch.object(connected_agent_service, 'process_query') as mock_process, \
             patch.object(connected_agent_service, 'process_query_direct') as mock_direct, \
             patch('config.settings.settings.validate') as mock_settings_validate:
            
            # Setup default mock responses
            mock_health.return_value = {
                'service': 'Connected Agent Service',
                'initialized': True,
                'agents_created': 3,
                'main_agent_ready': True,
                'project_client_ready': True
            }
            
            mock_messages.return_value = {
                'success': True,
                'messages': [],
                'thread_id': 'test-thread',
                'message_count': 0
            }
            
            mock_analyze.return_value = {
                'success': True,
                'purview': 'No relevant data assets found in catalog',
                'catalog_results': {'status': 'success', 'assets_found': 0},
                'confidence': 0.3
            }
            
            mock_process.return_value = {
                'success': True,
                'query': 'test query',
                'response': 'No response generated',
                'purview_analysis': 'No relevant data assets found',
                'annotations': [],
                'metadata': {},
                'analysis_metadata': {}
            }
            
            mock_direct.return_value = {
                'success': True,
                'response': 'No response generated',
                'metadata': {'agent_used': 'test', 'direct_call': True}
            }
            
            # Mock settings validation
            mock_settings_validate.return_value = {
                'valid': True,
                'missing_variables': [],
                'fabric_enabled': True,
                'genie_configured': True
            }
            
            yield {
                'credential': mock_cred,
                'cli_credential': mock_cli_cred,
                'client': mock_client,
                'service_mocks': {
                    'health': mock_health,
                    'messages': mock_messages,
                    'analyze': mock_analyze,
                    'process': mock_process,
                    'direct': mock_direct
                },
                'settings_validate': mock_settings_validate
            }

@pytest.fixture
def env_vars():
    """Provide test environment variables"""
    return {
        'AZURE_AI_AGENT_ENDPOINT': 'https://test.endpoint.com',
        'MODEL_DEPLOYMENT_NAME': 'test-model',
        'PURVIEW_ENDPOINT': 'https://test-purview.endpoint.com',
        'BING_CONNECTION_ID': 'test-bing-id',
        'FABRIC_CONNECTION_ID': 'test-fabric-id',
        'ENABLE_FABRIC_AGENT': 'true',
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token',
        'FLASK_HOST': '0.0.0.0',
        'FLASK_PORT': '5000',
        'FLASK_DEBUG': 'false'
    }

@pytest.fixture(autouse=True)
def mock_env_vars(env_vars, monkeypatch):
    """Mock environment variables for testing"""
    # Set environment variables first, before any imports
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    # Import settings after env vars are set
    from config.settings import Settings
    
    # Create a new settings instance with the mocked env vars
    test_settings = Settings()
    
    # Patch the settings object in the main config module only
    with patch('config.settings.settings', test_settings):
        yield test_settings