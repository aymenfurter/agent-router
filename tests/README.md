# Python Test Suite Documentation

This document describes the comprehensive test suite implemented for the Python agent-router application.

## Test Structure

The test suite is organized into three main categories:

```
tests/
├── __init__.py
├── conftest.py              # Shared test configuration and fixtures
├── unit/                    # Unit tests for individual modules
│   ├── __init__.py
│   ├── test_settings_simple.py        # Configuration management tests
│   ├── test_logging_simple.py         # Logging configuration tests  
│   ├── test_genie_agent_service.py     # Databricks Genie service tests
│   ├── test_message_processor.py       # Message processing tests
│   ├── test_catalog_service.py         # Purview catalog service tests
│   ├── test_agent_factory.py           # Agent creation tests
│   └── test_app.py                     # Flask application tests
├── integration/             # Integration tests with mocked dependencies
│   ├── __init__.py
│   └── test_service_integration.py     # Service integration tests
└── api/                     # API endpoint tests
    ├── __init__.py
    └── test_api_routes.py              # Flask API route tests
```

## Test Configuration

### Dependencies and Setup

- **Testing Framework**: pytest with additional plugins
- **Coverage**: pytest-cov with 80% target coverage
- **Mocking**: unittest.mock and pytest-mock for external dependencies
- **HTTP Mocking**: responses library for API testing
- **Configuration**: pyproject.toml with comprehensive test settings

### External Dependency Mocking

All external Azure services and dependencies are comprehensively mocked:

```python
mock_modules = [
    'azure', 'azure.identity', 'azure.ai', 'azure.ai.projects', 
    'azure.ai.agents', 'azure.ai.agents.models', 'azure.purview',
    'azure.purview.catalog', 'openai', 'fastapi', 'uvicorn', 'pydantic',
    'dotenv'
]
```

## Test Coverage by Module

### Configuration Management (`config/settings.py`) - 100% Coverage
**File: `test_settings_simple.py`**

- Environment variable loading and defaults
- Boolean conversion for flags (ENABLE_FABRIC_AGENT, FLASK_DEBUG)  
- Integer conversion (FLASK_PORT)
- Required variable validation
- Genie configuration validation
- Fabric agent configuration

**Key Test Cases:**
- Default values when environment variables are missing
- Proper type conversion and boolean parsing
- Configuration validation with missing/present variables
- Partial vs. complete Genie configuration

### Logging Configuration (`utils/logging_config.py`) - 100% Coverage
**File: `test_logging_simple.py`**

- Logging setup with default and custom levels
- Azure SDK logger suppression
- Logger instance creation and configuration
- Logging format and date format validation

**Key Test Cases:**
- Default INFO level logging setup
- Custom logging levels
- Azure logger suppression for reduced verbosity
- Proper format string configuration

### Genie Agent Service (`services/genie_agent_service.py`) - 100% Coverage
**File: `test_genie_agent_service.py`**

- Configuration validation
- Databricks API interaction (mocked)
- Query processing workflow
- SQL query generation and result parsing
- Error handling for failed/timeout scenarios
- Response formatting with attachments

**Key Test Cases:**
- Service configuration validation
- Complete conversation workflow with successful response
- SQL query attachment processing with data tables
- Failed status handling (FAILED, CANCELLED, timeout)
- Empty response handling
- Proper authentication headers

### Message Processor (`services/message_processor.py`) - 34% Coverage
**File: `test_message_processor.py`**

- Message content extraction
- File citation processing
- URL citation processing  
- Thread message formatting

**Key Test Cases:**
- Basic message content extraction
- File citation with Azure file metadata
- URL citation processing
- Mixed citation types
- Thread message formatting and ordering

### Flask Application (`app.py`) - Partial Coverage
**File: `test_app.py`**

- Flask application initialization
- Blueprint registration
- Route accessibility
- Static file serving
- Application lifecycle (startup/shutdown)

## Integration Tests

### Service Integration (`test_service_integration.py`)
- Connected Agent Service initialization
- Multi-service workflow testing
- Purview analysis integration
- Configuration validation across services
- End-to-end query processing (mocked)

## API Tests

### Flask API Routes (`test_api_routes.py`)
- Health check endpoints (`/api/health`, `/api/config`)
- Query processing endpoints (`/api/analyze`, `/api/route`, `/api/process`)
- Direct agent processing (`/api/process-direct`)
- Thread management (`/api/thread/<id>/messages`)

## Running Tests

### Local Development
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests with coverage
python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/api/ -v

# Run with coverage threshold
python -m pytest tests/ --cov-fail-under=80
```

### GitHub Actions CI/CD
The test suite runs automatically on:
- Push to main/develop branches
- Pull requests to main/develop branches
- Python versions: 3.10, 3.11, 3.12

**Workflow file**: `.github/workflows/python-tests.yml`

## Test Statistics

- **Total Test Cases**: 42+ passing tests
- **Current Coverage**: 31.49% (working towards 80% target)
- **Modules with 100% Coverage**: 
  - `config/settings.py`
  - `utils/logging_config.py`  
  - `services/genie_agent_service.py`
- **Test Execution Time**: ~6.5 seconds for full unit test suite

## Mocking Strategy

### Azure Services
All Azure SDK components are mocked at the module level to avoid:
- Network calls during testing
- Authentication requirements
- External service dependencies

### External APIs
- Databricks Genie API: Mocked with `responses` library
- Microsoft Purview API: Mocked for catalog search operations
- File downloads: Mocked to avoid network I/O

### Flask Application
- Database connections: N/A (no database in current implementation)
- External service calls: Comprehensively mocked
- Static file serving: Uses temporary directories for testing

## Test Environment Variables

The test suite uses environment variables for configuration testing:

```bash
AZURE_AI_AGENT_ENDPOINT="https://test.endpoint.com"
MODEL_DEPLOYMENT_NAME="test-model"
PURVIEW_ENDPOINT="https://test-purview.endpoint.com"
BING_CONNECTION_ID="test-bing-id"
FABRIC_CONNECTION_ID="test-fabric-id"
ENABLE_FABRIC_AGENT="true"
DATABRICKS_INSTANCE="test.databricks.com"
GENIE_SPACE_ID="test-space-id"
DATABRICKS_AUTH_TOKEN="test-token"
```

## Future Test Enhancements

1. **Increase Coverage**: Add more comprehensive tests for:
   - `services/connected_agent_service.py` (currently 32% coverage)
   - `services/catalog_service.py` (needs HTTP mocking fixes)
   - `services/agent_factory.py` (needs import mocking improvements)

2. **Performance Tests**: Add performance testing for:
   - Query processing latency
   - Concurrent request handling
   - Memory usage patterns

3. **End-to-End Tests**: Add real integration tests with:
   - Test Azure environments
   - Test Databricks instances
   - Test Purview catalogs

4. **Security Tests**: Add security testing for:
   - Authentication handling
   - Input validation
   - Secret management

## Contributing to Tests

When adding new features:

1. **Unit Tests**: Add unit tests for all new functions/classes
2. **Integration Tests**: Add integration tests for service interactions
3. **API Tests**: Add API tests for new endpoints
4. **Mocking**: Ensure all external dependencies are properly mocked
5. **Coverage**: Maintain 80% minimum coverage threshold
6. **Documentation**: Update test documentation for new test patterns