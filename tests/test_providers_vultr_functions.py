import pytest
import requests
from unittest.mock import MagicMock, patch, call
from cloudproxy.providers.vultr.functions import (
    create_proxy,
    delete_proxy,
    list_instances,
    create_firewall,
    VultrFirewallExistsException,
    VultrInstance,
    get_api_headers,
)


class TestVultrFunctions:
    
    @pytest.fixture
    def mock_instance_config(self):
        return {
            "enabled": True,
            "ips": [],
            "scaling": {"min_scaling": 2, "max_scaling": 5},
            "plan": "vc2-1c-1gb",
            "region": "ewr",
            "os_id": 387,
            "display_name": "Vultr Test",
            "secrets": {"api_token": "test-api-token"},
        }
    
    @pytest.fixture
    def mock_settings_config(self, mock_instance_config):
        with patch('cloudproxy.providers.vultr.functions.settings') as mock_settings:
            mock_settings.config = {
                "auth": {"username": "testuser", "password": "testpass"},
                "providers": {
                    "vultr": {
                        "instances": {
                            "default": mock_instance_config,
                            "test_instance": mock_instance_config
                        }
                    }
                }
            }
            yield mock_settings
    
    def test_get_api_headers(self, mock_instance_config):
        headers = get_api_headers(mock_instance_config)
        assert headers["Authorization"] == "Bearer test-api-token"
        assert headers["Content-Type"] == "application/json"
    
    def test_vultr_instance_class(self):
        data = {
            "id": "test-id",
            "main_ip": "192.168.1.1",
            "label": "test-label",
            "date_created": "2024-01-01T00:00:00Z",
            "status": "active",
            "region": "ewr",
            "plan": "vc2-1c-1gb",
            "tags": ["test", "cloudproxy"]
        }
        
        instance = VultrInstance(data)
        assert instance.id == "test-id"
        assert instance.main_ip == "192.168.1.1"
        assert instance.ip_address == "192.168.1.1"
        assert instance.label == "test-label"
        assert instance.status == "active"
        assert instance.tags == ["test", "cloudproxy"]
    
    @patch('cloudproxy.providers.vultr.functions.requests.post')
    @patch('cloudproxy.providers.vultr.functions.set_auth')
    def test_create_proxy_success(self, mock_set_auth, mock_post, mock_settings_config, mock_instance_config):
        # Setup mocks
        mock_set_auth.return_value = "user_data_script"
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "instance": {
                "id": "new-instance-id"
            }
        }
        mock_post.return_value = mock_response
        
        # Call function
        result = create_proxy(mock_instance_config)
        
        # Assertions
        assert result is True
        mock_set_auth.assert_called_once_with("testuser", "testpass")
        mock_post.assert_called_once()
        
        # Check the payload sent to API
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.vultr.com/v2/instances"
        payload = call_args[1]["json"]
        assert payload["region"] == "ewr"
        assert payload["plan"] == "vc2-1c-1gb"
        assert payload["os_id"] == 387
        assert "cloudproxy" in payload["tags"]
    
    @patch('cloudproxy.providers.vultr.functions.requests.post')
    @patch('cloudproxy.providers.vultr.functions.set_auth')
    def test_create_proxy_failure(self, mock_set_auth, mock_post, mock_settings_config, mock_instance_config):
        # Setup mocks
        mock_set_auth.return_value = "user_data_script"
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        # Call function
        result = create_proxy(mock_instance_config)
        
        # Assertions
        assert result is False
    
    @patch('cloudproxy.providers.vultr.functions.requests.delete')
    def test_delete_proxy_success(self, mock_delete, mock_instance_config):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        # Test with instance ID string
        result = delete_proxy("test-instance-id", mock_instance_config)
        assert result is True
        mock_delete.assert_called_with(
            "https://api.vultr.com/v2/instances/test-instance-id",
            headers=get_api_headers(mock_instance_config)
        )
    
    @patch('cloudproxy.providers.vultr.functions.requests.delete')
    def test_delete_proxy_with_instance_object(self, mock_delete, mock_instance_config):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        # Test with VultrInstance object
        instance = VultrInstance({"id": "test-instance-id", "main_ip": "192.168.1.1"})
        result = delete_proxy(instance, mock_instance_config)
        assert result is True
    
    @patch('cloudproxy.providers.vultr.functions.requests.delete')
    def test_delete_proxy_not_found(self, mock_delete, mock_instance_config):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response
        
        # Call function
        result = delete_proxy("non-existent-id", mock_instance_config)
        
        # Should return True even if not found
        assert result is True
    
    @patch('cloudproxy.providers.vultr.functions.requests.get')
    def test_list_instances_success(self, mock_get, mock_settings_config, mock_instance_config):
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "instances": [
                {
                    "id": "instance-1",
                    "main_ip": "192.168.1.1",
                    "tags": ["cloudproxy", "cloudproxy-default"]
                },
                {
                    "id": "instance-2",
                    "main_ip": "192.168.1.2",
                    "tags": ["cloudproxy", "cloudproxy-default"]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Call function
        instances = list_instances(mock_instance_config)
        
        # Assertions
        assert len(instances) == 2
        assert all(isinstance(inst, VultrInstance) for inst in instances)
        assert instances[0].id == "instance-1"
        assert instances[1].id == "instance-2"
    
    @patch('cloudproxy.providers.vultr.functions.requests.get')
    def test_list_instances_with_old_tags(self, mock_get, mock_settings_config, mock_instance_config):
        # Setup mocks for default instance checking old tags
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "instances": [
                {
                    "id": "instance-1",
                    "main_ip": "192.168.1.1",
                    "tags": ["cloudproxy", "cloudproxy-default"]
                }
            ]
        }
        
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "instances": [
                {
                    "id": "instance-1",
                    "main_ip": "192.168.1.1",
                    "tags": ["cloudproxy", "cloudproxy-default"]
                },
                {
                    "id": "instance-2",
                    "main_ip": "192.168.1.2",
                    "tags": ["cloudproxy"]  # Old tag format
                }
            ]
        }
        
        mock_get.side_effect = [mock_response1, mock_response2]
        
        # Call function
        instances = list_instances(mock_instance_config)
        
        # Should include the old-tagged instance
        assert len(instances) == 2
    
    @patch('cloudproxy.providers.vultr.functions.requests.get')
    def test_list_instances_failure(self, mock_get, mock_settings_config, mock_instance_config):
        # Setup mocks
        mock_get.side_effect = requests.exceptions.RequestException("API Error")
        
        # Call function
        instances = list_instances(mock_instance_config)
        
        # Should return empty list on error
        assert instances == []
    
    @patch('cloudproxy.providers.vultr.functions._create_firewall_rules')
    @patch('cloudproxy.providers.vultr.functions.requests.post')
    @patch('cloudproxy.providers.vultr.functions.requests.get')
    def test_create_firewall_success(self, mock_get, mock_post, mock_create_rules, 
                                    mock_settings_config, mock_instance_config):
        # Setup mocks - no existing firewall
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {"firewall_groups": []}
        mock_get.return_value = mock_get_response
        
        # Setup create firewall response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = {
            "firewall_group": {
                "id": "new-firewall-id"
            }
        }
        mock_post.return_value = mock_post_response
        
        # Call function
        firewall_id = create_firewall(mock_instance_config)
        
        # Assertions
        assert firewall_id == "new-firewall-id"
        assert mock_instance_config["firewall_group_id"] == "new-firewall-id"
        mock_create_rules.assert_called_once_with("new-firewall-id", mock_instance_config)
    
    @patch('cloudproxy.providers.vultr.functions.requests.get')
    def test_create_firewall_already_exists(self, mock_get, mock_settings_config, mock_instance_config):
        # Setup mocks - firewall already exists
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "firewall_groups": [
                {
                    "id": "existing-firewall-id",
                    "description": "cloudproxy-default"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Call function and expect exception
        with pytest.raises(VultrFirewallExistsException):
            create_firewall(mock_instance_config)
        
        # Should still store the firewall ID
        assert mock_instance_config["firewall_group_id"] == "existing-firewall-id"
    
    @patch('cloudproxy.providers.vultr.functions.requests.post')
    def test_create_firewall_rules(self, mock_post, mock_instance_config):
        from cloudproxy.providers.vultr.functions import _create_firewall_rules
        
        # Setup mocks
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response
        
        # Call function
        _create_firewall_rules("test-firewall-id", mock_instance_config)
        
        # Should have made 3 calls for 3 rules
        assert mock_post.call_count == 3
        
        # Check that proper rules were created
        calls = mock_post.call_args_list
        
        # First rule - inbound port 8899
        assert calls[0][0][0] == "https://api.vultr.com/v2/firewalls/test-firewall-id/rules"
        assert calls[0][1]["json"]["port"] == "8899"
        assert calls[0][1]["json"]["protocol"] == "tcp"
        
        # Second rule - outbound TCP
        assert calls[1][1]["json"]["port"] == "1:65535"
        assert calls[1][1]["json"]["protocol"] == "tcp"
        
        # Third rule - outbound UDP
        assert calls[2][1]["json"]["port"] == "1:65535"
        assert calls[2][1]["json"]["protocol"] == "udp"