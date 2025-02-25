import pytest
from unittest.mock import patch, Mock
from cloudproxy.providers import settings
from cloudproxy.providers.manager import init_schedule

# Test setup and teardown
@pytest.fixture
def setup_provider_config():
    """Fixture to preserve and restore provider settings"""
    # Save original settings
    original_do_enabled = settings.config["providers"]["digitalocean"]["enabled"]
    original_aws_enabled = settings.config["providers"]["aws"]["enabled"]
    original_gcp_enabled = settings.config["providers"]["gcp"]["enabled"]
    original_hetzner_enabled = settings.config["providers"]["hetzner"]["enabled"]
    
    # Return function to restore settings
    yield
    
    # Restore original settings
    settings.config["providers"]["digitalocean"]["enabled"] = original_do_enabled
    settings.config["providers"]["aws"]["enabled"] = original_aws_enabled
    settings.config["providers"]["gcp"]["enabled"] = original_gcp_enabled
    settings.config["providers"]["hetzner"]["enabled"] = original_hetzner_enabled

# Tests for scheduler initialization
@patch('cloudproxy.providers.manager.BackgroundScheduler')
def test_init_schedule_all_enabled(mock_scheduler_class, setup_provider_config):
    """Test scheduler initialization with all providers enabled"""
    # Setup
    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Configure all providers as enabled
    settings.config["providers"]["digitalocean"]["enabled"] = True
    settings.config["providers"]["aws"]["enabled"] = True
    settings.config["providers"]["gcp"]["enabled"] = True
    settings.config["providers"]["hetzner"]["enabled"] = True
    
    # Execute
    init_schedule()
    
    # Verify
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 4  # One for each provider

@patch('cloudproxy.providers.manager.BackgroundScheduler')
def test_init_schedule_all_disabled(mock_scheduler_class, setup_provider_config):
    """Test scheduler initialization with all providers disabled"""
    # Setup
    mock_scheduler = Mock()
    mock_scheduler_class.return_value = mock_scheduler
    
    # Configure all providers as disabled
    settings.config["providers"]["digitalocean"]["enabled"] = False
    settings.config["providers"]["aws"]["enabled"] = False
    settings.config["providers"]["gcp"]["enabled"] = False
    settings.config["providers"]["hetzner"]["enabled"] = False
    
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
    settings.config["providers"]["digitalocean"]["enabled"] = True
    settings.config["providers"]["aws"]["enabled"] = False
    settings.config["providers"]["gcp"]["enabled"] = True
    settings.config["providers"]["hetzner"]["enabled"] = False
    
    # Execute
    init_schedule()
    
    # Verify
    mock_scheduler.start.assert_called_once()
    assert mock_scheduler.add_job.call_count == 2  # Two jobs should be added
    
    # Verify the correct methods were scheduled
    calls = mock_scheduler.add_job.call_args_list
    methods = [call[0][0].__name__ for call in calls]
    assert "do_manager" in methods
    assert "gcp_manager" in methods 