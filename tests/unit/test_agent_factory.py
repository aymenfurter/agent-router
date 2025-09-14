import pytest
from unittest.mock import patch, Mock, MagicMock

# Mock dependencies before imports
with patch.dict('sys.modules', {
    'azure': MagicMock(),
    'azure.identity': MagicMock(),
    'azure.ai': MagicMock(),
    'azure.ai.projects': MagicMock(),
    'azure.ai.agents': MagicMock(),
    'azure.ai.agents.models': MagicMock(),
}):
    from services.agent_factory import AgentFactory


class TestAgentFactory:
    """Test cases for the AgentFactory class"""
    
    @pytest.fixture
    def mock_project_client(self):
        """Create a mock AIProjectClient"""
        client = Mock()
        client.agents = Mock()
        client.agents.create_agent.return_value = Mock(id='agent-123')
        client.agents.files = Mock()
        client.agents.vector_stores = Mock()
        return client
    
    @pytest.fixture
    def agent_factory(self, mock_project_client):
        """Create AgentFactory instance with mocked client"""
        return AgentFactory(mock_project_client)
    
    def test_init(self, mock_project_client):
        """Test AgentFactory initialization"""
        factory = AgentFactory(mock_project_client)
        assert factory.project_client == mock_project_client
        assert factory.logger is not None
    
    @patch('services.agent_factory.settings')
    def test_create_fabric_agent_disabled(self, mock_settings, agent_factory):
        """Test create_fabric_agent when Fabric is disabled"""
        mock_settings.ENABLE_FABRIC_AGENT = False
        mock_settings.FABRIC_CONNECTION_ID = None
        
        result = agent_factory.create_fabric_agent()
        assert result is None
    
    @patch('services.agent_factory.settings')  
    def test_create_fabric_agent_no_connection_id(self, mock_settings, agent_factory):
        """Test create_fabric_agent when connection ID is missing"""
        mock_settings.ENABLE_FABRIC_AGENT = True
        mock_settings.FABRIC_CONNECTION_ID = None
        
        result = agent_factory.create_fabric_agent()
        assert result is None
    
    @patch('services.agent_factory.FabricTool')
    @patch('services.agent_factory.settings')
    def test_create_fabric_agent_enabled(self, mock_settings, mock_fabric_tool, agent_factory, mock_project_client):
        """Test create_fabric_agent when properly configured"""
        # Setup mocks
        mock_settings.ENABLE_FABRIC_AGENT = True
        mock_settings.FABRIC_CONNECTION_ID = 'fabric-conn-123'
        mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
        
        mock_tool_instance = Mock()
        mock_tool_instance.definitions = ['fabric_tool_def']
        mock_fabric_tool.return_value = mock_tool_instance
        
        mock_agent = Mock(id='fabric-agent-456')
        mock_project_client.agents.create_agent.return_value = mock_agent
        
        result = agent_factory.create_fabric_agent()
        
        assert result == mock_agent
        mock_fabric_tool.assert_called_once_with(connection_id='fabric-conn-123')
        mock_project_client.agents.create_agent.assert_called_once_with(
            model='test-model',
            name='fabric-agent',
            instructions='You are a data analysis agent with access to Microsoft Fabric data sources.',
            tools=['fabric_tool_def']
        )
    
    @patch('services.agent_factory.BingGroundingTool')
    @patch('services.agent_factory.settings')
    def test_create_web_agent(self, mock_settings, mock_bing_tool, agent_factory, mock_project_client):
        """Test create_web_agent"""
        # Setup mocks
        mock_settings.BING_CONNECTION_ID = 'bing-conn-123'
        mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
        
        mock_tool_instance = Mock()
        mock_tool_instance.definitions = ['bing_tool_def']
        mock_bing_tool.return_value = mock_tool_instance
        
        mock_agent = Mock(id='web-agent-456')
        mock_project_client.agents.create_agent.return_value = mock_agent
        
        result = agent_factory.create_web_agent()
        
        assert result == mock_agent
        mock_bing_tool.assert_called_once_with(connection_id='bing-conn-123')
        mock_project_client.agents.create_agent.assert_called_once_with(
            model='test-model',
            name='web-agent',
            instructions='You are a web search agent that finds current information from the internet using Bing Search.',
            tools=['bing_tool_def']
        )
    
    @patch('services.agent_factory.Path')
    @patch('services.agent_factory.requests')
    @patch('services.agent_factory.FileSearchTool')
    @patch('services.agent_factory.FilePurpose')
    @patch('services.agent_factory.settings')
    def test_create_rag_agent(self, mock_settings, mock_file_purpose, mock_file_search_tool, 
                             mock_requests, mock_path, agent_factory, mock_project_client):
        """Test create_rag_agent"""
        # Setup mocks
        mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
        
        # Mock Path operations
        mock_data_dir = Mock()
        mock_file_path = Mock()
        mock_file_path.exists.return_value = False
        mock_data_dir.__truediv__.return_value = mock_file_path
        mock_path.return_value = mock_data_dir
        
        # Mock requests
        mock_response = Mock()
        mock_response.content = b'PDF content'
        mock_requests.get.return_value = mock_response
        
        # Mock file operations
        mock_file = Mock(id='file-123')
        mock_project_client.agents.files.upload_and_poll.return_value = mock_file
        
        # Mock vector store
        mock_vector_store = Mock(id='vs-456')
        mock_project_client.agents.vector_stores.create_and_poll.return_value = mock_vector_store
        
        # Mock file search tool
        mock_tool_instance = Mock()
        mock_tool_instance.definitions = ['file_search_def']
        mock_tool_instance.resources = {'file_search': 'resources'}
        mock_file_search_tool.return_value = mock_tool_instance
        
        # Mock agent
        mock_agent = Mock(id='rag-agent-789')
        mock_project_client.agents.create_agent.return_value = mock_agent
        
        result = agent_factory.create_rag_agent()
        
        assert isinstance(result, tuple)
        agent, cleanup_resources = result
        assert agent == mock_agent
        assert cleanup_resources['vector_store'] == mock_vector_store
        assert cleanup_resources['file'] == mock_file
        
        # Verify file download was attempted
        mock_requests.get.assert_called_once()
        
        # Verify file upload
        mock_project_client.agents.files.upload_and_poll.assert_called_once()
        
        # Verify vector store creation
        mock_project_client.agents.vector_stores.create_and_poll.assert_called_once()
    
    @patch('services.agent_factory.ConnectedAgentTool')
    @patch('services.agent_factory.FunctionTool') 
    @patch('services.agent_factory.settings')
    def test_create_routing_agent(self, mock_settings, mock_function_tool, mock_connected_tool,
                                 agent_factory, mock_project_client):
        """Test create_routing_agent"""
        # Setup mocks
        mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
        
        # Mock connected agents
        mock_agent1 = Mock(id='agent-1')
        mock_agent2 = Mock(id='agent-2')
        connected_agents = {
            'web_agent': mock_agent1,
            'rag_agent': mock_agent2
        }
        
        # Mock search and genie functions
        search_function = Mock()
        genie_function = Mock()
        
        # Mock function tool
        mock_function_tool_instance = Mock()
        mock_function_tool_instance.definitions = ['func_tool_def']
        mock_function_tool.return_value = mock_function_tool_instance
        
        # Mock connected agent tools
        mock_connected_tool_instance = Mock()
        mock_connected_tool_instance.definitions = [{'connected_agent_def': True}]
        mock_connected_tool.return_value = mock_connected_tool_instance
        
        # Mock routing agent
        mock_routing_agent = Mock(id='routing-agent-999')
        mock_project_client.agents.create_agent.return_value = mock_routing_agent
        
        result = agent_factory.create_routing_agent(connected_agents, search_function, genie_function)
        
        assert result == mock_routing_agent
        
        # Verify function tool was created with correct functions
        mock_function_tool.assert_called_once()
        call_args = mock_function_tool.call_args[1]
        assert search_function in call_args['functions']
        assert genie_function in call_args['functions']
        
        # Verify connected agent tools were created
        assert mock_connected_tool.call_count == 2
        
        # Verify routing agent was created
        mock_project_client.agents.create_agent.assert_called_once()
        create_call = mock_project_client.agents.create_agent.call_args[1]
        assert create_call['model'] == 'test-model'
        assert create_call['name'] == 'purview_routing_agent'
        assert 'routing agent for Microsoft Purview' in create_call['instructions']
    
    @patch('services.agent_factory.Path')
    def test_create_rag_agent_file_exists(self, mock_path, agent_factory, mock_project_client):
        """Test create_rag_agent when file already exists"""
        # Mock Path operations - file exists
        mock_data_dir = Mock()
        mock_file_path = Mock()
        mock_file_path.exists.return_value = True  # File exists
        mock_data_dir.__truediv__.return_value = mock_file_path
        mock_path.return_value = mock_data_dir
        
        # Mock other operations
        mock_file = Mock(id='file-existing')
        mock_project_client.agents.files.upload_and_poll.return_value = mock_file
        
        mock_vector_store = Mock(id='vs-existing')
        mock_project_client.agents.vector_stores.create_and_poll.return_value = mock_vector_store
        
        mock_agent = Mock(id='rag-agent-existing')
        mock_project_client.agents.create_agent.return_value = mock_agent
        
        with patch('services.agent_factory.FileSearchTool') as mock_file_search_tool, \
             patch('services.agent_factory.requests') as mock_requests:
            
            mock_tool_instance = Mock()
            mock_tool_instance.definitions = ['file_search_def']
            mock_tool_instance.resources = {'file_search': 'resources'}
            mock_file_search_tool.return_value = mock_tool_instance
            
            agent, cleanup_resources = agent_factory.create_rag_agent()
            
            # Verify requests.get was NOT called since file exists
            mock_requests.get.assert_not_called()
            
            # Verify other operations still occurred
            assert agent == mock_agent
            assert cleanup_resources['file'] == mock_file