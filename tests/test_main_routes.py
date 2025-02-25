from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, Mock

from cloudproxy.main import app, get_ip_list
from cloudproxy.providers.settings import delete_queue, restart_queue, config

# Create test client
client = TestClient(app)

# Fixture to preserve original settings
@pytest.fixture
def setup_test_data():
    """Fixture to setup test data and restore original values after test"""
    # Save original values
    original_do_ips = config["providers"]["digitalocean"]["ips"].copy()
    original_aws_ips = config["providers"]["aws"]["ips"].copy()
    original_gcp_ips = config["providers"]["gcp"]["ips"].copy()
    original_hetzner_ips = config["providers"]["hetzner"]["ips"].copy()
    original_delete_queue = delete_queue.copy()
    original_restart_queue = restart_queue.copy()
    
    # Setup test data
    config["providers"]["digitalocean"]["ips"] = ["1.1.1.1", "2.2.2.2"]
    config["providers"]["aws"]["ips"] = ["3.3.3.3", "4.4.4.4"]
    config["providers"]["gcp"]["ips"] = ["5.5.5.5", "6.6.6.6"]
    config["providers"]["hetzner"]["ips"] = ["7.7.7.7", "8.8.8.8"]
    
    # Clear queues
    delete_queue.clear()
    restart_queue.clear()
    
    yield
    
    # Restore original values
    config["providers"]["digitalocean"]["ips"] = original_do_ips
    config["providers"]["aws"]["ips"] = original_aws_ips
    config["providers"]["gcp"]["ips"] = original_gcp_ips
    config["providers"]["hetzner"]["ips"] = original_hetzner_ips
    delete_queue.clear()
    delete_queue.update(original_delete_queue)
    restart_queue.clear()
    restart_queue.update(original_restart_queue)

