import pytest
from unittest.mock import Mock, patch
from services.message_processor import MessageProcessor


class TestMessageProcessor:
    """Test cases for the MessageProcessor class"""
    
    @pytest.fixture
    def mock_project_client(self):
        """Create a mock AIProjectClient"""
        return Mock()
    
    @pytest.fixture
    def message_processor(self, mock_project_client):
        """Create MessageProcessor instance with mocked client"""
        return MessageProcessor(mock_project_client)
    
    def test_init(self, mock_project_client):
        """Test MessageProcessor initialization"""
        processor = MessageProcessor(mock_project_client)
        assert processor.project_client == mock_project_client
        assert processor.logger is not None
    
    def test_extract_message_with_annotations_basic_message(self, message_processor):
        """Test extracting message with basic content and no annotations"""
        # Mock message with text content
        mock_message = Mock()
        mock_text_content = Mock()
        mock_text_content.text.value = "Test message content"
        mock_message.content = [mock_text_content]
        mock_message.file_citation_annotations = []
        mock_message.url_citation_annotations = []
        
        result = message_processor.extract_message_with_annotations(mock_message)
        
        assert result["content"] == "Test message content"
        assert result["annotations"] == []
    
    def test_extract_message_with_annotations_no_content(self, message_processor):
        """Test extracting message with no content"""
        mock_message = Mock()
        mock_message.content = []
        mock_message.file_citation_annotations = []
        mock_message.url_citation_annotations = []
        
        result = message_processor.extract_message_with_annotations(mock_message)
        
        assert result["content"] == ""
        assert result["annotations"] == []
    
    def test_extract_message_with_annotations_none_content(self, message_processor):
        """Test extracting message with None content"""
        mock_message = Mock()
        mock_message.content = None
        mock_message.file_citation_annotations = []
        mock_message.url_citation_annotations = []
        
        result = message_processor.extract_message_with_annotations(mock_message)
        
        assert result["content"] == ""
        assert result["annotations"] == []
    
    def test_extract_message_with_file_citations(self, message_processor, mock_project_client):
        """Test extracting message with file citations"""
        # Setup mock file citation
        mock_file_citation = Mock()
        mock_file_citation.file_citation.file_id = "file-123"
        mock_file_citation.file_citation.quote = "quoted text"
        mock_file_citation.text = "citation text"
        mock_file_citation.start_index = 10
        mock_file_citation.end_index = 25
        
        # Setup mock file info
        mock_file_info = Mock()
        mock_file_info.filename = "test_document.pdf"
        mock_project_client.agents.files.get.return_value = mock_file_info
        
        # Setup mock message
        mock_message = Mock()
        mock_text_content = Mock()
        mock_text_content.text.value = "Test message with file citation"
        mock_message.content = [mock_text_content]
        mock_message.file_citation_annotations = [mock_file_citation]
        mock_message.url_citation_annotations = []
        
        result = message_processor.extract_message_with_annotations(mock_message)
        
        assert result["content"] == "Test message with file citation"
        assert len(result["annotations"]) == 1
        
        annotation = result["annotations"][0]
        assert annotation["type"] == "file_citation"
        assert annotation["text"] == "citation text"
        assert annotation["start_index"] == 10
        assert annotation["end_index"] == 25
        assert annotation["file_id"] == "file-123"
        assert annotation["file_name"] == "test_document.pdf"
        assert annotation["quote"] == "quoted text"
        
        mock_project_client.agents.files.get.assert_called_once_with("file-123")
    
    def test_extract_message_with_url_citations(self, message_processor):
        """Test extracting message with URL citations"""
        # Setup mock URL citation
        mock_url_citation = Mock()
        mock_url_citation.url_citation.url = "https://example.com"
        mock_url_citation.url_citation.title = "Example Website"
        mock_url_citation.text = "citation text"
        mock_url_citation.start_index = 15
        mock_url_citation.end_index = 30
        
        # Setup mock message
        mock_message = Mock()
        mock_text_content = Mock()
        mock_text_content.text.value = "Test message with URL citation"
        mock_message.content = [mock_text_content]
        mock_message.file_citation_annotations = []
        mock_message.url_citation_annotations = [mock_url_citation]
        
        result = message_processor.extract_message_with_annotations(mock_message)
        
        assert result["content"] == "Test message with URL citation"
        assert len(result["annotations"]) == 1
        
        annotation = result["annotations"][0]
        assert annotation["type"] == "url_citation"
        assert annotation["text"] == "citation text"
        assert annotation["start_index"] == 15
        assert annotation["end_index"] == 30
        assert annotation["url"] == "https://example.com"
        assert annotation["title"] == "Example Website"
    
    def test_extract_message_with_mixed_citations(self, message_processor, mock_project_client):
        """Test extracting message with both file and URL citations"""
        # Setup mock file citation
        mock_file_citation = Mock()
        mock_file_citation.file_citation.file_id = "file-456"
        mock_file_citation.file_citation.quote = "file quote"
        mock_file_citation.text = "file citation"
        mock_file_citation.start_index = 5
        mock_file_citation.end_index = 15
        
        # Setup mock URL citation
        mock_url_citation = Mock()
        mock_url_citation.url_citation.url = "https://test.com"
        mock_url_citation.url_citation.title = "Test Site"
        mock_url_citation.text = "url citation"
        mock_url_citation.start_index = 20
        mock_url_citation.end_index = 35
        
        # Setup mock file info
        mock_file_info = Mock()
        mock_file_info.filename = "mixed_doc.pdf"
        mock_project_client.agents.files.get.return_value = mock_file_info
        
        # Setup mock message
        mock_message = Mock()
        mock_text_content = Mock()
        mock_text_content.text.value = "Message with mixed citations"
        mock_message.content = [mock_text_content]
        mock_message.file_citation_annotations = [mock_file_citation]
        mock_message.url_citation_annotations = [mock_url_citation]
        
        result = message_processor.extract_message_with_annotations(mock_message)
        
        assert result["content"] == "Message with mixed citations"
        assert len(result["annotations"]) == 2
        
        # Check file citation
        file_annotation = next(a for a in result["annotations"] if a["type"] == "file_citation")
        assert file_annotation["file_id"] == "file-456"
        assert file_annotation["file_name"] == "mixed_doc.pdf"
        
        # Check URL citation
        url_annotation = next(a for a in result["annotations"] if a["type"] == "url_citation")
        assert url_annotation["url"] == "https://test.com"
        assert url_annotation["title"] == "Test Site"
    
    def test_format_thread_messages_empty_list(self, message_processor):
        """Test formatting empty message list"""
        result = message_processor.format_thread_messages([], "thread-123")
        assert result == []
    
    def test_format_thread_messages_single_message(self, message_processor):
        """Test formatting single message"""
        mock_message = Mock()
        mock_message.id = "msg-123"
        mock_message.role = "user"
        mock_message.created_at = "2024-01-01T10:00:00Z"
        
        # Setup content
        mock_text_content = Mock()
        mock_text_content.text.value = "Hello, assistant!"
        mock_message.content = [mock_text_content]
        mock_message.file_citation_annotations = []
        mock_message.url_citation_annotations = []
        
        result = message_processor.format_thread_messages([mock_message], "thread-456")
        
        assert len(result) == 1
        formatted_msg = result[0]
        assert formatted_msg["id"] == "msg-123"
        assert formatted_msg["role"] == "user"
        assert formatted_msg["content"] == "Hello, assistant!"
        assert formatted_msg["annotations"] == []
        assert formatted_msg["created_at"] == "2024-01-01T10:00:00Z"
        assert formatted_msg["thread_id"] == "thread-456"
    
    def test_format_thread_messages_multiple_messages(self, message_processor):
        """Test formatting multiple messages in reverse order"""
        # Create mock messages
        mock_msg1 = Mock()
        mock_msg1.id = "msg-1"
        mock_msg1.role = "user"
        mock_msg1.created_at = "2024-01-01T10:00:00Z"
        mock_text1 = Mock()
        mock_text1.text.value = "First message"
        mock_msg1.content = [mock_text1]
        mock_msg1.file_citation_annotations = []
        mock_msg1.url_citation_annotations = []
        
        mock_msg2 = Mock()
        mock_msg2.id = "msg-2"
        mock_msg2.role = "assistant"
        mock_msg2.created_at = "2024-01-01T10:01:00Z"
        mock_text2 = Mock()
        mock_text2.text.value = "Second message"
        mock_msg2.content = [mock_text2]
        mock_msg2.file_citation_annotations = []
        mock_msg2.url_citation_annotations = []
        
        # Messages are passed in order, but should be reversed in output
        result = message_processor.format_thread_messages([mock_msg1, mock_msg2], "thread-789")
        
        assert len(result) == 2
        # First in result should be msg-2 (reversed)
        assert result[0]["id"] == "msg-2"
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "Second message"
        
        # Second in result should be msg-1 (reversed)
        assert result[1]["id"] == "msg-1"
        assert result[1]["role"] == "user"
        assert result[1]["content"] == "First message"
    
    def test_process_file_citations_multiple_files(self, message_processor, mock_project_client):
        """Test processing multiple file citations"""
        # Setup mock file citations
        mock_citation1 = Mock()
        mock_citation1.file_citation.file_id = "file-1"
        mock_citation1.file_citation.quote = "quote 1"
        mock_citation1.text = "citation 1"
        mock_citation1.start_index = 0
        mock_citation1.end_index = 10
        
        mock_citation2 = Mock()
        mock_citation2.file_citation.file_id = "file-2"
        mock_citation2.file_citation.quote = "quote 2"
        mock_citation2.text = "citation 2"
        mock_citation2.start_index = 15
        mock_citation2.end_index = 25
        
        # Setup mock file info responses
        mock_file1 = Mock()
        mock_file1.filename = "doc1.pdf"
        mock_file2 = Mock()
        mock_file2.filename = "doc2.pdf"
        
        mock_project_client.agents.files.get.side_effect = [mock_file1, mock_file2]
        
        result = message_processor._process_file_citations([mock_citation1, mock_citation2])
        
        assert len(result) == 2
        assert result[0]["file_id"] == "file-1"
        assert result[0]["file_name"] == "doc1.pdf"
        assert result[1]["file_id"] == "file-2"
        assert result[1]["file_name"] == "doc2.pdf"
    
    def test_process_url_citations_multiple_urls(self, message_processor):
        """Test processing multiple URL citations"""
        mock_citation1 = Mock()
        mock_citation1.url_citation.url = "https://site1.com"
        mock_citation1.url_citation.title = "Site 1"
        mock_citation1.text = "url 1"
        mock_citation1.start_index = 5
        mock_citation1.end_index = 15
        
        mock_citation2 = Mock()
        mock_citation2.url_citation.url = "https://site2.com"
        mock_citation2.url_citation.title = "Site 2"
        mock_citation2.text = "url 2"
        mock_citation2.start_index = 20
        mock_citation2.end_index = 30
        
        result = message_processor._process_url_citations([mock_citation1, mock_citation2])
        
        assert len(result) == 2
        assert result[0]["url"] == "https://site1.com"
        assert result[0]["title"] == "Site 1"
        assert result[1]["url"] == "https://site2.com"
        assert result[1]["title"] == "Site 2"