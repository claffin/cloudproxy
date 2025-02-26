import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from cloudproxy.main import app
from cloudproxy.providers import settings

client = TestClient(app)


@pytest.fixture
def mock_providers_config(monkeypatch):
    """Fixture for mock provider configuration."""
    mock_config = {
        "providers": {
            "digitalocean": {
                "enabled": True,
                "ips": ["192.168.1.1", "192.168.1.2", "192.168.2.1", "192.168.2.2"],  # Combined IPs from all instances
                "instances": {
                    "default": {
                        "enabled": True,
                        "secrets": {"access_token": "default-do-token"},
                        "size": "s-1vcpu-1gb",
                        "region": "lon1",
                        "min_scaling": 2,
                        "max_scaling": 5,
                        "display_name": "London DO",
                        "ips": ["192.168.1.1", "192.168.1.2"],
                        "scaling": {"min_scaling": 2, "max_scaling": 5}
                    },
                    "nyc": {
                        "enabled": True,
                        "secrets": {"access_token": "nyc-do-token"},
                        "size": "s-1vcpu-1gb",
                        "region": "nyc1",
                        "min_scaling": 1,
                        "max_scaling": 3,
                        "display_name": "New York DO",
                        "ips": ["192.168.2.1", "192.168.2.2"],
                        "scaling": {"min_scaling": 1, "max_scaling": 3}
                    }
                }
            },
            "aws": {
                "enabled": True,
                "ips": ["10.0.1.1", "10.0.1.2", "10.0.2.1", "10.0.2.2"],  # Combined IPs from all instances
                "instances": {
                    "default": {
                        "enabled": True,
                        "secrets": {
                            "access_key_id": "default-aws-key",
                            "secret_access_key": "default-aws-secret"
                        },
                        "size": "t2.micro",
                        "region": "us-east-1",
                        "min_scaling": 2,
                        "max_scaling": 4,
                        "spot": False,
                        "display_name": "US East AWS",
                        "ips": ["10.0.1.1", "10.0.1.2"],
                        "scaling": {"min_scaling": 2, "max_scaling": 4}
                    },
                    "eu": {
                        "enabled": True,
                        "secrets": {
                            "access_key_id": "eu-aws-key",
                            "secret_access_key": "eu-aws-secret"
                        },
                        "size": "t2.micro",
                        "region": "eu-west-1",
                        "min_scaling": 1,
                        "max_scaling": 2,
                        "spot": True,
                        "display_name": "EU West AWS",
                        "ips": ["10.0.2.1", "10.0.2.2"],
                        "scaling": {"min_scaling": 1, "max_scaling": 2}
                    }
                }
            },
            "hetzner": {
                "enabled": True,
                "ips": ["172.16.1.1", "172.16.1.2"],  # Combined IPs from all instances
                "instances": {
                    "default": {
                        "enabled": True,
                        "secrets": {"access_token": "default-hetzner-token"},
                        "size": "cx11",
                        "location": "nbg1",
                        "min_scaling": 2,
                        "max_scaling": 3,
                        "display_name": "Germany Hetzner",
                        "ips": ["172.16.1.1", "172.16.1.2"],
                        "scaling": {"min_scaling": 2, "max_scaling": 3}
                    }
                }
            },
            "gcp": {
                "enabled": False,
                "zone": "us-east1-b",
                "image_project": "debian-cloud",
                "image_family": "debian-11",
                "ips": [],  # No IPs since it's disabled
                "scaling": {"min_scaling": 0, "max_scaling": 0},
                "size": "e2-small",
                "instances": {
                    "default": {
                        "enabled": False,
                        "secrets": {"json_key": "mock-gcp-key"},
                        "zone": "us-east1-b",
                        "image_project": "debian-cloud",
                        "image_family": "debian-11",
                        "size": "e2-small",
                        "min_scaling": 0,
                        "max_scaling": 0,
                        "display_name": "US East GCP",
                        "ips": [],
                        "scaling": {"min_scaling": 0, "max_scaling": 0}
                    }
                }
            }
        }
    }
    
    monkeypatch.setattr(settings, "config", mock_config)
    return mock_config["providers"]


