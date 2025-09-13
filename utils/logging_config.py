import logging
from typing import List

def setup_logging(level: int = logging.INFO) -> None:
    """Setup application logging configuration."""
    
    # Configure basic logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Suppress Azure SDK verbose logs
    azure_loggers = [
        'azure.core.pipeline.policies.http_logging_policy',
        'azure.identity._credentials.managed_identity', 
        'azure.identity._credentials.chained',
        'azure.identity',
        'azure.core',
        'azure.ai'
    ]
    
    for logger_name in azure_loggers:
        azure_logger = logging.getLogger(logger_name)
        azure_logger.setLevel(logging.ERROR)
        azure_logger.disabled = True

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration."""
    return logging.getLogger(name)
