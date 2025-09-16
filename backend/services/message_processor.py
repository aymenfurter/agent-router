from typing import Dict, List, Any
from azure.ai.projects import AIProjectClient
from backend.utils.logging_config import get_logger

class MessageProcessor:
    def __init__(self, project_client: AIProjectClient):
        self.logger = get_logger(__name__)
        self.project_client = project_client
    
    def extract_message_with_annotations(self, message) -> Dict[str, Any]:
        annotations = []
        content = ""
        
        if hasattr(message, 'content') and message.content:
            content = message.content[0].text.value if message.content[0].text else ""
        
        if hasattr(message, 'file_citation_annotations'):
            annotations.extend(self._process_file_citations(message.file_citation_annotations))
        
        if hasattr(message, 'url_citation_annotations'):
            annotations.extend(self._process_url_citations(message.url_citation_annotations))
        
        return {"content": content, "annotations": annotations}
    
    def _process_file_citations(self, file_citations: List) -> List[Dict[str, Any]]:
        annotations = []
        for annotation in file_citations:
            file_id = annotation.file_citation.file_id
            file_info = self.project_client.agents.files.get(file_id)
            annotations.append({
                "type": "file_citation",
                "text": annotation.text,
                "start_index": annotation.start_index,
                "end_index": annotation.end_index,
                "file_id": file_id,
                "file_name": file_info.filename,
                "quote": annotation.file_citation.quote
            })
        return annotations
    
    def _process_url_citations(self, url_citations: List) -> List[Dict[str, Any]]:
        return [{
            "type": "url_citation", 
            "text": annotation.text,
            "start_index": annotation.start_index,
            "end_index": annotation.end_index,
            "url": annotation.url_citation.url,
            "title": annotation.url_citation.title
        } for annotation in url_citations]
    
    def format_thread_messages(self, messages: List, thread_id: str) -> List[Dict[str, Any]]:
        formatted_messages = []
        for message in reversed(messages):
            message_data = self.extract_message_with_annotations(message)
            formatted_messages.append({
                "id": message.id,
                "role": message.role,
                "content": message_data["content"],
                "annotations": message_data["annotations"],
                "created_at": message.created_at,
                "thread_id": thread_id
            })
        return formatted_messages
