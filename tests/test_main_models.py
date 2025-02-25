import pytest
from unittest.mock import patch
from datetime import datetime
from pydantic import ValidationError

from cloudproxy.main import (
    Metadata, 
    ProxyAddress,
    ProxyList,
    ProxyResponse,
    ErrorResponse,
    ProviderScaling,
    BaseProvider,
    DigitalOceanProvider,
    AWSProvider,
    GCPProvider,
    HetznerProvider,
    ProviderUpdateRequest
)
from cloudproxy.providers import settings

# Tests for Metadata model
def test_metadata_default_values():
    """Test that Metadata model has proper default values"""
    metadata = Metadata()
    
    # Check that request_id is a valid UUID string
    assert isinstance(metadata.request_id, str)
    assert len(metadata.request_id) > 0
    
    # Check that timestamp is a datetime
    assert isinstance(metadata.timestamp, datetime)
    
    # Each instance should have a different request_id
    another_metadata = Metadata()
    assert metadata.request_id != another_metadata.request_id

# Tests for ProxyAddress model
def test_proxy_address_defaults():
    """Test ProxyAddress model with default values"""
    proxy = ProxyAddress(ip="192.168.1.1")
    
    assert str(proxy.ip) == "192.168.1.1"
    assert proxy.port == 8899
    assert proxy.auth_enabled is True

def test_proxy_address_custom_values():
    """Test ProxyAddress model with custom values"""
    proxy = ProxyAddress(
        ip="192.168.1.1", 
        port=8080, 
        auth_enabled=False
    )
    
    assert str(proxy.ip) == "192.168.1.1"
    assert proxy.port == 8080
    assert proxy.auth_enabled is False

# Test the model integration with config values
def test_create_proxy_address():
    """Test the create_proxy_address helper function"""
    from cloudproxy.main import create_proxy_address
    
    # Save original no_auth setting
    original_no_auth = settings.config["no_auth"]
    
    try:
        # Test with auth enabled
        settings.config["no_auth"] = False
        proxy = create_proxy_address("192.168.1.1")
        assert str(proxy.ip) == "192.168.1.1"
        assert proxy.auth_enabled is True
        
        # Test with auth disabled
        settings.config["no_auth"] = True
        proxy = create_proxy_address("192.168.1.1")
        assert str(proxy.ip) == "192.168.1.1"
        assert proxy.auth_enabled is False
    finally:
        # Restore original setting
        settings.config["no_auth"] = original_no_auth

# Tests for ProxyList model
def test_proxy_list():
    """Test ProxyList model"""
    proxy1 = ProxyAddress(ip="192.168.1.1")
    proxy2 = ProxyAddress(ip="192.168.1.2")
    
    proxy_list = ProxyList(total=2, proxies=[proxy1, proxy2])
    
    assert proxy_list.total == 2
    assert len(proxy_list.proxies) == 2
    assert isinstance(proxy_list.metadata, Metadata)
    assert str(proxy_list.proxies[0].ip) == "192.168.1.1"
    assert str(proxy_list.proxies[1].ip) == "192.168.1.2"

# Tests for ProxyResponse model
def test_proxy_response():
    """Test ProxyResponse model"""
    proxy = ProxyAddress(ip="192.168.1.1")
    
    response = ProxyResponse(message="Test message", proxy=proxy)
    
    assert response.message == "Test message"
    assert str(response.proxy.ip) == "192.168.1.1"
    assert isinstance(response.metadata, Metadata)

# Tests for ErrorResponse model
def test_error_response():
    """Test ErrorResponse model"""
    error = ErrorResponse(error="Test error", detail="Error details")
    
    assert error.error == "Test error"
    assert error.detail == "Error details"
    assert isinstance(error.metadata, Metadata)

# Tests for ProviderScaling model
def test_provider_scaling():
    """Test ProviderScaling model"""
    scaling = ProviderScaling(min_scaling=1, max_scaling=5)
    
    assert scaling.min_scaling == 1
    assert scaling.max_scaling == 5

