import pytest
import json
import os
from unittest.mock import patch, Mock, MagicMock
import responses

# Mock dotenv before importing
with patch.dict('sys.modules', {'dotenv': MagicMock()}):
    from services.genie_agent_service import GenieAgentService


class TestGenieAgentService:
    """Test cases for the GenieAgentService class"""
    
    @pytest.fixture
    def genie_service(self):
        """Create GenieAgentService instance"""
        with patch('services.genie_agent_service.load_dotenv'):
            return GenieAgentService()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_is_configured_false_when_missing_vars(self, genie_service):
        """Test is_configured returns False when required vars are missing"""
        with patch('services.genie_agent_service.load_dotenv'):
            service = GenieAgentService()
            assert service.is_configured() is False
    
    @patch.dict(os.environ, {
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token'
    })
    def test_is_configured_true_when_all_vars_present(self):
        """Test is_configured returns True when all required vars are present"""
        with patch('services.genie_agent_service.load_dotenv'):
            service = GenieAgentService()
            assert service.is_configured() is True
    
    def test_handoff_genie_agent_not_configured(self, genie_service):
        """Test handoff_genie_agent when service is not configured"""
        genie_service.databricks_instance = None
        genie_service.genie_space_id = None  
        genie_service.auth_token = None
        
        result = genie_service.handoff_genie_agent("test query")
        result_data = json.loads(result)
        
        assert result_data["status"] == "error"
        assert result_data["message"] == "Missing Genie configuration"
    
    @responses.activate
    @patch.dict(os.environ, {
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token'
    })
    def test_handoff_genie_agent_successful_conversation(self):
        """Test successful Genie conversation flow"""
        with patch('services.genie_agent_service.load_dotenv'):
            service = GenieAgentService()
            
            # Mock start conversation response
            start_response = {
                'conversation': {'id': 'conv-123'},
                'message': {'id': 'msg-456'}
            }
            responses.add(
                responses.POST,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/start-conversation',
                json=start_response,
                status=200
            )
            
            # Mock status response - completed
            status_response = {
                'status': 'COMPLETED',
                'attachments': [
                    {
                        'text': {
                            'content': 'Here is your analysis result'
                        }
                    }
                ]
            }
            responses.add(
                responses.GET,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/conversations/conv-123/messages/msg-456',
                json=status_response,
                status=200
            )
            
            result = service.handoff_genie_agent("analyze sales data")
            result_data = json.loads(result)
            
            assert result_data["status"] == "success"
            assert result_data["response"] == "Here is your analysis result"
            assert result_data["conversation_id"] == "conv-123"
            assert result_data["message_id"] == "msg-456"
    
    @responses.activate
    @patch.dict(os.environ, {
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token'
    })
    def test_handoff_genie_agent_with_sql_query(self):
        """Test Genie conversation with SQL query generation"""
        with patch('services.genie_agent_service.load_dotenv'):
            service = GenieAgentService()
            
            # Mock start conversation response
            start_response = {
                'conversation': {'id': 'conv-789'},
                'message': {'id': 'msg-101'}
            }
            responses.add(
                responses.POST,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/start-conversation',
                json=start_response,
                status=200
            )
            
            # Mock status response with query attachment
            status_response = {
                'status': 'COMPLETED',
                'attachments': [
                    {
                        'query': {
                            'query': 'SELECT * FROM sales WHERE date > 2024-01-01',
                            'description': 'Sales data for 2024',
                            'query_result_metadata': {'row_count': 150}
                        },
                        'attachment_id': 'attach-123'
                    }
                ]
            }
            responses.add(
                responses.GET,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/conversations/conv-789/messages/msg-101',
                json=status_response,
                status=200
            )
            
            # Mock query results
            query_results = {
                'statement_response': {
                    'result': {
                        'data_array': [
                            ['2024-01-01', 'Product A', 100],
                            ['2024-01-02', 'Product B', 200]
                        ],
                        'schema': {
                            'columns': [
                                {'name': 'date'},
                                {'name': 'product'},
                                {'name': 'amount'}
                            ]
                        }
                    }
                }
            }
            responses.add(
                responses.GET,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/conversations/conv-789/messages/msg-101/query-result/attach-123',
                json=query_results,
                status=200
            )
            
            result = service.handoff_genie_agent("show me sales data")
            result_data = json.loads(result)
            
            assert result_data["status"] == "success"
            assert "Sales data for 2024" in result_data["response"]
            assert "SELECT * FROM sales WHERE date > 2024-01-01" in result_data["response"]
            assert "Total rows: 150" in result_data["response"]
            assert "First 10 rows:" in result_data["response"]
            assert "date | product | amount" in result_data["response"]
            assert result_data["generated_query"] == "SELECT * FROM sales WHERE date > 2024-01-01"
            assert result_data["row_count"] == 150
    
    @responses.activate
    @patch.dict(os.environ, {
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token'
    })
    def test_handoff_genie_agent_failed_status(self):
        """Test Genie conversation when query fails"""
        with patch('services.genie_agent_service.load_dotenv'):
            service = GenieAgentService()
            
            # Mock start conversation response
            start_response = {
                'conversation': {'id': 'conv-fail'},
                'message': {'id': 'msg-fail'}
            }
            responses.add(
                responses.POST,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/start-conversation',
                json=start_response,
                status=200
            )
            
            # Mock status response - failed
            status_response = {
                'status': 'FAILED',
                'attachments': []
            }
            responses.add(
                responses.GET,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/conversations/conv-fail/messages/msg-fail',
                json=status_response,
                status=200
            )
            
            result = service.handoff_genie_agent("bad query")
            result_data = json.loads(result)
            
            assert result_data["status"] == "error"
            assert "Genie query failed with status: FAILED" in result_data["message"]
    
    @responses.activate
    @patch.dict(os.environ, {
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token'
    })
    def test_handoff_genie_agent_timeout_status(self):
        """Test Genie conversation timeout scenario"""
        with patch('services.genie_agent_service.load_dotenv'), \
             patch('time.sleep'):  # Speed up the test
            service = GenieAgentService()
            
            # Mock start conversation response
            start_response = {
                'conversation': {'id': 'conv-timeout'},
                'message': {'id': 'msg-timeout'}
            }
            responses.add(
                responses.POST,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/start-conversation',
                json=start_response,
                status=200
            )
            
            # Mock status response - always in progress (never completes)
            status_response = {
                'status': 'IN_PROGRESS',
                'attachments': []
            }
            responses.add(
                responses.GET,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/conversations/conv-timeout/messages/msg-timeout',
                json=status_response,
                status=200
            )
            
            result = service.handoff_genie_agent("slow query")
            result_data = json.loads(result)
            
            assert result_data["status"] == "error"
            assert "Genie query failed with status: IN_PROGRESS" in result_data["message"]
    
    @responses.activate 
    @patch.dict(os.environ, {
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token'
    })
    def test_handoff_genie_agent_no_response(self):
        """Test handling when no meaningful response is generated"""
        with patch('services.genie_agent_service.load_dotenv'):
            service = GenieAgentService()
            
            # Mock start conversation response
            start_response = {
                'conversation': {'id': 'conv-empty'},
                'message': {'id': 'msg-empty'}
            }
            responses.add(
                responses.POST,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/start-conversation',
                json=start_response,
                status=200
            )
            
            # Mock status response with empty attachments
            status_response = {
                'status': 'COMPLETED',
                'attachments': []
            }
            responses.add(
                responses.GET,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/conversations/conv-empty/messages/msg-empty',
                json=status_response,
                status=200
            )
            
            result = service.handoff_genie_agent("empty query")
            result_data = json.loads(result)
            
            assert result_data["status"] == "success"
            assert result_data["response"] == "No response generated"
    
    @responses.activate
    @patch.dict(os.environ, {
        'DATABRICKS_INSTANCE': 'test.databricks.com',
        'GENIE_SPACE_ID': 'test-space-id',
        'DATABRICKS_AUTH_TOKEN': 'test-token'
    })
    def test_handoff_genie_agent_request_headers(self):
        """Test that proper headers are sent with requests"""
        with patch('services.genie_agent_service.load_dotenv'):
            service = GenieAgentService()
            
            # Mock start conversation response
            start_response = {
                'conversation': {'id': 'conv-123'},
                'message': {'id': 'msg-456'}
            }
            
            def request_callback(request):
                # Verify headers
                assert request.headers['Authorization'] == 'Bearer test-token'
                assert request.headers['Content-Type'] == 'application/json'
                return (200, {}, json.dumps(start_response))
            
            responses.add_callback(
                responses.POST,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/start-conversation',
                callback=request_callback,
                content_type='application/json'
            )
            
            # Mock status response
            responses.add(
                responses.GET,
                'https://test.databricks.com/api/2.0/genie/spaces/test-space-id/conversations/conv-123/messages/msg-456',
                json={'status': 'COMPLETED', 'attachments': []},
                status=200
            )
            
            service.handoff_genie_agent("test query")