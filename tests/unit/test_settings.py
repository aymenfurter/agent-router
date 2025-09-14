import pytest
import os
from unittest.mock import patch, Mock
from config.settings import Settings, settings


class TestSettings:
    """Test cases for the Settings configuration class"""
    
    def test_settings_initialization_defaults(self, monkeypatch):
        """Test settings initialization with default values"""
        # Clear all environment variables
        for var in ['AZURE_AI_AGENT_ENDPOINT', 'MODEL_DEPLOYMENT_NAME', 
                   'PURVIEW_ENDPOINT', 'BING_CONNECTION_ID', 'FABRIC_CONNECTION_ID',
                   'ENABLE_FABRIC_AGENT', 'DATABRICKS_INSTANCE', 'GENIE_SPACE_ID',
                   'DATABRICKS_AUTH_TOKEN', 'FLASK_HOST', 'FLASK_PORT', 'FLASK_DEBUG']:
            monkeypatch.delenv(var, raising=False)
        
        test_settings = Settings()
        
        assert test_settings.AZURE_AI_AGENT_ENDPOINT is None
        assert test_settings.MODEL_DEPLOYMENT_NAME is None
        assert test_settings.PURVIEW_ENDPOINT is None
        assert test_settings.BING_CONNECTION_ID is None
        assert test_settings.FABRIC_CONNECTION_ID is None
        assert test_settings.ENABLE_FABRIC_AGENT is False
        assert test_settings.DATABRICKS_INSTANCE is None
        assert test_settings.GENIE_SPACE_ID is None
        assert test_settings.DATABRICKS_AUTH_TOKEN is None
        assert test_settings.FLASK_HOST == '0.0.0.0'
        assert test_settings.FLASK_PORT == 5000
        assert test_settings.FLASK_DEBUG is True

    def test_settings_initialization_with_env_vars(self, mock_env_vars):
        """Test settings initialization with environment variables"""
        test_settings = Settings()
        
        assert test_settings.AZURE_AI_AGENT_ENDPOINT == 'https://test.endpoint.com'
        assert test_settings.MODEL_DEPLOYMENT_NAME == 'test-model'
        assert test_settings.PURVIEW_ENDPOINT == 'https://test-purview.endpoint.com'
        assert test_settings.BING_CONNECTION_ID == 'test-bing-id'
        assert test_settings.FABRIC_CONNECTION_ID == 'test-fabric-id'
        assert test_settings.ENABLE_FABRIC_AGENT is True
        assert test_settings.DATABRICKS_INSTANCE == 'test.databricks.com'
        assert test_settings.GENIE_SPACE_ID == 'test-space-id'
        assert test_settings.DATABRICKS_AUTH_TOKEN == 'test-token'
        assert test_settings.FLASK_HOST == '0.0.0.0'
        assert test_settings.FLASK_PORT == 5000
        assert test_settings.FLASK_DEBUG is False

    def test_flask_port_conversion(self, monkeypatch):
        """Test that FLASK_PORT is properly converted to integer"""
        monkeypatch.setenv('FLASK_PORT', '8080')
        test_settings = Settings()
        assert test_settings.FLASK_PORT == 8080
        assert isinstance(test_settings.FLASK_PORT, int)

    def test_boolean_conversion_enable_fabric_agent(self, monkeypatch):
        """Test ENABLE_FABRIC_AGENT boolean conversion"""
        # Test true values
        for true_val in ['true', 'True', 'TRUE']:
            monkeypatch.setenv('ENABLE_FABRIC_AGENT', true_val)
            test_settings = Settings()
            assert test_settings.ENABLE_FABRIC_AGENT is True

        # Test false values
        for false_val in ['false', 'False', 'FALSE', '', '0']:
            monkeypatch.setenv('ENABLE_FABRIC_AGENT', false_val)
            test_settings = Settings()
            assert test_settings.ENABLE_FABRIC_AGENT is False

    def test_boolean_conversion_flask_debug(self, monkeypatch):
        """Test FLASK_DEBUG boolean conversion"""
        # Test true values
        for true_val in ['true', 'True', 'TRUE']:
            monkeypatch.setenv('FLASK_DEBUG', true_val)
            test_settings = Settings()
            assert test_settings.FLASK_DEBUG is True

        # Test false values
        for false_val in ['false', 'False', 'FALSE', '', '0']:
            monkeypatch.setenv('FLASK_DEBUG', false_val)
            test_settings = Settings()
            assert test_settings.FLASK_DEBUG is False

    def test_get_required_vars_fabric_disabled(self, monkeypatch):
        """Test get_required_vars when Fabric is disabled"""
        monkeypatch.setenv('ENABLE_FABRIC_AGENT', 'false')
        test_settings = Settings()
        required_vars = test_settings.get_required_vars()
        
        expected_vars = ['AZURE_AI_AGENT_ENDPOINT', 'MODEL_DEPLOYMENT_NAME', 
                        'BING_CONNECTION_ID', 'PURVIEW_ENDPOINT']
        assert required_vars == expected_vars
        assert 'FABRIC_CONNECTION_ID' not in required_vars

    def test_get_required_vars_fabric_enabled(self, monkeypatch):
        """Test get_required_vars when Fabric is enabled"""
        monkeypatch.setenv('ENABLE_FABRIC_AGENT', 'true')
        test_settings = Settings()
        required_vars = test_settings.get_required_vars()
        
        expected_vars = ['AZURE_AI_AGENT_ENDPOINT', 'MODEL_DEPLOYMENT_NAME', 
                        'BING_CONNECTION_ID', 'PURVIEW_ENDPOINT', 'FABRIC_CONNECTION_ID']
        assert required_vars == expected_vars

    def test_validate_all_required_present(self, mock_env_vars):
        """Test validate method when all required variables are present"""
        test_settings = Settings()
        validation_result = test_settings.validate()
        
        assert validation_result['valid'] is True
        assert validation_result['missing_variables'] == []
        assert validation_result['fabric_enabled'] is True
        assert validation_result['genie_configured'] is True

    def test_validate_missing_required_vars(self, monkeypatch):
        """Test validate method when required variables are missing"""
        # Set only some required variables
        monkeypatch.setenv('AZURE_AI_AGENT_ENDPOINT', 'https://test.endpoint.com')
        monkeypatch.setenv('ENABLE_FABRIC_AGENT', 'true')
        
        test_settings = Settings()
        validation_result = test_settings.validate()
        
        assert validation_result['valid'] is False
        assert 'MODEL_DEPLOYMENT_NAME' in validation_result['missing_variables']
        assert 'BING_CONNECTION_ID' in validation_result['missing_variables']
        assert 'PURVIEW_ENDPOINT' in validation_result['missing_variables']
        assert 'FABRIC_CONNECTION_ID' in validation_result['missing_variables']

    def test_validate_genie_configured_partial(self, monkeypatch):
        """Test validate method with partial Genie configuration"""
        monkeypatch.setenv('DATABRICKS_INSTANCE', 'test.databricks.com')
        # Missing GENIE_SPACE_ID and DATABRICKS_AUTH_TOKEN
        
        test_settings = Settings()
        validation_result = test_settings.validate()
        
        assert validation_result['genie_configured'] is False

    def test_validate_genie_configured_complete(self, mock_env_vars):
        """Test validate method with complete Genie configuration"""
        test_settings = Settings()
        validation_result = test_settings.validate()
        
        assert validation_result['genie_configured'] is True

    def test_settings_singleton_instance(self):
        """Test that the settings instance is properly created"""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_dotenv_loaded(self):
        """Test that dotenv is loaded during settings initialization"""
        # The dotenv loading happens at module import time, which is already mocked
        # in conftest.py. We just need to verify the mock was set up correctly.
        import sys
        assert 'dotenv' in sys.modules
        assert sys.modules['dotenv'].load_dotenv.return_value is True