def test_provider_scaling_validation():
    """Test ProviderScaling model validation"""
    # Invalid scaling value (negative)
    with pytest.raises(ValidationError):
        ProviderScaling(min_scaling=-1, max_scaling=5)
    
    # Invalid scaling value (negative)
    with pytest.raises(ValidationError):
        ProviderScaling(min_scaling=1, max_scaling=-5)

# Tests for provider models
def test_base_provider():
    """Test BaseProvider model"""
    provider = BaseProvider(
        enabled=True,
        ips=["192.168.1.1", "192.168.1.2"],
        scaling={"min_scaling": 1, "max_scaling": 3},
        size="small",
        region="europe"
    )
    
    assert provider.enabled is True
    assert provider.ips == ["192.168.1.1", "192.168.1.2"]
    assert provider.scaling.min_scaling == 1
    assert provider.scaling.max_scaling == 3
    assert provider.size == "small"
    assert provider.region == "europe"

def test_digitalocean_provider():
    """Test DigitalOceanProvider model"""
    provider = DigitalOceanProvider(
        enabled=True,
        ips=["192.168.1.1"],
        scaling={"min_scaling": 1, "max_scaling": 3},
        size="s-1vcpu-1gb",
        region="nyc1"
    )
    
    assert provider.enabled is True
    assert provider.ips == ["192.168.1.1"]
    assert provider.scaling.min_scaling == 1
    assert provider.scaling.max_scaling == 3
    assert provider.size == "s-1vcpu-1gb"
    assert provider.region == "nyc1"

def test_aws_provider():
    """Test AWSProvider model"""
    provider = AWSProvider(
        enabled=True,
        ips=["192.168.1.1"],
        scaling={"min_scaling": 1, "max_scaling": 3},
        size="t2.micro",
        region="us-east-1",
        ami="ami-12345",
        spot=True
    )
    
    assert provider.enabled is True
    assert provider.ips == ["192.168.1.1"]
    assert provider.scaling.min_scaling == 1
    assert provider.scaling.max_scaling == 3
    assert provider.size == "t2.micro"
    assert provider.region == "us-east-1"
    assert provider.ami == "ami-12345"
    assert provider.spot is True

def test_gcp_provider():
    """Test GCPProvider model"""
    provider = GCPProvider(
        enabled=True,
        ips=["192.168.1.1"],
        scaling={"min_scaling": 1, "max_scaling": 3},
        size="e2-micro",
        zone="us-central1-a",
        image_project="debian-cloud",
        image_family="debian-10"
    )
    
    assert provider.enabled is True
    assert provider.ips == ["192.168.1.1"]
    assert provider.scaling.min_scaling == 1
    assert provider.scaling.max_scaling == 3
    assert provider.size == "e2-micro"
    assert provider.zone == "us-central1-a"
    assert provider.image_project == "debian-cloud"
    assert provider.image_family == "debian-10"

def test_hetzner_provider():
    """Test HetznerProvider model"""
    provider = HetznerProvider(
        enabled=True,
        ips=["192.168.1.1"],
        scaling={"min_scaling": 1, "max_scaling": 3},
        size="cx11",
        location="nbg1"
    )
    
    assert provider.enabled is True
    assert provider.ips == ["192.168.1.1"]
    assert provider.scaling.min_scaling == 1
    assert provider.scaling.max_scaling == 3
    assert provider.size == "cx11"
    assert provider.location == "nbg1"

# Tests for ProviderUpdateRequest model
def test_provider_update_request():
    """Test ProviderUpdateRequest model with valid values"""
    update = ProviderUpdateRequest(min_scaling=1, max_scaling=5)
    
    assert update.min_scaling == 1
    assert update.max_scaling == 5

def test_provider_update_request_validation():
    """Test ProviderUpdateRequest model validation for max_scaling"""
    # Valid: max_scaling equals min_scaling
    update = ProviderUpdateRequest(min_scaling=5, max_scaling=5)
    assert update.min_scaling == 5
    assert update.max_scaling == 5
    
    # Invalid: max_scaling less than min_scaling
    with pytest.raises(ValidationError):
        ProviderUpdateRequest(min_scaling=5, max_scaling=2) 