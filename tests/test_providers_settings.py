import os
import pytest
from cloudproxy.providers.settings import config, delete_queue, restart_queue

@pytest.fixture
def reset_env():
    """Fixture to reset environment variables after test"""
    saved_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved_env)

def test_basic_config_structure():
    """Test that the basic config structure exists"""
    assert "auth" in config
    assert "providers" in config
    assert "aws" in config["providers"]
    assert "digitalocean" in config["providers"]
    assert "gcp" in config["providers"]
    assert "hetzner" in config["providers"]
    assert "azure" in config["providers"]

def test_delete_and_restart_queues():
    """Test that delete and restart queues are initialized as sets"""
    assert isinstance(delete_queue, set)
    assert isinstance(restart_queue, set)
    # Note: We don't check if they're empty since they might have values
    # from previous test runs or other module initialization

def test_additional_instance_creation(reset_env):
    """Test creation of additional instances for providers using the new format pattern"""
    # Set environment variables for a new AWS instance
    os.environ["AWS_INSTANCE_TEST1_ENABLED"] = "True"
    os.environ["AWS_INSTANCE_TEST1_SIZE"] = "t3.micro"
    os.environ["AWS_INSTANCE_TEST1_REGION"] = "us-east-1"
    os.environ["AWS_INSTANCE_TEST1_MIN_SCALING"] = "3"
    os.environ["AWS_INSTANCE_TEST1_MAX_SCALING"] = "5"
    os.environ["AWS_INSTANCE_TEST1_DISPLAY_NAME"] = "AWS Test Instance"
    os.environ["AWS_INSTANCE_TEST1_ACCESS_KEY_ID"] = "test-key-id"
    os.environ["AWS_INSTANCE_TEST1_SECRET_ACCESS_KEY"] = "test-secret-key"
    os.environ["AWS_INSTANCE_TEST1_AMI"] = "ami-test123"
    os.environ["AWS_INSTANCE_TEST1_SPOT"] = "True"

    # Import the module again to reload configuration
    import importlib
    import cloudproxy.providers.settings
    importlib.reload(cloudproxy.providers.settings)
    from cloudproxy.providers.settings import config

    # Verify the new instance was created
    assert "test1" in config["providers"]["aws"]["instances"]
    test_instance = config["providers"]["aws"]["instances"]["test1"]
    
    # Verify all properties were set correctly
    assert test_instance["enabled"] is True
    assert test_instance["size"] == "t3.micro"
    assert test_instance["region"] == "us-east-1"
    assert test_instance["scaling"]["min_scaling"] == 3
    assert test_instance["scaling"]["max_scaling"] == 5
    assert test_instance["display_name"] == "AWS Test Instance"
    assert test_instance["secrets"]["access_key_id"] == "test-key-id"
    assert test_instance["secrets"]["secret_access_key"] == "test-secret-key"
    assert test_instance["ami"] == "ami-test123"
    assert test_instance["spot"] is True

def test_multiple_provider_instances(reset_env):
    """Test creation of additional instances for multiple providers"""
    # Set environment variables for AWS and GCP instances
    os.environ["AWS_INSTANCE_TEST2_ENABLED"] = "True"
    os.environ["AWS_INSTANCE_TEST2_SIZE"] = "t2.small"
    
    os.environ["GCP_INSTANCE_TEST1_ENABLED"] = "True"
    os.environ["GCP_INSTANCE_TEST1_SIZE"] = "n1-standard-1"
    os.environ["GCP_INSTANCE_TEST1_ZONE"] = "us-west1-b"
    os.environ["GCP_INSTANCE_TEST1_PROJECT"] = "test-project"
    os.environ["GCP_INSTANCE_TEST1_SERVICE_ACCOUNT_KEY"] = "test-key-content"
    
    # Import the module again to reload configuration
    import importlib
    import cloudproxy.providers.settings
    importlib.reload(cloudproxy.providers.settings)
    from cloudproxy.providers.settings import config
    
    # Verify AWS instance
    assert "test2" in config["providers"]["aws"]["instances"]
    aws_instance = config["providers"]["aws"]["instances"]["test2"]
    assert aws_instance["enabled"] is True
    assert aws_instance["size"] == "t2.small"
    
    # Verify GCP instance
    assert "test1" in config["providers"]["gcp"]["instances"]
    gcp_instance = config["providers"]["gcp"]["instances"]["test1"]
    assert gcp_instance["enabled"] is True
    assert gcp_instance["size"] == "n1-standard-1"
    assert gcp_instance["zone"] == "us-west1-b"
    assert gcp_instance["project"] == "test-project"
    assert gcp_instance["secrets"]["service_account_key"] == "test-key-content"

def test_backward_compatibility(reset_env):
    """Test that top-level properties are maintained for backward compatibility"""
    # Set up environment variables for default instances
    os.environ["AWS_ENABLED"] = "True"
    os.environ["AWS_SIZE"] = "t2.large"
    
    # Import the module again to reload configuration
    import importlib
    import cloudproxy.providers.settings
    importlib.reload(cloudproxy.providers.settings)
    from cloudproxy.providers.settings import config
    
    # Verify that top-level properties match the default instance
    assert config["providers"]["aws"]["enabled"] == config["providers"]["aws"]["instances"]["default"]["enabled"]
    assert config["providers"]["aws"]["size"] == config["providers"]["aws"]["instances"]["default"]["size"]
    assert config["providers"]["aws"]["size"] == "t2.large" 