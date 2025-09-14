import os
import sys
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
sys.modules['dotenv'].load_dotenv = Mock()

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
    return env_vars