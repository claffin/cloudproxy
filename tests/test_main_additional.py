from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch
import os

from cloudproxy.main import app, custom_openapi, main, get_ip_list
from cloudproxy.providers.settings import delete_queue, restart_queue, config

# Create test client
client = TestClient(app)

def test_random_with_proxies():
    """Test the /random endpoint when proxies are available"""
    # Add a mock proxy to the IP list temporarily
    original_ip_list = config["providers"]["digitalocean"]["ips"].copy()
    config["providers"]["digitalocean"]["ips"] = ["192.168.1.10"]
    
    try:
        response = client.get("/random")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "message" in data
        assert "proxy" in data
        assert data["message"] == "Random proxy retrieved successfully"
        assert data["proxy"]["ip"] == "192.168.1.10"
    finally:
        # Restore original IP list
        config["providers"]["digitalocean"]["ips"] = original_ip_list

def test_custom_openapi():
    """Test custom OpenAPI schema generation"""
    # First call should create and return schema
    schema = custom_openapi()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "CloudProxy API"
    
    # Second call should return the cached schema
    cached_schema = custom_openapi()
    assert cached_schema is schema

def test_custom_swagger_ui_html():
    """Test Swagger UI HTML endpoint"""
    response = client.get("/docs")
    assert response.status_code == 200
    # Check that the response contains HTML with Swagger UI elements
    assert b"swagger-ui" in response.content
    assert b"openapi.json" in response.content

def test_openapi_json():
    """Test OpenAPI JSON endpoint"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
    assert "info" in data
    assert data["info"]["title"] == "CloudProxy API"

def test_static_files_error_handling():
    """Test error handling for static files"""
    # This tests that our fix for the GitHub workflow issue works properly
    # We should get a 404 instead of a server error
    response = client.get("/ui/nonexistent-file")
    assert response.status_code in (404, 307)  # Either 404 or redirect to index

def test_auth_endpoint():
    """Test authentication settings endpoint"""
    # Set test values
    original_username = config["auth"]["username"]
    original_password = config["auth"]["password"]
    original_no_auth = config["no_auth"]
    
    try:
        config["auth"]["username"] = "test_user"
        config["auth"]["password"] = "test_pass"
        config["no_auth"] = False
        
        response = client.get("/auth")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_user"
        assert data["password"] == "test_pass"
        assert data["auth_enabled"] is True
    finally:
        # Restore original values
        config["auth"]["username"] = original_username
        config["auth"]["password"] = original_password
        config["no_auth"] = original_no_auth

def test_get_ip_list():
    """Test the get_ip_list function with various provider configurations"""
    # Setup test data
    original_do_ips = config["providers"]["digitalocean"]["ips"].copy()
    original_aws_ips = config["providers"]["aws"]["ips"].copy()
    original_gcp_ips = config["providers"]["gcp"]["ips"].copy()
    original_hetzner_ips = config["providers"]["hetzner"]["ips"].copy()
    original_delete_queue = delete_queue.copy()
    original_restart_queue = restart_queue.copy()
    
    try:
        # Set test values
        config["providers"]["digitalocean"]["ips"] = ["1.1.1.1", "2.2.2.2"]
        config["providers"]["aws"]["ips"] = ["3.3.3.3"]
        config["providers"]["gcp"]["ips"] = ["4.4.4.4"]
        config["providers"]["hetzner"]["ips"] = ["5.5.5.5"]
        config["no_auth"] = False
        
        # Empty queues
        delete_queue.clear()
        restart_queue.clear()
        
        # Test with no IPs in queues
        result = get_ip_list()
        assert len(result) == 5
        ip_values = [str(proxy.ip) for proxy in result]
        assert "1.1.1.1" in ip_values
        assert "3.3.3.3" in ip_values
        assert "5.5.5.5" in ip_values
        
        # Test with some IPs in delete queue
        delete_queue.add("1.1.1.1")
        restart_queue.add("4.4.4.4")
        result = get_ip_list()
        assert len(result) == 3
        ip_values = [str(proxy.ip) for proxy in result]
        assert "1.1.1.1" not in ip_values  # Should be filtered out
        assert "4.4.4.4" not in ip_values  # Should be filtered out
        
    finally:
        # Restore original data
        config["providers"]["digitalocean"]["ips"] = original_do_ips
        config["providers"]["aws"]["ips"] = original_aws_ips
        config["providers"]["gcp"]["ips"] = original_gcp_ips
        config["providers"]["hetzner"]["ips"] = original_hetzner_ips
        delete_queue.clear()
        delete_queue.update(original_delete_queue)
        restart_queue.clear()
        restart_queue.update(original_restart_queue)

def test_error_responses():
    """Test that API returns proper error responses"""
    # Test invalid IP address
    response = client.delete("/destroy?ip_address=invalid-ip")
    assert response.status_code == 422
    
    # Test provider not found
    response = client.get("/providers/nonexistent")
    assert response.status_code == 404
    assert "Provider 'nonexistent' not found" in response.json()["detail"]
    
    # Test invalid provider update
    response = client.patch("/providers/digitalocean", json={
        "min_scaling": 10,
        "max_scaling": 5  # Invalid: max should be >= min
    })
    assert response.status_code == 422

@patch("uvicorn.run")
def test_main_function(mock_run):
    """Test the main function that starts the server"""
    # Call the main function
    main()
    
    # Verify that uvicorn.run was called with the correct parameters
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 8000
    assert kwargs["log_level"] == "info" 