@pytest.fixture
def mock_provider_ips():
    """Fixture for mock provider IPs."""
    # Original provider IPs
    original_ips = {
        provider: {
            instance: settings.config["providers"][provider]["instances"][instance].get("ips", []).copy()
            for instance in settings.config["providers"][provider]["instances"]
        } 
        for provider in settings.config["providers"]
        if provider in settings.config["providers"]
    }
    
    # Set mock IPs for each provider instance
    mock_ips = {
        "digitalocean": {
            "default": ["192.168.1.1", "192.168.1.2"],
            "nyc": ["192.168.2.1", "192.168.2.2"]
        },
        "aws": {
            "default": ["10.0.1.1", "10.0.1.2"],
            "eu": ["10.0.2.1", "10.0.2.2"]
        },
        "hetzner": {
            "default": ["172.16.1.1", "172.16.1.2"]
        }
    }
    
    # Update config with mock IPs
    for provider, instances in mock_ips.items():
        for instance, ips in instances.items():
            settings.config["providers"][provider]["instances"][instance]["ips"] = ips
    
    yield mock_ips
    
    # Restore original IPs
    for provider, instances in original_ips.items():
        for instance, ips in instances.items():
            if provider in settings.config["providers"] and instance in settings.config["providers"][provider]["instances"]:
                settings.config["providers"][provider]["instances"][instance]["ips"] = ips


def test_get_providers_list(mock_providers_config, mock_provider_ips):
    """Test retrieving the list of all providers with their instances."""
    response = client.get("/providers")
    assert response.status_code == 200
    
    data = response.json()
    assert "metadata" in data
    assert "providers" in data
    
    providers = data["providers"]
    
    # Check DigitalOcean provider
    assert "digitalocean" in providers
    digitalocean = providers["digitalocean"]
    assert digitalocean["enabled"] is True
    assert len(digitalocean["ips"]) == 4  # Combined IPs from all instances
    assert "instances" in digitalocean
    
    # Check DigitalOcean instances
    do_instances = digitalocean["instances"]
    assert "default" in do_instances
    assert "nyc" in do_instances
    assert do_instances["default"]["display_name"] == "London DO"
    assert do_instances["nyc"]["display_name"] == "New York DO"
    
    # Check AWS provider
    assert "aws" in providers
    aws = providers["aws"]
    assert aws["enabled"] is True
    assert len(aws["ips"]) == 4  # Combined IPs from all instances
    
    # Check AWS instances
    aws_instances = aws["instances"]
    assert "default" in aws_instances
    assert "eu" in aws_instances
    assert aws_instances["default"]["display_name"] == "US East AWS"
    assert aws_instances["eu"]["display_name"] == "EU West AWS"
    assert aws_instances["eu"]["spot"] is True


def test_get_provider_details(mock_providers_config, mock_provider_ips):
    """Test retrieving details for a specific provider with all its instances."""
    response = client.get("/providers/digitalocean")
    assert response.status_code == 200
    
    data = response.json()
    assert "metadata" in data
    assert "message" in data
    assert "provider" in data
    assert "instances" in data
    
    # Check provider details
    provider = data["provider"]
    assert provider["enabled"] is True
    assert len(provider["ips"]) == 4  # Combined IPs from all instances
    
    # Check instances details
    instances = data["instances"]
    assert "default" in instances
    assert "nyc" in instances
    
    default_instance = instances["default"]
    assert default_instance["enabled"] is True
    assert default_instance["region"] == "lon1"
    assert default_instance["size"] == "s-1vcpu-1gb"
    assert default_instance["min_scaling"] == 2
    assert default_instance["max_scaling"] == 5
    assert default_instance["display_name"] == "London DO"
    assert len(default_instance["ips"]) == 2
    
    nyc_instance = instances["nyc"]
    assert nyc_instance["enabled"] is True
    assert nyc_instance["region"] == "nyc1"
    assert nyc_instance["min_scaling"] == 1
    assert nyc_instance["max_scaling"] == 3
    assert nyc_instance["display_name"] == "New York DO"
    assert len(nyc_instance["ips"]) == 2


