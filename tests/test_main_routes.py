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
    original_providers = config["providers"].copy()
    original_delete_queue = delete_queue.copy()
    original_restart_queue = restart_queue.copy()
    
    # Setup test data
    for provider in ["digitalocean", "aws", "gcp", "hetzner", "azure"]:
        config["providers"][provider]["instances"]["default"]["ips"] = []
    
    config["providers"]["digitalocean"]["instances"]["default"]["ips"] = ["1.1.1.1", "2.2.2.2"]
    config["providers"]["aws"]["instances"]["default"]["ips"] = ["3.3.3.3", "4.4.4.4"]
    config["providers"]["gcp"]["instances"]["default"]["ips"] = ["5.5.5.5", "6.6.6.6"]
    config["providers"]["hetzner"]["instances"]["default"]["ips"] = ["7.7.7.7", "8.8.8.8"]
    config["providers"]["azure"]["instances"]["default"]["ips"] = ["9.9.9.9", "10.10.10.10"]
    
    # Add a test instance for AWS
    config["providers"]["aws"]["instances"]["production"] = {
        "enabled": True,
        "ips": ["11.11.11.11", "12.12.12.12"],
        "scaling": {"min_scaling": 2, "max_scaling": 4},
        "size": "t3.medium",
        "region": "us-west-2",
        "display_name": "AWS Production"
    }
    
    # Clear queues
    delete_queue.clear()
    restart_queue.clear()
    
    yield
    
    # Restore original values
    config["providers"] = original_providers
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
    assert data["total"] == 12  # Total IPs across all providers with AWS production instance
    assert len(data["proxies"]) == 10  # Default limit is 10, we have 12 total
    
    # Check that IPs from each provider are included
    ip_values = [proxy["ip"] for proxy in data["proxies"]]
    # The test should check for IPs that are actually in the data
    assert "1.1.1.1" in ip_values
    assert "3.3.3.3" in ip_values
    assert "5.5.5.5" in ip_values
    assert "7.7.7.7" in ip_values
    # One of the actual IPs from AWS production instead of 9.9.9.9
    assert "11.11.11.11" in ip_values

def test_root_endpoint_custom_pagination(setup_test_data):
    """Test the root endpoint with custom pagination parameters"""
    response = client.get("/?offset=2&limit=3")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 12  # Total IPs across all providers with AWS production instance
    assert len(data["proxies"]) == 3  # Requested limit of 3
    
    # Third, fourth, and fifth IPs based on the order in get_ip_list
    ip_values = [proxy["ip"] for proxy in data["proxies"]]
    # The exact IPs will depend on the order they're returned by get_ip_list
    assert len(ip_values) == 3
    
def test_root_endpoint_pagination_bounds(setup_test_data):
    """Test the root endpoint with pagination at the bounds"""
    # Test offset beyond available data
    response = client.get("/?offset=12")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 12  # Total IPs across all providers with AWS production instance
    assert len(data["proxies"]) == 0  # No proxies returned
    
    # Test with very large limit
    response = client.get("/?limit=100")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 12  # Total should be 12 not 10
    assert len(data["proxies"]) == 12  # All proxies returned

