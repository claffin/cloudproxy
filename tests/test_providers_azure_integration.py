import asyncio
import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from cloudproxy.providers import settings
from cloudproxy.providers.manager import init_schedule
from cloudproxy.providers.azure.main import azure_start, azure_manager


@pytest.fixture
def mock_settings():
    """Mock settings for testing Azure integration"""
    original_settings = settings.config.copy()
    
    # Set up mock settings
    settings.config = {
        "providers": {
            "azure": {
                "enabled": True,
                "instances": {
                    "default": {
                        "proxy_count": 2,
                        "poll_interval": 60,
                        "subscription_id": "test-sub-id",
                        "client_id": "test-client-id",
                        "client_secret": "test-client-secret",
                        "tenant_id": "test-tenant-id",
                        "resource_group": "test-rg",
                        "location": "eastus",
                        "size": "Standard_B1s",
                        "ips": []
                    },
                    "custom": {
                        "proxy_count": 1,
                        "poll_interval": 30,
                        "subscription_id": "custom-sub-id",
                        "client_id": "custom-client-id",
                        "client_secret": "custom-client-secret",
                        "tenant_id": "custom-tenant-id",
                        "resource_group": "custom-rg",
                        "location": "westus",
                        "size": "Standard_B2s",
                        "ips": []
                    }
                }
            }
        },
        "auth": {
            "username": "test-user",
            "password": "test-pass"
        }
    }
    
    yield settings.config
    
    # Restore original settings
    settings.config = original_settings


@pytest.mark.asyncio
async def test_azure_manager_default_instance(mock_settings):
    """Test the Azure manager function with default instance"""
    # Mock the azure_start function
    with patch('cloudproxy.providers.azure.main.azure_start', autospec=True) as mock_start:
        # Set up the mock to return some test IPs
        test_ips = [
            {"ip": "1.2.3.4", "port": 8899, "username": "test-user", "password": "test-pass", "ready": True, "provider": "azure", "provider_instance": "default"},
            {"ip": "5.6.7.8", "port": 8899, "username": "test-user", "password": "test-pass", "ready": True, "provider": "azure", "provider_instance": "default"}
        ]
        mock_start.return_value = test_ips
        
        # Call the manager function
        result = await azure_manager("default")
        
        # Verify the start function was called with the right settings
        mock_start.assert_called_once_with(mock_settings["providers"]["azure"]["instances"]["default"], "default")
        
        # Verify the result is as expected
        assert result == test_ips
        
        # Verify the IPs were updated in the config
        assert mock_settings["providers"]["azure"]["instances"]["default"]["ips"] == test_ips


@pytest.mark.asyncio
async def test_azure_manager_custom_instance(mock_settings):
    """Test the Azure manager function with custom instance"""
    # Mock the azure_start function
    with patch('cloudproxy.providers.azure.main.azure_start', autospec=True) as mock_start:
        # Set up the mock to return a test IP
        test_ips = [
            {"ip": "9.10.11.12", "port": 8899, "username": "test-user", "password": "test-pass", "ready": True, "provider": "azure", "provider_instance": "custom"}
        ]
        mock_start.return_value = test_ips
        
        # Call the manager function
        result = await azure_manager("custom")
        
        # Verify the start function was called with the right settings
        mock_start.assert_called_once_with(mock_settings["providers"]["azure"]["instances"]["custom"], "custom")
        
        # Verify the result is as expected
        assert result == test_ips
        
        # Verify the IPs were updated in the config
        assert mock_settings["providers"]["azure"]["instances"]["custom"]["ips"] == test_ips


@pytest.mark.asyncio
async def test_init_schedule_includes_azure(mock_settings):
    """Test that the Azure manager function can be integrated with the scheduler."""
    # Create a mock scheduler
    mock_scheduler = MagicMock()
    
    # Enable Azure in the settings and add enabled flag to instances
    mock_settings["providers"]["azure"]["enabled"] = True
    mock_settings["providers"]["azure"]["instances"]["default"]["enabled"] = True
    mock_settings["providers"]["azure"]["instances"]["custom"]["enabled"] = True
    
    # Patch the actual settings.config rather than the import in manager.py
    with patch('cloudproxy.providers.settings.config', mock_settings):
        # Just verify that init_schedule can be called without errors
        init_schedule(mock_scheduler)
        
        # Verify the scheduler was started
        mock_scheduler.start.assert_called_once()
        
        # Just verify that add_job was called at least once
        assert mock_scheduler.add_job.call_count > 0, "No jobs were scheduled" 