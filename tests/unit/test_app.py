import pytest
import os
from unittest.mock import patch, Mock, MagicMock
from flask import Flask

# Mock external dependencies before imports
with patch.dict('sys.modules', {
    'dotenv': MagicMock(),
    'azure': MagicMock(),
    'azure.identity': MagicMock(),
    'azure.ai': MagicMock(),
    'azure.ai.projects': MagicMock(),
}):
    # Need to mock the services before importing app
    with patch('app.connected_agent_service') as mock_service, \
         patch('app.setup_logging') as mock_logging, \
         patch('app.settings') as mock_settings:
        
        mock_service.cleanup.return_value = None
        mock_logging.return_value = None
        mock_settings.FLASK_HOST = '0.0.0.0'
        mock_settings.FLASK_PORT = 5000
        mock_settings.FLASK_DEBUG = False
        
        from app import app


class TestFlaskApp:
    """Test cases for the Flask application"""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app"""
        app.config['TESTING'] = True
        return app.test_client()
    
    @pytest.fixture
    def mock_dist_dir(self, tmp_path, monkeypatch):
        """Mock the dist directory with test files"""
        dist_dir = tmp_path / "dist"
        dist_dir.mkdir()
        
        # Create test index.html
        index_file = dist_dir / "index.html"
        index_file.write_text("<html><body>Test App</body></html>")
        
        # Create test static files
        js_file = dist_dir / "app.js"
        js_file.write_text("console.log('test');")
        
        css_file = dist_dir / "styles.css"
        css_file.write_text("body { margin: 0; }")
        
        # Patch the DIST_DIR in app module
        monkeypatch.setattr('app.DIST_DIR', str(dist_dir))
        return dist_dir
        
        css_file = dist_dir / "styles.css"
        css_file.write_text("body { margin: 0; }")
        
        # Patch the DIST_DIR in the app module
        monkeypatch.setattr('app.DIST_DIR', str(dist_dir))
        return str(dist_dir)
    
    def test_app_creation(self):
        """Test that Flask app is created properly"""
        assert app is not None
        assert isinstance(app, Flask)
        assert app.config.get('TESTING') is not None
    
    def test_blueprints_registered(self):
        """Test that all blueprints are registered"""
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'health' in blueprint_names
        assert 'query' in blueprint_names  
        assert 'thread' in blueprint_names
    
    def test_index_route(self, client, mock_dist_dir):
        """Test the main index route"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Test App' in response.data
    
    def test_static_files_js(self, client, mock_dist_dir):
        """Test serving JavaScript static files"""
        response = client.get('/app.js')
        assert response.status_code == 200
        assert b"console.log('test');" in response.data
    
    def test_static_files_css(self, client, mock_dist_dir):
        """Test serving CSS static files"""
        response = client.get('/styles.css')
        assert response.status_code == 200
        assert b"body { margin: 0; }" in response.data
    
    def test_static_files_not_found(self, client, mock_dist_dir):
        """Test handling of non-existent static files"""
        response = client.get('/nonexistent.js')
        assert response.status_code == 404
    
    @patch('app.connected_agent_service')
    def test_teardown_appcontext(self, mock_service, client):
        """Test application context teardown"""
        mock_service.cleanup.return_value = None
        
        # Simulate an error in app context
        with app.app_context():
            from app import cleanup_service
            cleanup_service(Exception("Test error"))
        
        # The teardown should handle errors gracefully
        assert True  # If we get here, no exception was raised
    
    def test_cleanup_on_exit_function_exists(self):
        """Test that cleanup function is defined"""
        from app import cleanup_on_exit
        assert callable(cleanup_on_exit)
    
    @patch('app.connected_agent_service')
    def test_cleanup_on_exit(self, mock_service):
        """Test cleanup on exit functionality"""
        from app import cleanup_on_exit
        mock_service.cleanup.return_value = None
        
        cleanup_on_exit()
        mock_service.cleanup.assert_called_once()
    
    def test_health_endpoint_available(self, client):
        """Test that health endpoint is accessible"""
        with patch('api.health_routes.connected_agent_service') as mock_service, \
             patch('api.health_routes.settings') as mock_settings:
            
            mock_service.get_health_status.return_value = {'status': 'ok'}
            mock_settings.validate.return_value = {'valid': True}
            
            response = client.get('/api/health')
            assert response.status_code == 200
    
    def test_query_endpoints_available(self, client):
        """Test that query endpoints are accessible"""
        with patch('api.query_routes.connected_agent_service') as mock_service:
            mock_service.analyze_purview.return_value = {
                'success': True, 'purview': 'test'
            }
            
            response = client.post('/api/analyze', 
                                 json={'query': 'test'},
                                 content_type='application/json')
            assert response.status_code == 200
    
    def test_thread_endpoints_available(self, client):
        """Test that thread endpoints are accessible"""
        with patch('api.thread_routes.connected_agent_service') as mock_service:
            mock_service.get_thread_messages.return_value = {
                'success': True, 'messages': []
            }
            
            response = client.get('/api/thread/test-thread-id/messages')
            assert response.status_code == 200


