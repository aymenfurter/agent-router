import pytest
import json
from unittest.mock import patch, Mock, MagicMock
import responses

# Mock dependencies before imports
with patch.dict('sys.modules', {
    'azure': MagicMock(),
    'azure.identity': MagicMock(),
    'azure.purview': MagicMock(),
    'azure.purview.catalog': MagicMock(),
}):
    from services.catalog_service import CatalogService


class TestCatalogService:
    """Test cases for the CatalogService class"""
    
    @pytest.fixture
    def catalog_service(self):
        """Create CatalogService instance"""
        return CatalogService()
    
    def test_init(self, catalog_service):
        """Test CatalogService initialization"""
        assert catalog_service.logger is not None
        assert isinstance(catalog_service.contacts, dict)
        assert "c53c736b-8469-409c-9dcc-b3a61953d4dd" in catalog_service.contacts
    
    @pytest.mark.parametrize("description,expected", [
        ("This dataset connects to agent: genie for analytics", "genie"),
        ("Use agent: rag for document search", "rag"),
        ("Agent: fabric handles structured data", "fabric"),
        ("AGENT: WEB for internet searches", "WEB"),  # The regex captures as-is
        ("No agent information here", None),
        ("", None),
        (None, None)
    ])
    def test_parse_agent_from_description(self, catalog_service, description, expected):
        """Test parsing agent name from description"""
        result = catalog_service.parse_agent_from_description(description)
        assert result == expected
    
    def test_parse_agent_from_description_case_insensitive(self, catalog_service):
        """Test that agent parsing is case insensitive"""
        descriptions = [
            "agent: GENIE",
            "AGENT: genie", 
            "Agent: Genie",
            "AgEnT: GeNiE"
        ]
        
        for desc in descriptions:
            result = catalog_service.parse_agent_from_description(desc)
            assert result.lower() == "genie"
    
    @responses.activate
    @patch('services.catalog_service.AzureCliCredential')
    @patch('services.catalog_service.settings')
    def test_search_catalog_successful(self, mock_settings, mock_cred, catalog_service):
        """Test successful catalog search"""
        # Mock settings
        mock_settings.PURVIEW_ENDPOINT = "https://test-purview.azure.com"
        
        # Mock credential
        mock_token = Mock()
        mock_token.token = "test_access_token"
        mock_cred.return_value.get_token.return_value = mock_token
        
        # Mock API response
        api_response = {
            'value': [
                {
                    'id': 'asset-1',
                    'displayText': 'Sales Database',
                    'userDescription': 'Sales data with agent: genie support',
                    'contact': [{'id': 'c53c736b-8469-409c-9dcc-b3a61953d4dd'}]
                },
                {
                    'id': 'asset-2', 
                    'displayText': 'Marketing Documents',
                    'userDescription': 'Marketing materials for agent: rag',
                    'contact': [{'id': 'unknown-contact-id'}]
                }
            ]
        }
        
        responses.add(
            responses.POST,
            'https://test-purview.azure.com/datamap/api/search/query?api-version=2023-09-01',
            json=api_response,
            status=200
        )
        
        result = catalog_service.search_catalog("sales")
        
        assert result['status'] == 'success'
        assert result['assets_found'] == 2
        assert len(result['results']) == 2
        
        # Check first asset
        first_asset = result['results'][0]
        assert first_asset['name'] == 'Sales Database'
        assert first_asset['connected_agent'] == 'genie'
        assert first_asset['contact'] == 'Aymen Furter (aymen.furter@microsoft.com)'
        
        # Check second asset
        second_asset = result['results'][1]
        assert second_asset['name'] == 'Marketing Documents'
        assert second_asset['connected_agent'] == 'rag'
        assert second_asset['contact'] is None
    
    @responses.activate
    @patch('services.catalog_service.AzureCliCredential')
    @patch('services.catalog_service.settings')
    def test_search_catalog_no_results(self, mock_settings, mock_cred, catalog_service):
        """Test catalog search with no results"""
        mock_settings.PURVIEW_ENDPOINT = "https://test-purview.azure.com"
        
        mock_token = Mock()
        mock_token.token = "test_access_token"
        mock_cred.return_value.get_token.return_value = mock_token
        
        # Empty response
        api_response = {'value': []}
        
        responses.add(
            responses.POST,
            'https://test-purview.azure.com/datamap/api/search/query?api-version=2023-09-01',
            json=api_response,
            status=200
        )
        
        result = catalog_service.search_catalog("nonexistent")
        
        assert result['status'] == 'success'
        assert result['assets_found'] == 0
        assert result['results'] == []
    
    @responses.activate
    @patch('services.catalog_service.AzureCliCredential')
    @patch('services.catalog_service.settings')
    def test_search_catalog_with_filters(self, mock_settings, mock_cred, catalog_service):
        """Test that catalog search includes proper filters"""
        mock_settings.PURVIEW_ENDPOINT = "https://test-purview.azure.com"
        
        mock_token = Mock()
        mock_token.token = "test_access_token"
        mock_cred.return_value.get_token.return_value = mock_token
        
        def request_callback(request):
            # Verify request payload
            payload = json.loads(request.body)
            assert payload['limit'] == 10
            assert payload['keywords'] == 'test query'
            
            # Verify filters
            expected_filters = {
                'or': [
                    {'entityType': 'azure_storage_account'},
                    {'entityType': 'fabric_lakehouse'},
                    {'entityType': 'databricks_schema'}
                ]
            }
            assert payload['filter'] == expected_filters
            
            # Verify headers
            assert request.headers['Authorization'] == 'Bearer test_access_token'
            
            return (200, {}, json.dumps({'value': []}))
        
        responses.add_callback(
            responses.POST,
            'https://test-purview.azure.com/datamap/api/search/query?api-version=2023-09-01',
            callback=request_callback,
            content_type='application/json'
        )
        
        catalog_service.search_catalog("test query")
    
    @responses.activate
    @patch('services.catalog_service.AzureCliCredential')
    @patch('services.catalog_service.settings')
    def test_search_catalog_http_error(self, mock_settings, mock_cred, catalog_service):
        """Test catalog search with HTTP error"""
        mock_settings.PURVIEW_ENDPOINT = "https://test-purview.azure.com"
        
        mock_token = Mock()
        mock_token.token = "test_access_token"
        mock_cred.return_value.get_token.return_value = mock_token
        
        responses.add(
            responses.POST,
            'https://test-purview.azure.com/datamap/api/search/query?api-version=2023-09-01',
            json={'error': 'Not found'},
            status=404
        )
        
        with pytest.raises(Exception):  # requests.exceptions.HTTPError
            catalog_service.search_catalog("test")
    
    def test_search_catalog_asset_without_description(self, catalog_service):
        """Test handling asset without description"""
        with responses.RequestsMock() as rsps:
            # Mock credential and settings
            with patch('services.catalog_service.AzureCliCredential') as mock_cred, \
                 patch('services.catalog_service.settings') as mock_settings:
                
                mock_settings.PURVIEW_ENDPOINT = "https://test-purview.azure.com"
                mock_token = Mock()
                mock_token.token = "test_token"
                mock_cred.return_value.get_token.return_value = mock_token
                
                # Asset without userDescription
                api_response = {
                    'value': [
                        {
                            'id': 'asset-no-desc',
                            'displayText': 'Asset Without Description'
                            # No userDescription field
                        }
                    ]
                }
                
                rsps.add(
                    responses.POST,
                    'https://test-purview.azure.com/datamap/api/search/query?api-version=2023-09-01',
                    json=api_response,
                    status=200
                )
                
                result = catalog_service.search_catalog("test")
                
                assert result['status'] == 'success'
                assert result['assets_found'] == 1
                asset = result['results'][0]
                assert asset['description'] == 'No description'
                assert asset['connected_agent'] is None
    
    def test_search_catalog_asset_without_contact(self, catalog_service):
        """Test handling asset without contact information"""
        with responses.RequestsMock() as rsps:
            with patch('services.catalog_service.AzureCliCredential') as mock_cred, \
                 patch('services.catalog_service.settings') as mock_settings:
                
                mock_settings.PURVIEW_ENDPOINT = "https://test-purview.azure.com"
                mock_token = Mock()
                mock_token.token = "test_token"
                mock_cred.return_value.get_token.return_value = mock_token
                
                # Asset without contact
                api_response = {
                    'value': [
                        {
                            'id': 'asset-no-contact',
                            'displayText': 'Asset Without Contact',
                            'userDescription': 'Asset description'
                            # No contact field
                        }
                    ]
                }
                
                rsps.add(
                    responses.POST,
                    'https://test-purview.azure.com/datamap/api/search/query?api-version=2023-09-01',
                    json=api_response,
                    status=200
                )
                
                result = catalog_service.search_catalog("test")
                
                assert result['status'] == 'success'
                asset = result['results'][0]
                assert asset['contact'] is None
    
    def test_contacts_mapping(self, catalog_service):
        """Test that contacts mapping is properly configured"""
        expected_contact_id = "c53c736b-8469-409c-9dcc-b3a61953d4dd"
        expected_contact_info = "Aymen Furter (aymen.furter@microsoft.com)"
        
        assert expected_contact_id in catalog_service.contacts
        assert catalog_service.contacts[expected_contact_id] == expected_contact_info
    
    @patch('services.catalog_service.AzureCliCredential')
    def test_credential_token_request(self, mock_cred, catalog_service):
        """Test that credential requests proper token scope"""
        mock_token = Mock()
        mock_token.token = "test_token"
        mock_cred.return_value.get_token.return_value = mock_token
        
        with responses.RequestsMock() as rsps:
            with patch('services.catalog_service.settings') as mock_settings:
                mock_settings.PURVIEW_ENDPOINT = "https://test-purview.azure.com"
                
                rsps.add(
                    responses.POST,
                    'https://test-purview.azure.com/datamap/api/search/query?api-version=2023-09-01',
                    json={'value': []},
                    status=200
                )
                
                catalog_service.search_catalog("test")
                
                # Verify token was requested with proper scope
                mock_cred.return_value.get_token.assert_called_once_with("https://purview.azure.net/.default")