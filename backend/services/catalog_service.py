import json
import requests
import re
from typing import Dict, Any, Optional
from azure.identity import AzureCliCredential
from backend.utils.logging_config import get_logger
from backend.config.settings import settings

class CatalogService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.contacts = {
            "c53c736b-8469-409c-9dcc-b3a61953d4dd": "Aymen Furter (aymen.furter@microsoft.com)"
        }
    
    def parse_agent_from_description(self, description: str) -> Optional[str]:
        match = re.search(r'agent:\s*(\w+)', description, re.IGNORECASE) if description else None
        return match.group(1) if match else None
    
    def search_catalog(self, query: str) -> Dict[str, Any]:
        token = AzureCliCredential().get_token("https://purview.azure.net/.default")
        
        search_response = requests.post(
            f"{settings.PURVIEW_ENDPOINT}/datamap/api/search/query?api-version=2023-09-01",
            json={
                "limit": 10, 
                "keywords": query, 
                "filter": {
                    "or": [
                        {"entityType": "azure_storage_account"}, 
                        {"entityType": "fabric_lakehouse"},
                        {"entityType": "databricks_schema"}
                    ]
                }
            },
            headers={"Authorization": f"Bearer {token.token}"}
        )
        
        search_response.raise_for_status()

        results = []
        for asset in search_response.json().get('value', []):
            description = asset.get('userDescription', 'No description')
            agent_name = self.parse_agent_from_description(description)
            contact_id = asset.get('contact', [{}])[0].get('id') if asset.get('contact') else None
            
            results.append({
                "name": asset['displayText'],
                "description": description,
                "asset_id": asset['id'],
                "connected_agent": agent_name,
                "contact": self.contacts.get(contact_id) if contact_id else None
            })
        
        return {
            "status": "success", 
            "assets_found": len(results), 
            "results": results
        }

catalog_service = CatalogService()