# Tests for root endpoint with pagination
def test_root_endpoint_default_pagination(setup_test_data):
    """Test the root endpoint with default pagination (offset=0, limit=10)"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    assert "metadata" in data
    assert "total" in data
    assert "proxies" in data
    assert data["total"] == 8  # Total IPs across all providers
    assert len(data["proxies"]) == 8  # Default limit is 10, but we only have 8
    
    # Check that IPs from each provider are included
    ip_values = [proxy["ip"] for proxy in data["proxies"]]
    assert "1.1.1.1" in ip_values
    assert "3.3.3.3" in ip_values
    assert "5.5.5.5" in ip_values
    assert "7.7.7.7" in ip_values

def test_root_endpoint_custom_pagination(setup_test_data):
    """Test the root endpoint with custom pagination parameters"""
    response = client.get("/?offset=2&limit=3")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 8  # Total IPs across all providers
    assert len(data["proxies"]) == 3  # Requested limit of 3
    
    # Third, fourth, and fifth IPs based on the order in get_ip_list
    ip_values = [proxy["ip"] for proxy in data["proxies"]]
    # The exact IPs will depend on the order they're returned by get_ip_list
    assert len(ip_values) == 3
    
def test_root_endpoint_pagination_bounds(setup_test_data):
    """Test the root endpoint with pagination at the bounds"""
    # Test offset beyond available data
    response = client.get("/?offset=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 8
    assert len(data["proxies"]) == 0  # No proxies returned
    
    # Test with very large limit
    response = client.get("/?limit=100")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 8
    assert len(data["proxies"]) == 8  # All proxies returned

# Tests for /destroy endpoints
def test_destroy_get_endpoint_empty(setup_test_data):
    """Test the GET /destroy endpoint with empty queue"""
    response = client.get("/destroy")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["proxies"]) == 0

def test_destroy_get_endpoint_with_items(setup_test_data):
    """Test the GET /destroy endpoint with items in queue"""
    # Add some IPs to delete queue
    delete_queue.add("1.1.1.1")
    delete_queue.add("3.3.3.3")
    
    response = client.get("/destroy")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2
    assert len(data["proxies"]) == 2
    
    ip_values = [proxy["ip"] for proxy in data["proxies"]]
    assert "1.1.1.1" in ip_values
    assert "3.3.3.3" in ip_values

def test_destroy_delete_endpoint(setup_test_data):
    """Test the DELETE /destroy endpoint"""
    # Add an IP to the providers list
    ip_to_delete = "9.9.9.9"
    config["providers"]["digitalocean"]["ips"].append(ip_to_delete)
    
    # Schedule the IP for deletion
    response = client.delete(f"/destroy?ip_address={ip_to_delete}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Proxy scheduled for deletion"
    assert data["proxy"]["ip"] == ip_to_delete
    assert ip_to_delete in delete_queue

# Tests for /restart endpoints
def test_restart_get_endpoint_empty(setup_test_data):
    """Test the GET /restart endpoint with empty queue"""
    response = client.get("/restart")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["proxies"]) == 0

def test_restart_get_endpoint_with_items(setup_test_data):
    """Test the GET /restart endpoint with items in queue"""
    # Add some IPs to restart queue
    restart_queue.add("2.2.2.2")
    restart_queue.add("4.4.4.4")
    
    response = client.get("/restart")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2
    assert len(data["proxies"]) == 2
    
    ip_values = [proxy["ip"] for proxy in data["proxies"]]
    assert "2.2.2.2" in ip_values
    assert "4.4.4.4" in ip_values

def test_restart_delete_endpoint(setup_test_data):
    """Test the DELETE /restart endpoint"""
    # Use an existing IP from the providers list
    ip_to_restart = "5.5.5.5"
    
    # Schedule the IP for restart
    response = client.delete(f"/restart?ip_address={ip_to_restart}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["message"] == "Proxy scheduled for restart"
    assert data["proxy"]["ip"] == ip_to_restart
    assert ip_to_restart in restart_queue

# Tests for provider management endpoints
def test_providers_get_all(setup_test_data):
    """Test the GET /providers endpoint"""
    response = client.get("/providers")
    assert response.status_code == 200
    data = response.json()
    
    assert "providers" in data
    assert "metadata" in data
    assert "digitalocean" in data["providers"]
    assert "aws" in data["providers"]
    assert "gcp" in data["providers"]
    assert "hetzner" in data["providers"]
    
    # Check that provider data has expected structure
    do_provider = data["providers"]["digitalocean"]
    assert "enabled" in do_provider
    assert "ips" in do_provider
    assert "scaling" in do_provider
    assert "region" in do_provider
    assert "size" in do_provider

def test_provider_get_specific(setup_test_data):
    """Test the GET /providers/{provider} endpoint"""
    response = client.get("/providers/digitalocean")
    assert response.status_code == 200
    data = response.json()
    
    assert "provider" in data
    assert "metadata" in data
    assert "message" in data
    assert data["message"] == "Provider 'digitalocean' configuration retrieved successfully"
    
    provider = data["provider"]
    assert provider["ips"] == ["1.1.1.1", "2.2.2.2"]
    assert "scaling" in provider
    assert "region" in provider
    assert "size" in provider

def test_provider_patch_endpoint(setup_test_data):
    """Test the PATCH /providers/{provider} endpoint"""
    # Save original scaling settings
    original_min = config["providers"]["aws"]["scaling"]["min_scaling"]
    original_max = config["providers"]["aws"]["scaling"]["max_scaling"]
    
    try:
        # Update scaling settings
        response = client.patch("/providers/aws", json={
            "min_scaling": 2,
            "max_scaling": 5
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Provider 'aws' scaling configuration updated successfully"
        assert data["provider"]["scaling"]["min_scaling"] == 2
        assert data["provider"]["scaling"]["max_scaling"] == 5
        
        # Verify settings were actually updated in the config
        assert config["providers"]["aws"]["scaling"]["min_scaling"] == 2
        assert config["providers"]["aws"]["scaling"]["max_scaling"] == 5
    finally:
        # Restore original settings
        config["providers"]["aws"]["scaling"]["min_scaling"] = original_min
        config["providers"]["aws"]["scaling"]["max_scaling"] = original_max

# Edge cases and error handling
def test_random_no_proxies():
    """Test the /random endpoint when no proxies are available"""
    # Save original IPs
    original_do_ips = config["providers"]["digitalocean"]["ips"].copy()
    original_aws_ips = config["providers"]["aws"]["ips"].copy()
    original_gcp_ips = config["providers"]["gcp"]["ips"].copy()
    original_hetzner_ips = config["providers"]["hetzner"]["ips"].copy()
    
    try:
        # Clear all IPs
        config["providers"]["digitalocean"]["ips"] = []
        config["providers"]["aws"]["ips"] = []
        config["providers"]["gcp"]["ips"] = []
        config["providers"]["hetzner"]["ips"] = []
        
        response = client.get("/random")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "No proxies available"
    finally:
        # Restore original IPs
        config["providers"]["digitalocean"]["ips"] = original_do_ips
        config["providers"]["aws"]["ips"] = original_aws_ips
        config["providers"]["gcp"]["ips"] = original_gcp_ips
        config["providers"]["hetzner"]["ips"] = original_hetzner_ips

def test_provider_model_selection():
    """Test the provider model selection for different provider types"""
    from cloudproxy.main import get_provider_model
    
    # Test DigitalOcean provider
    do_config = {
        "enabled": True,
        "ips": ["1.1.1.1"],
        "scaling": {"min_scaling": 1, "max_scaling": 3},
        "size": "s-1vcpu-1gb",
        "region": "nyc1"
    }
    do_model = get_provider_model("digitalocean", do_config)
    assert do_model.region == "nyc1"
    
    # Test AWS provider
    aws_config = {
        "enabled": True,
        "ips": ["2.2.2.2"],
        "scaling": {"min_scaling": 1, "max_scaling": 3},
        "size": "t2.micro",
        "region": "us-east-1",
        "ami": "ami-12345",
        "spot": True
    }
    aws_model = get_provider_model("aws", aws_config)
    assert aws_model.region == "us-east-1"
    assert aws_model.ami == "ami-12345"
    assert aws_model.spot is True
    
    # Test GCP provider
    gcp_config = {
        "enabled": True,
        "ips": ["3.3.3.3"],
        "scaling": {"min_scaling": 1, "max_scaling": 3},
        "size": "e2-micro",
        "zone": "us-central1-a",
        "image_project": "debian-cloud",
        "image_family": "debian-10"
    }
    gcp_model = get_provider_model("gcp", gcp_config)
    assert gcp_model.zone == "us-central1-a"
    assert gcp_model.image_project == "debian-cloud"
    
    # Test Hetzner provider
    hetzner_config = {
        "enabled": True,
        "ips": ["4.4.4.4"],
        "scaling": {"min_scaling": 1, "max_scaling": 3},
        "size": "cx11",
        "location": "nbg1"
    }
    hetzner_model = get_provider_model("hetzner", hetzner_config)
    assert hetzner_model.location == "nbg1"
    
    # Test unknown provider (should return BaseProvider)
    unknown_config = {
        "enabled": True,
        "ips": ["5.5.5.5"],
        "scaling": {"min_scaling": 1, "max_scaling": 3},
        "size": "small",
        "region": "europe"
    }
    unknown_model = get_provider_model("unknown", unknown_config)
    assert unknown_model.region == "europe" 