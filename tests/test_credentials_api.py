import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import the FastAPI app
from cloudproxy.main import app
# Import CredentialManager class for instantiation and the module to patch
from cloudproxy.credentials import CredentialManager
import cloudproxy.credentials as credentials_module

# Mock the provider reset_clients functions before initializing the TestClient
# as the credentials_api router imports and uses these functions.
# We use patch as a context manager or decorator for mocking during tests.

# Reset the global credential_manager for each test
@pytest.fixture(autouse=True)
def fresh_credential_manager(monkeypatch):
    # Create a new CredentialManager instance for each test
    test_cm = CredentialManager()
    # Patch the credential_manager in the credentials module itself
    monkeypatch.setattr(credentials_module, "credential_manager", test_cm)
    # The API routes and any other module importing credential_manager from cloudproxy.credentials
    # will now get this test_cm instance.
    yield test_cm
    # monkeypatch automatically undoes the patch after the test

# Mock the reset_clients functions for all API tests
# We need to patch the functions where they are *used* (in credentials_api.py)
@pytest.fixture(autouse=True)
def mock_reset_clients():
    with patch('cloudproxy.api.credentials_api.reset_aws_clients') as mock_aws_reset, \
         patch('cloudproxy.api.credentials_api.reset_digitalocean_clients') as mock_do_reset, \
         patch('cloudproxy.api.credentials_api.reset_gcp_clients') as mock_gcp_reset, \
         patch('cloudproxy.api.credentials_api.reset_hetzner_clients') as mock_hetzner_reset:
        yield mock_aws_reset, mock_do_reset, mock_gcp_reset, mock_hetzner_reset


@pytest.fixture
def client(fresh_credential_manager):
    """Provides a TestClient with a fresh credential_manager."""
    # The fresh_credential_manager fixture already patches the global credential_manager
    # in cloudproxy.credentials. The TestClient should pick up this patched version.
    return TestClient(app)

def test_credential_manager_add_get(fresh_credential_manager):
    """Test adding and retrieving credentials."""
    provider = "aws"
    instance = "test-instance"
    secrets = {"access_key_id": "abc", "secret_access_key": "xyz"}

    fresh_credential_manager.add_credentials(provider, instance, secrets)
    retrieved_secrets = fresh_credential_manager.get_credentials(provider, instance)

    assert retrieved_secrets == secrets

def test_credential_manager_get_nonexistent(fresh_credential_manager):
    """Test retrieving credentials for a non-existent instance."""
    provider = "aws"
    instance = "non-existent-instance"

    retrieved_secrets = fresh_credential_manager.get_credentials(provider, instance)

    assert retrieved_secrets is None

def test_credential_manager_remove(fresh_credential_manager):
    """Test removing credentials."""
    provider = "gcp"
    instance = "test-gcp-instance"
    secrets = {"service_account_key": "{}"}

    fresh_credential_manager.add_credentials(provider, instance, secrets)
    assert fresh_credential_manager.get_credentials(provider, instance) is not None

    fresh_credential_manager.remove_credentials(provider, instance)
    assert fresh_credential_manager.get_credentials(provider, instance) is None

def test_credential_manager_remove_nonexistent(fresh_credential_manager):
    """Test removing non-existent credentials."""
    provider = "digitalocean"
    instance = "non-existent-do-instance"

    # Removing non-existent credentials should not raise an error
    fresh_credential_manager.remove_credentials(provider, instance)
    assert fresh_credential_manager.get_credentials(provider, instance) is None

def test_credential_manager_list_configurations(fresh_credential_manager):
    """Test listing configurations."""
    fresh_credential_manager.add_credentials("aws", "instance1", {"key": "val1"})
    fresh_credential_manager.add_credentials("gcp", "instance2", {"key": "val2"})
    fresh_credential_manager.add_credentials("aws", "instance3", {"key": "val3"})

    configurations = fresh_credential_manager.list_configurations()

    expected_configurations = [
        ("aws", "instance1"),
        ("gcp", "instance2"),
        ("aws", "instance3"),
    ]
    # Order might not be guaranteed, so check if all expected are present
    assert len(configurations) == len(expected_configurations)
    for conf in expected_configurations:
        assert conf in configurations

# API Tests
def test_post_credentials(client, fresh_credential_manager):
    """Test POST /api/credentials/{provider_name}/{instance_id} endpoint."""
    provider = "aws"
    instance = "api-test-instance"
    secrets = {"access_key_id": "api_abc", "secret_access_key": "api_xyz"}

    with patch('cloudproxy.api.credentials_api.credential_manager', fresh_credential_manager):
        response = client.post(f"/api/credentials/{provider}/{instance}", json={"secrets": secrets})

    assert response.status_code == 200
    assert response.json() == {"message": f"Credentials added/updated for {provider}/{instance}"}

    # Verify credentials were added to the manager
    retrieved_secrets = fresh_credential_manager.get_credentials(provider, instance)
    assert retrieved_secrets == secrets

def test_get_credentials(client, fresh_credential_manager):
    """Test GET /api/credentials endpoint."""
    fresh_credential_manager.add_credentials("aws", "get-instance1", {"key": "val1"})
    fresh_credential_manager.add_credentials("gcp", "get-instance2", {"key": "val2"})

    with patch('cloudproxy.api.credentials_api.credential_manager', fresh_credential_manager):
        response = client.get("/api/credentials/")

    assert response.status_code == 200
    configurations = response.json()

    expected_configurations = [
        ("aws", "get-instance1"),
        ("gcp", "get-instance2"),
    ]
    assert len(configurations) == len(expected_configurations)
    for conf in expected_configurations:
        assert list(conf) in configurations # FastAPI returns list, not tuple

def test_delete_credentials(client, fresh_credential_manager):
    """Test DELETE /api/credentials/{provider_name}/{instance_id} endpoint."""
    provider = "hetzner"
    instance = "delete-test-instance"
    secrets = {"access_token": "delete_token"}

    fresh_credential_manager.add_credentials(provider, instance, secrets)
    assert fresh_credential_manager.get_credentials(provider, instance) is not None

    with patch('cloudproxy.api.credentials_api.credential_manager', fresh_credential_manager):
        response = client.delete(f"/api/credentials/{provider}/{instance}")

    assert response.status_code == 200
    assert response.json() == {"message": f"Credentials removed for {provider}/{instance}"}

    # Verify credentials were removed from the manager
    assert fresh_credential_manager.get_credentials(provider, instance) is None

def test_delete_nonexistent_credentials(client, fresh_credential_manager):
    """Test DELETE /api/credentials/{provider_name}/{instance_id} for non-existent credentials."""
    provider = "digitalocean"
    instance = "non-existent-api-instance"

    with patch('cloudproxy.api.credentials_api.credential_manager', fresh_credential_manager):
        response = client.delete(f"/api/credentials/{provider}/{instance}")

    assert response.status_code == 200 # Should still return 200 even if not found
    assert response.json() == {"message": f"Credentials removed for {provider}/{instance}"}
    assert fresh_credential_manager.get_credentials(provider, instance) is None