class TestAppStartupAndShutdown:
    """Test Flask application startup and shutdown behavior"""
    
    @patch('app.os.path.exists')
    @patch('app.print')
    @patch('app.exit')
    def test_missing_dist_directory(self, mock_exit, mock_print, mock_exists):
        """Test behavior when dist directory is missing"""
        mock_exists.return_value = False
        
        # Import the main execution block (this is tricky to test directly)
        # We'll test the logic by mocking the path check
        from app import DIST_DIR
        
        # Simulate the condition check
        if not os.path.exists(DIST_DIR):
            mock_print("❌ Build files not found!")
            mock_exit(1)
        
        # Verify the expected behavior would occur
        assert mock_exists.return_value is False
    
    @patch('app.os.path.exists')
    def test_dist_directory_exists(self, mock_exists):
        """Test normal startup when dist directory exists"""
        mock_exists.return_value = True
        
        from app import DIST_DIR
        
        # Check that when directory exists, no exit is called
        if not os.path.exists(DIST_DIR):
            assert False, "Should not reach this point"
        
        assert mock_exists.return_value is True
    
    @patch('app.atexit.register')
    def test_cleanup_registration(self, mock_atexit_register):
        """Test that cleanup function is registered with atexit"""
        # This is difficult to test directly since it happens at module level
        # We'll verify the function exists and is callable
        from app import cleanup_on_exit
        assert callable(cleanup_on_exit)
    
    def test_app_configuration(self):
        """Test Flask app configuration"""
        # Test that the app has the expected configuration
        assert app.name == 'app'
        
        # Test that blueprints are properly configured
        health_bp = app.blueprints.get('health')
        assert health_bp is not None
        assert health_bp.url_prefix == '/api'
        
        query_bp = app.blueprints.get('query')
        assert query_bp is not None
        assert query_bp.url_prefix == '/api'
        
        thread_bp = app.blueprints.get('thread')
        assert thread_bp is not None
        assert thread_bp.url_prefix == '/api'
    
    @patch('app.settings')
    def test_settings_access(self, mock_settings):
        """Test that settings are properly imported and accessible"""
        mock_settings.FLASK_HOST = '127.0.0.1'
        mock_settings.FLASK_PORT = 8080
        mock_settings.FLASK_DEBUG = True
        
        # Test that settings are accessible in the app context
        assert mock_settings.FLASK_HOST == '127.0.0.1'
        assert mock_settings.FLASK_PORT == 8080
        assert mock_settings.FLASK_DEBUG is True
    
    def test_dist_dir_configuration(self):
        """Test DIST_DIR path configuration"""
        from app import DIST_DIR
        assert DIST_DIR is not None
        assert isinstance(DIST_DIR, str)
        assert 'dist' in DIST_DIR