def test_get_provider_instance_details(mock_providers_config, mock_provider_ips):
    """Test retrieving details for a specific instance of a provider."""
    response = client.get("/providers/aws/eu")
    assert response.status_code == 200
    
    data = response.json()
    assert "metadata" in data
    assert "message" in data
    assert "provider" in data
    assert "instance" in data
    assert "config" in data
    
    # Check response structure
    assert data["provider"] == "aws"
    assert data["instance"] == "eu"
    
    # Check instance config
    config = data["config"]
    assert config["enabled"] is True
    assert config["region"] == "eu-west-1"
    assert config["size"] == "t2.micro"
    assert config["spot"] is True
    assert "scaling" in config
    assert config["scaling"]["min_scaling"] == 1
    assert config["scaling"]["max_scaling"] == 2
    assert config["display_name"] == "EU West AWS"
    assert len(config["ips"]) == 2
    assert config["ips"] == mock_provider_ips["aws"]["eu"]


def test_update_provider_instance_scaling(mock_providers_config):
    """Test updating scaling configuration for a provider instance."""
    # Data to send
    update_data = {
        "min_scaling": 3,
        "max_scaling": 5
    }
    
    response = client.patch("/providers/aws/eu", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "updated successfully" in data["message"]
    assert "aws" in data["message"]
    assert "eu" in data["message"]
    
    # Verify config was updated
    config = data["config"]
    assert config["scaling"]["min_scaling"] == 3
    assert config["scaling"]["max_scaling"] == 5
    
    # Verify actual settings were updated
    assert settings.config["providers"]["aws"]["instances"]["eu"]["scaling"]["min_scaling"] == 3
    assert settings.config["providers"]["aws"]["instances"]["eu"]["scaling"]["max_scaling"] == 5


def test_update_provider_instance_scaling_validation_error(mock_providers_config):
    """Test validation error when max_scaling < min_scaling."""
    # Invalid data to send
    update_data = {
        "min_scaling": 5,
        "max_scaling": 3  # Less than min_scaling
    }
    
    response = client.patch("/providers/aws/eu", json=update_data)
    assert response.status_code == 422  # Unprocessable Entity
    
    data = response.json()
    assert "detail" in data
    
    # Original values should remain unchanged
    assert settings.config["providers"]["aws"]["instances"]["eu"]["min_scaling"] == 1
    assert settings.config["providers"]["aws"]["instances"]["eu"]["max_scaling"] == 2


def test_get_nonexistent_provider():
    """Test retrieving a provider that doesn't exist."""
    response = client.get("/providers/nonexistent")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "nonexistent" in data["detail"]


def test_get_nonexistent_provider_instance():
    """Test retrieving an instance that doesn't exist for a provider."""
    response = client.get("/providers/aws/nonexistent")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
    assert "nonexistent" in data["detail"]


@patch('cloudproxy.main.get_provider_model')
def test_provider_models_with_instances(mock_get_provider_model, mock_providers_config):
    """Test that provider models include instances data."""
    # Create a real BaseProvider object instead of a MagicMock
    from cloudproxy.main import BaseProvider, ProviderScaling, ProviderInstance
    
    # Create a proper provider model for each provider
    def get_mock_provider(provider_name, provider_config):
        provider = BaseProvider(
            enabled=True,
            ips=[],
            region="us-east-1",
            size="t2.micro",
            image="",
            scaling=ProviderScaling(min_scaling=2, max_scaling=5),
            instances={}
        )
        # Add test instance to the provider
        provider.instances["default"] = ProviderInstance(
            enabled=True,
            ips=[],
            scaling=ProviderScaling(min_scaling=2, max_scaling=5),
            size="t2.micro",
            region="us-east-1",
            display_name="Test Instance"
        )
        return provider
    
    # Configure the mock to return our proper provider object
    mock_get_provider_model.side_effect = get_mock_provider
    
    # Make a request to trigger provider model creation
    response = client.get("/providers")
    
    # Verify response
    assert response.status_code == 200
    assert "providers" in response.json() 