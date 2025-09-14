import pytest
import logging
from unittest.mock import patch, Mock
from utils.logging_config import setup_logging, get_logger


class TestLoggingConfig:
    """Test cases for the logging configuration utilities"""
    
    def test_setup_logging_default_level(self):
        """Test setup_logging with default level"""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            
            mock_basic_config.assert_called_once_with(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom level"""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(level=logging.DEBUG)
            
            mock_basic_config.assert_called_once_with(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

    def test_setup_logging_azure_loggers_suppressed(self):
        """Test that Azure SDK loggers are properly suppressed"""
        with patch('logging.basicConfig'), \
             patch('logging.getLogger') as mock_get_logger:
            
            # Mock logger instances
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            setup_logging()
            
            # Verify Azure loggers were configured
            expected_azure_loggers = [
                'azure.core.pipeline.policies.http_logging_policy',
                'azure.identity._credentials.managed_identity',
                'azure.identity._credentials.chained',
                'azure.identity',
                'azure.core',
                'azure.ai'
            ]
            
            # Check that getLogger was called for each Azure logger
            for logger_name in expected_azure_loggers:
                mock_get_logger.assert_any_call(logger_name)
            
            # Check that each mock logger was configured properly
            assert mock_logger.setLevel.call_count == len(expected_azure_loggers)
            mock_logger.setLevel.assert_called_with(logging.ERROR)
            assert mock_logger.disabled is True

    def test_get_logger_returns_logger_instance(self):
        """Test that get_logger returns a proper logger instance"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock(spec=logging.Logger)
            mock_get_logger.return_value = mock_logger
            
            logger = get_logger('test.module')
            
            mock_get_logger.assert_called_once_with('test.module')
            assert logger == mock_logger

    def test_get_logger_different_names(self):
        """Test get_logger with different logger names"""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock(spec=logging.Logger)
            mock_get_logger.return_value = mock_logger
            
            # Test different logger names
            logger_names = ['app', 'services.agent', 'config.settings', '__main__']
            
            for name in logger_names:
                logger = get_logger(name)
                mock_get_logger.assert_any_call(name)
                assert logger == mock_logger

    def test_setup_logging_integration(self):
        """Integration test for setup_logging functionality"""
        # Test actual logging setup without mocking
        setup_logging(level=logging.WARNING)
        
        # Get a test logger
        test_logger = get_logger('test_integration')
        
        # Verify the logger was created
        assert isinstance(test_logger, logging.Logger)
        assert test_logger.name == 'test_integration'
        
        # Verify Azure loggers are suppressed
        azure_logger = logging.getLogger('azure.core')
        assert azure_logger.level == logging.ERROR
        assert azure_logger.disabled is True

    def test_logging_format_and_date_format(self):
        """Test that logging format and date format are correctly applied"""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            
            # Extract the call arguments
            call_args = mock_basic_config.call_args[1]  # keyword arguments
            
            assert call_args['format'] == '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            assert call_args['datefmt'] == '%Y-%m-%d %H:%M:%S'

    def test_azure_logger_configuration_details(self):
        """Test detailed Azure logger configuration"""
        expected_loggers = [
            'azure.core.pipeline.policies.http_logging_policy',
            'azure.identity._credentials.managed_identity', 
            'azure.identity._credentials.chained',
            'azure.identity',
            'azure.core',
            'azure.ai'
        ]
        
        with patch('logging.basicConfig'), \
             patch('logging.getLogger') as mock_get_logger:
            
            mock_loggers = {}
            for logger_name in expected_loggers:
                mock_logger = Mock()
                mock_loggers[logger_name] = mock_logger
                
            def get_logger_side_effect(name):
                return mock_loggers.get(name, Mock())
                
            mock_get_logger.side_effect = get_logger_side_effect
            
            setup_logging()
            
            # Verify each Azure logger was properly configured
            for logger_name in expected_loggers:
                mock_logger = mock_loggers[logger_name]
                mock_logger.setLevel.assert_called_once_with(logging.ERROR)
                assert mock_logger.disabled is True