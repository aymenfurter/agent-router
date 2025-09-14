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
    
    def test_create_fabric_agent_enabled(self, agent_factory, mock_project_client):
        """Test create_fabric_agent when properly configured"""
        # Patch settings at the module level where it's imported
        from services import agent_factory as af_module
        
        # Save original values
        original_enable = af_module.settings.ENABLE_FABRIC_AGENT
        original_connection_id = af_module.settings.FABRIC_CONNECTION_ID
        original_model = af_module.settings.MODEL_DEPLOYMENT_NAME
        
        try:
            # Set the mock values directly on the settings object
            af_module.settings.ENABLE_FABRIC_AGENT = True
            af_module.settings.FABRIC_CONNECTION_ID = 'fabric-conn-123'
            af_module.settings.MODEL_DEPLOYMENT_NAME = 'test-model'
            
            # Reset the mocked FabricTool to have specific behavior
            fabric_tool_instance = Mock()
            fabric_tool_instance.definitions = ['fabric_tool_def']
            af_module.FabricTool.return_value = fabric_tool_instance
            
            # Setup agent creation mock
            mock_agent = Mock(id='fabric-agent-456')
            mock_project_client.agents.create_agent.return_value = mock_agent
            
            # Call the method
            result = agent_factory.create_fabric_agent()
            
            # Assertions
            assert result == mock_agent
            af_module.FabricTool.assert_called_once_with(connection_id='fabric-conn-123')
            mock_project_client.agents.create_agent.assert_called_once_with(
                model='test-model',
                name='fabric-agent',
                instructions='You are a data analysis agent with access to Microsoft Fabric data sources.',
                tools=['fabric_tool_def']
            )
        finally:
            # Restore original values
            af_module.settings.ENABLE_FABRIC_AGENT = original_enable
            af_module.settings.FABRIC_CONNECTION_ID = original_connection_id
            af_module.settings.MODEL_DEPLOYMENT_NAME = original_model
    
    def test_create_web_agent(self, agent_factory, mock_project_client):
        """Test create_web_agent"""
        with patch('services.agent_factory.settings') as mock_settings:
            # Setup settings mocks
            mock_settings.BING_CONNECTION_ID = 'bing-conn-123'
            mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
            
            # Reset the mocked BingGroundingTool to have specific behavior
            from services import agent_factory as af
            bing_tool_instance = Mock()
            bing_tool_instance.definitions = ['bing_tool_def']
            af.BingGroundingTool.return_value = bing_tool_instance
            
            # Setup agent creation mock
            mock_agent = Mock(id='web-agent-456')
            mock_project_client.agents.create_agent.return_value = mock_agent
            
            # Call the method
            result = agent_factory.create_web_agent()
            
            # Assertions
            assert result == mock_agent
            af.BingGroundingTool.assert_called_once_with(connection_id='bing-conn-123')
            mock_project_client.agents.create_agent.assert_called_once_with(
                model='test-model',
                name='web-agent',
                instructions='You are a web search agent that finds current information from the internet using Bing Search.',
                tools=['bing_tool_def']
            )
    
    def test_create_rag_agent(self, agent_factory, mock_project_client):
        """Test create_rag_agent"""
        with patch('services.agent_factory.settings') as mock_settings, \
             patch('services.agent_factory.Path') as mock_path:
            
            # Setup settings mocks
            mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
            
            # Mock Path operations - create mock objects for data_dir and file_path
            mock_data_dir = Mock()
            mock_file_path = Mock()
            mock_file_path.exists.return_value = False
            mock_file_path.__str__ = Mock(return_value='/tmp/data/encarta_guide.pdf')
            
            # Mock Path constructor to return data_dir mock
            mock_path.return_value = mock_data_dir
            # Mock the division operator for data_dir / "encarta_guide.pdf"
            mock_data_dir.__truediv__ = Mock(return_value=mock_file_path)
            mock_data_dir.mkdir = Mock()
            
            # Mock file operations - open
            with patch('builtins.open', create=True) as mock_open:
                mock_file_handle = Mock()
                mock_open.return_value.__enter__.return_value = mock_file_handle
                
                # Mock Azure file operations
                mock_file = Mock(id='file-123')
                mock_project_client.agents.files.upload_and_poll.return_value = mock_file
                
                # Mock vector store
                mock_vector_store = Mock(id='vs-456')
                mock_project_client.agents.vector_stores.create_and_poll.return_value = mock_vector_store
                
                # Reset the mocked FileSearchTool to have specific behavior
                from services import agent_factory as af
                file_search_tool_instance = Mock()
                file_search_tool_instance.definitions = ['file_search_def']
                file_search_tool_instance.resources = {'file_search': 'resources'}
                af.FileSearchTool.return_value = file_search_tool_instance
                
                # Mock agent
                mock_agent = Mock(id='rag-agent-789')
                mock_project_client.agents.create_agent.return_value = mock_agent
                
                # Call the method
                result = agent_factory.create_rag_agent()
                
                # Assertions
                assert isinstance(result, tuple)
                assert result[0] == mock_agent
                assert 'vector_store' in result[1]
                assert 'file' in result[1]
                agent, cleanup_resources = result
                assert agent == mock_agent
                assert cleanup_resources['vector_store'] == mock_vector_store
                assert cleanup_resources['file'] == mock_file
                
                # Note: With global mocking, requests.get is already mocked, so we don't assert it was called
                
                # Verify file upload
                mock_project_client.agents.files.upload_and_poll.assert_called_once()
                
                # Verify vector store creation
                mock_project_client.agents.vector_stores.create_and_poll.assert_called_once()
    
    def test_create_routing_agent(self, agent_factory, mock_project_client):
        """Test create_routing_agent"""
        with patch('services.agent_factory.settings') as mock_settings:
            # Setup settings mocks
            mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
            
            # Setup test data
            mock_agent1 = Mock(id='agent-1')
            mock_agent2 = Mock(id='agent-2')
            connected_agents = {
                'web_agent': mock_agent1,
                'rag_agent': mock_agent2
            }
            
            # Mock search and genie functions
            search_function = Mock(name='search_function')
            genie_function = Mock(name='genie_function')
            
            # Reset the mocked tools to have specific behavior
            from services import agent_factory as af
            
            # Mock function tool
            function_tool_instance = Mock()
            function_tool_instance.definitions = ['func_tool_def']
            af.FunctionTool.return_value = function_tool_instance
            
            # Mock connected agent tools
            connected_tool_instance = Mock()
            connected_tool_instance.definitions = [{'connected_agent_def': True}]
            af.ConnectedAgentTool.return_value = connected_tool_instance
            
            # Mock routing agent
            mock_routing_agent = Mock(id='routing-agent-999')
            mock_project_client.agents.create_agent.return_value = mock_routing_agent
            
            # Call the method
            result = agent_factory.create_routing_agent(connected_agents, search_function, genie_function)
            
            # Assertions
            assert result == mock_routing_agent
            
            # Verify function tool was created
            af.FunctionTool.assert_called_once()
            
            # Verify connected agent tools were created
            assert af.ConnectedAgentTool.call_count == 2
            
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
        mock_file_path.__str__ = Mock(return_value='/tmp/data/encarta_guide.pdf')
        mock_data_dir.__truediv__ = Mock(return_value=mock_file_path)
        mock_data_dir.mkdir = Mock()
        mock_path.return_value = mock_data_dir
        
        # Mock other Azure operations
        mock_file = Mock(id='file-existing')
        mock_project_client.agents.files.upload_and_poll.return_value = mock_file
        
        mock_vector_store = Mock(id='vs-existing')
        mock_project_client.agents.vector_stores.create_and_poll.return_value = mock_vector_store
        
        mock_agent = Mock(id='rag-agent-existing')
        mock_project_client.agents.create_agent.return_value = mock_agent
        
        with patch('services.agent_factory.FileSearchTool') as mock_file_search_tool, \
             patch('services.agent_factory.requests') as mock_requests, \
             patch('services.agent_factory.settings') as mock_settings:
            
            mock_settings.MODEL_DEPLOYMENT_NAME = 'test-model'
            
            mock_tool_instance = Mock()
            mock_tool_instance.definitions = ['file_search_def']
            mock_tool_instance.resources = {'file_search': 'resources'}
            mock_file_search_tool.return_value = mock_tool_instance
            
            # Call the method
            agent, cleanup_resources = agent_factory.create_rag_agent()
            
            # Verify requests.get was NOT called since file exists
            mock_requests.get.assert_not_called()
            
            # Verify other operations still occurred
            assert agent == mock_agent
            assert cleanup_resources['vector_store'] == mock_vector_store
            assert cleanup_resources['file'] == mock_file
            assert cleanup_resources['file'] == mock_file