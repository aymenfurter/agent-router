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
        
        yield {
            'credential': mock_cred,
            'cli_credential': mock_cli_cred,
            'client': mock_client
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

@pytest.fixture
def mock_env_vars(env_vars, monkeypatch):
    """Mock environment variables for testing"""
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    # Also patch the settings object directly to ensure it uses the mocked values
    with patch('config.settings.settings') as mock_settings_obj:
        mock_settings_obj.AZURE_AI_AGENT_ENDPOINT = env_vars['AZURE_AI_AGENT_ENDPOINT']
        mock_settings_obj.MODEL_DEPLOYMENT_NAME = env_vars['MODEL_DEPLOYMENT_NAME']
        mock_settings_obj.PURVIEW_ENDPOINT = env_vars['PURVIEW_ENDPOINT']
        mock_settings_obj.BING_CONNECTION_ID = env_vars['BING_CONNECTION_ID']
        mock_settings_obj.FABRIC_CONNECTION_ID = env_vars['FABRIC_CONNECTION_ID']
        mock_settings_obj.ENABLE_FABRIC_AGENT = env_vars['ENABLE_FABRIC_AGENT'].lower() == 'true'
        mock_settings_obj.DATABRICKS_INSTANCE = env_vars['DATABRICKS_INSTANCE']
        mock_settings_obj.GENIE_SPACE_ID = env_vars['GENIE_SPACE_ID']
        mock_settings_obj.DATABRICKS_AUTH_TOKEN = env_vars['DATABRICKS_AUTH_TOKEN']
        mock_settings_obj.FLASK_HOST = env_vars['FLASK_HOST']
        mock_settings_obj.FLASK_PORT = int(env_vars['FLASK_PORT'])
        mock_settings_obj.FLASK_DEBUG = env_vars['FLASK_DEBUG'].lower() == 'true'
        yield mock_settings_obj