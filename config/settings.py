import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.AZURE_AI_AGENT_ENDPOINT = os.getenv('AZURE_AI_AGENT_ENDPOINT')
        self.MODEL_DEPLOYMENT_NAME = os.getenv('MODEL_DEPLOYMENT_NAME')
        self.PURVIEW_ENDPOINT = os.getenv('PURVIEW_ENDPOINT')
        self.BING_CONNECTION_ID = os.getenv('BING_CONNECTION_ID')
        self.FABRIC_CONNECTION_ID = os.getenv('FABRIC_CONNECTION_ID')
        self.ENABLE_FABRIC_AGENT = os.getenv('ENABLE_FABRIC_AGENT', 'false').lower() == 'true'
        self.DATABRICKS_INSTANCE = os.getenv('DATABRICKS_INSTANCE')
        self.GENIE_SPACE_ID = os.getenv('GENIE_SPACE_ID')
        self.DATABRICKS_AUTH_TOKEN = os.getenv('DATABRICKS_AUTH_TOKEN')
        self.FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
        self.FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    def get_required_vars(self) -> List[str]:
        required = ['AZURE_AI_AGENT_ENDPOINT', 'MODEL_DEPLOYMENT_NAME', 'BING_CONNECTION_ID', 'PURVIEW_ENDPOINT']
        if self.ENABLE_FABRIC_AGENT:
            required.append('FABRIC_CONNECTION_ID')
        return required
    
    def validate(self) -> Dict[str, Any]:
        missing_vars = [var for var in self.get_required_vars() if not getattr(self, var)]
        return {
            'valid': len(missing_vars) == 0,
            'missing_variables': missing_vars,
            'fabric_enabled': self.ENABLE_FABRIC_AGENT,
            'genie_configured': all([self.DATABRICKS_INSTANCE, self.GENIE_SPACE_ID, self.DATABRICKS_AUTH_TOKEN])
        }

settings = Settings()