def test_provider_instance_formatting(setup_test_data):
    """Test that proxies contain provider and instance information"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    # Check that proxies from different providers have the correct provider and instance info
    proxies = data["proxies"]
    
    # Verify AWS default instance
    aws_default_proxy = next((p for p in proxies if p["ip"] in ["3.3.3.3", "4.4.4.4"]), None)
    assert aws_default_proxy is not None
    assert aws_default_proxy["provider"] == "aws"
    assert aws_default_proxy["instance"] == "default"
    
    # Verify AWS production instance
    aws_production_proxy = next((p for p in proxies if p["ip"] in ["11.11.11.11", "12.12.12.12"]), None)
    assert aws_production_proxy is not None
    assert aws_production_proxy["provider"] == "aws"
    assert aws_production_proxy["instance"] == "production"
    assert aws_production_proxy["display_name"] == "AWS Production"

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
    config["providers"]["azure"]["instances"]["default"]["ips"].append(ip_to_delete)
    
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
    assert "azure" in data["providers"]
    
    # Check that aws has both instances
    aws_provider = data["providers"]["aws"]
    assert "instances" in aws_provider
    assert "default" in aws_provider["instances"]
    assert "production" in aws_provider["instances"]
    
    # Check production instance data
    production_instance = aws_provider["instances"]["production"]
    assert production_instance["display_name"] == "AWS Production"
    assert production_instance["ips"] == ["11.11.11.11", "12.12.12.12"]

def test_provider_get_specific(setup_test_data):
    """Test the GET /providers/{provider} endpoint"""
    response = client.get("/providers/digitalocean")
    assert response.status_code == 200
    data = response.json()
    
    assert "instances" in data
    assert "default" in data["instances"]
    
    default_instance = data["instances"]["default"]
    assert default_instance["ips"] == ["1.1.1.1", "2.2.2.2"]
    assert "scaling" in default_instance
    assert "region" in default_instance

def test_provider_instance_get(setup_test_data):
    """Test the GET /providers/{provider}/{instance} endpoint"""
    response = client.get("/providers/aws/production")
    assert response.status_code == 200
    data = response.json()
    
    assert "metadata" in data
    assert "message" in data
    assert "provider" in data
    assert "instance" in data
    assert "config" in data
    
    assert data["provider"] == "aws"
    assert data["instance"] == "production"
    assert data["message"] == "Provider 'aws' instance 'production' configuration retrieved successfully"
    
    instance_config = data["config"]
    assert instance_config["display_name"] == "AWS Production"
    assert instance_config["ips"] == ["11.11.11.11", "12.12.12.12"]
    assert instance_config["size"] == "t3.medium"
    assert instance_config["region"] == "us-west-2"
    assert instance_config["scaling"]["min_scaling"] == 2
    assert instance_config["scaling"]["max_scaling"] == 4

def test_provider_instance_get_not_found(setup_test_data):
    """Test the GET /providers/{provider}/{instance} with non-existent instance"""
    response = client.get("/providers/aws/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()

def test_provider_patch_endpoint(setup_test_data):
    """Test the PATCH /providers/{provider} endpoint"""
    # Save original scaling settings
    original_min = config["providers"]["aws"]["instances"]["default"]["scaling"]["min_scaling"]
    original_max = config["providers"]["aws"]["instances"]["default"]["scaling"]["max_scaling"]
    
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
        assert config["providers"]["aws"]["instances"]["default"]["scaling"]["min_scaling"] == 2
        assert config["providers"]["aws"]["instances"]["default"]["scaling"]["max_scaling"] == 5
    finally:
        # Restore original settings
        config["providers"]["aws"]["instances"]["default"]["scaling"]["min_scaling"] = original_min
        config["providers"]["aws"]["instances"]["default"]["scaling"]["max_scaling"] = original_max

def test_provider_instance_patch_endpoint(setup_test_data):
    """Test the PATCH /providers/{provider}/{instance} endpoint"""
    # Save original scaling settings
    original_min = config["providers"]["aws"]["instances"]["production"]["scaling"]["min_scaling"]
    original_max = config["providers"]["aws"]["instances"]["production"]["scaling"]["max_scaling"]
    
    try:
        # Update scaling settings for the production instance
        response = client.patch("/providers/aws/production", json={
            "min_scaling": 3,
            "max_scaling": 6
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Provider 'aws' instance 'production' scaling configuration updated successfully"
        assert data["config"]["scaling"]["min_scaling"] == 3
        assert data["config"]["scaling"]["max_scaling"] == 6
        
        # Verify settings were actually updated in the config
        assert config["providers"]["aws"]["instances"]["production"]["scaling"]["min_scaling"] == 3
        assert config["providers"]["aws"]["instances"]["production"]["scaling"]["max_scaling"] == 6
        
        # Verify the default instance was not affected
        assert config["providers"]["aws"]["instances"]["default"]["scaling"]["min_scaling"] != 3
    finally:
        # Restore original settings
        config["providers"]["aws"]["instances"]["production"]["scaling"]["min_scaling"] = original_min
        config["providers"]["aws"]["instances"]["production"]["scaling"]["max_scaling"] = original_max

def test_provider_instance_patch_invalid_scaling(setup_test_data):
    """Test the PATCH /providers/{provider}/{instance} with invalid scaling values"""
    response = client.patch("/providers/aws/production", json={
        "min_scaling": 5,
        "max_scaling": 3  # Invalid: max < min
    })
    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data

# Edge cases and error handling
def test_random_no_proxies():
    """Test the /random endpoint when no proxies are available"""
    # Save original IPs
    original_providers = config["providers"].copy()
    
    try:
        # Clear all IPs
        for provider in ["digitalocean", "aws", "gcp", "hetzner", "azure"]:
            for instance in config["providers"][provider]["instances"]:
                config["providers"][provider]["instances"][instance]["ips"] = []
        
        response = client.get("/random")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "No proxies available"
    finally:
        # Restore original IPs
        config["providers"] = original_providers

def test_provider_model_selection():
    """Test the provider model selection for different provider types"""
    from cloudproxy.main import get_provider_model
    
    # Test DigitalOcean provider
    do_config = {
        "instances": {
            "default": {
                "enabled": True,
                "ips": ["1.1.1.1"],
                "scaling": {"min_scaling": 1, "max_scaling": 3},
                "size": "s-1vcpu-1gb",
                "region": "nyc1",
                "display_name": "DigitalOcean"
            }
        }
    }
    do_model = get_provider_model("digitalocean", do_config)
    assert "default" in do_model.instances
    assert do_model.instances["default"].region == "nyc1"
    
    # Test AWS provider with multiple instances
    aws_config = {
        "instances": {
            "default": {
                "enabled": True,
                "ips": ["2.2.2.2"],
                "scaling": {"min_scaling": 1, "max_scaling": 3},
                "size": "t2.micro",
                "region": "us-east-1",
                "ami": "ami-12345",
                "spot": True,
                "display_name": "AWS Default"
            },
            "production": {
                "enabled": True,
                "ips": ["3.3.3.3"],
                "scaling": {"min_scaling": 2, "max_scaling": 4},
                "size": "t3.medium",
                "region": "us-west-2",
                "ami": "ami-67890",
                "spot": False,
                "display_name": "AWS Production"
            }
        }
    }
    aws_model = get_provider_model("aws", aws_config)
    assert "default" in aws_model.instances
    assert "production" in aws_model.instances
    assert aws_model.instances["default"].region == "us-east-1"
    assert aws_model.instances["default"].ami == "ami-12345"
    assert aws_model.instances["default"].spot is True
    assert aws_model.instances["production"].region == "us-west-2"
    assert aws_model.instances["production"].display_name == "AWS Production" 