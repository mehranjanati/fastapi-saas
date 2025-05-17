import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the parent directory
from main import app, get_current_user
from order_processor import order_processor

# Create a mock user for testing
async def mock_current_user():
    return {
        "user_id": "test-user-id",
        "username": "test-user",
        "role": "user"
    }

# Setup for all tests
@pytest.fixture
def client():
    """Create a test client with authentication bypassed"""
    # Override the dependency
    app.dependency_overrides[get_current_user] = mock_current_user
    
    # Create and return a test client
    test_client = TestClient(app)
    yield test_client
    
    # Clean up after tests
    app.dependency_overrides = {} 