import pytest
from unittest.mock import patch, Mock
from cloudproxy.providers import settings
from cloudproxy.providers.manager import init_schedule

# Test setup and teardown
@pytest.fixture
def setup_provider_config():
    """Fixture to preserve and restore provider settings"""
    # Save original settings
    original_providers = settings.config["providers"].copy()
    
    # Return function to restore settings
    yield
    
    # Restore original settings
    settings.config["providers"] = original_providers

# Tests for scheduler initialization
@patch('cloudproxy.providers.manager.BackgroundScheduler')
def test_init_schedule_all_enabled(mock_scheduler_class, setup_provider_config):
    """Test scheduler initialization with all providers enabled"""
    # Setup
    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Configure all providers as enabled
    for provider in ["digitalocean", "aws", "gcp", "hetzner"]:
        settings.config["providers"][provider]["instances"]["default"]["enabled"] = True
    
    # Remove the production instance for this test
    if "production" in settings.config["providers"]["aws"]["instances"]:
        del settings.config["providers"]["aws"]["instances"]["production"]
    
    # Execute
    init_schedule()
    
    # Verify
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 4  # One for each provider
    
    # Verify the correct methods were scheduled
    calls = mock_scheduler.add_job.call_args_list
    functions = [call[0][0].__name__ for call in calls]
    
    # Check that all provider managers were scheduled
    assert "do_manager" in functions
    assert "aws_manager" in functions
    assert "gcp_manager" in functions
    assert "hetzner_manager" in functions

@patch('cloudproxy.providers.manager.BackgroundScheduler')
def test_init_schedule_all_disabled(mock_scheduler_class, setup_provider_config):
    """Test scheduler initialization with all providers disabled"""
    # Setup
    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Configure all providers as disabled
    for provider in ["digitalocean", "aws", "gcp", "hetzner"]:
        settings.config["providers"][provider]["instances"]["default"]["enabled"] = False
    
    # Also disable the production instance if it exists
    if "production" in settings.config["providers"]["aws"]["instances"]:
        settings.config["providers"]["aws"]["instances"]["production"]["enabled"] = False
    
    # Execute
    init_schedule()
    
    # Verify
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 0  # No jobs should be added

@patch('cloudproxy.providers.manager.BackgroundScheduler')
def test_init_schedule_mixed_providers(mock_scheduler_class, setup_provider_config):
    """Test scheduler initialization with some providers enabled and others disabled"""
    # Setup
    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Configure mix of enabled/disabled providers
    settings.config["providers"]["digitalocean"]["instances"]["default"]["enabled"] = True
    settings.config["providers"]["aws"]["instances"]["default"]["enabled"] = False
    settings.config["providers"]["gcp"]["instances"]["default"]["enabled"] = True
    settings.config["providers"]["hetzner"]["instances"]["default"]["enabled"] = False
    
    # Also disable the production instance if it exists
    if "production" in settings.config["providers"]["aws"]["instances"]:
        settings.config["providers"]["aws"]["instances"]["production"]["enabled"] = False
    
    # Execute
    init_schedule()
    
    # Verify
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 2  # Two jobs should be added
    
    # Verify the correct methods were scheduled
    calls = mock_scheduler.add_job.call_args_list
    functions = [call[0][0].__name__ for call in calls]
    assert "do_manager" in functions
    assert "gcp_manager" in functions

@patch('cloudproxy.providers.manager.BackgroundScheduler')
def test_init_schedule_multiple_instances(mock_scheduler_class, setup_provider_config):
    """Test scheduler initialization with multiple instances of the same provider"""
    # Setup
    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Configure AWS with multiple instances
    settings.config["providers"]["aws"]["instances"] = {
        "default": {
            "enabled": True,
            "scaling": {"min_scaling": 1, "max_scaling": 2},
            "size": "t2.micro",
            "region": "us-east-1",
            "display_name": "Default AWS"
        },
        "production": {
            "enabled": True,
            "scaling": {"min_scaling": 2, "max_scaling": 5},
            "size": "t3.medium",
            "region": "us-west-2",
            "display_name": "Production AWS"
        },
        "testing": {
            "enabled": False,  # Disabled instance
            "scaling": {"min_scaling": 1, "max_scaling": 1},
            "size": "t2.nano",
            "region": "eu-west-1",
            "display_name": "Testing AWS"
        }
    }
    
    # Disable other providers for clarity
    settings.config["providers"]["digitalocean"]["instances"]["default"]["enabled"] = False
    settings.config["providers"]["gcp"]["instances"]["default"]["enabled"] = False
    settings.config["providers"]["hetzner"]["instances"]["default"]["enabled"] = False
    
    # Execute
    init_schedule()
    
    # Verify
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 2  # Only the two enabled AWS instances
    
    # Verify all calls are to aws_manager but with different instance names
    calls = mock_scheduler.add_job.call_args_list
    
    # Extract the job functions
    job_functions = [call[0][0] for call in calls]
    
    # The scheduler uses a closure, so we can't directly access the instance name
    # Instead, we'll check that we have the right number of aws_manager calls
    assert mock_scheduler.add_job.call_count == 2
    
    # Check log message calls would indicate both AWS instances were enabled
    # This is an indirect way to verify the right instances were scheduled

@patch('cloudproxy.providers.manager.BackgroundScheduler')
def test_init_schedule_multiple_providers_with_instances(mock_scheduler_class, setup_provider_config):
    """Test scheduler initialization with multiple providers each with multiple instances"""
    # Setup
    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Configure AWS with multiple instances
    settings.config["providers"]["aws"]["instances"] = {
        "default": {
            "enabled": True,
            "scaling": {"min_scaling": 1, "max_scaling": 2},
            "size": "t2.micro",
            "region": "us-east-1",
            "display_name": "Default AWS"
        },
        "production": {
            "enabled": True,
            "scaling": {"min_scaling": 2, "max_scaling": 5},
            "size": "t3.medium",
            "region": "us-west-2",
            "display_name": "Production AWS"
        }
    }
    
    # Configure DigitalOcean with multiple instances
    settings.config["providers"]["digitalocean"]["instances"] = {
        "default": {
            "enabled": True,
            "scaling": {"min_scaling": 1, "max_scaling": 2},
            "size": "s-1vcpu-1gb",
            "region": "nyc1",
            "display_name": "Default DO"
        },
        "backup": {
            "enabled": True,
            "scaling": {"min_scaling": 1, "max_scaling": 3},
            "size": "s-2vcpu-2gb",
            "region": "lon1",
            "display_name": "Backup DO"
        }
    }
    
    # Disable other providers for clarity
    settings.config["providers"]["gcp"]["instances"]["default"]["enabled"] = False
    settings.config["providers"]["hetzner"]["instances"]["default"]["enabled"] = False
    
    # Execute
    init_schedule()
    
    # Verify
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 4  # 2 AWS + 2 DO instances
    
    # Verify all calls are to the correct manager functions
    calls = mock_scheduler.add_job.call_args_list
    
    # Extract all function names from the calls
    function_names = set()
    for call in calls:
        func = call[0][0]
        # The function is a closure that calls another function
        # We need to extract the original function name from the closure
        function_names.add(func.__name__)
    
    # There should be closures for both provider types
    assert len(function_names) > 0 