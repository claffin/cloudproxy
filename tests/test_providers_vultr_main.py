import pytest
import datetime
from unittest.mock import MagicMock, patch, call
from cloudproxy.providers.vultr.main import (
    vultr_deployment,
    vultr_check_alive,
    vultr_check_delete,
    vultr_fw,
    vultr_start,
)
from cloudproxy.providers.vultr.functions import VultrInstance, VultrFirewallExistsException


class TestVultrMain:
    
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
    def mock_config(self, mock_instance_config):
        with patch('cloudproxy.providers.vultr.main.config') as mock_cfg:
            mock_cfg.__getitem__.side_effect = lambda x: {
                "providers": {
                    "vultr": {
                        "instances": {
                            "default": mock_instance_config
                        }
                    }
                },
                "age_limit": 3600  # 1 hour
            }.get(x, {})
            yield mock_cfg
    
    @pytest.fixture
    def mock_instances(self):
        """Create mock Vultr instances."""
        instances = []
        for i in range(3):
            data = {
                "id": f"instance-{i}",
                "main_ip": f"192.168.1.{i+1}",
                "label": f"cloudproxy-default-{i}",
                "date_created": "2024-01-01T00:00:00Z",
                "status": "active",
                "tags": ["cloudproxy", "cloudproxy-default"]
            }
            instances.append(VultrInstance(data))
        return instances
    
    @patch('cloudproxy.providers.vultr.main.create_proxy')
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    def test_vultr_deployment_scale_up(self, mock_list, mock_delete, mock_create, 
                                       mock_config, mock_instance_config):
        # Setup - currently have 1 instance, need 3
        mock_list.return_value = [VultrInstance({"id": "existing", "main_ip": "192.168.1.1"})]
        
        # Call function
        result = vultr_deployment(3, mock_instance_config)
        
        # Should create 2 new instances
        assert mock_create.call_count == 2
        assert mock_delete.call_count == 0
        assert result == 1  # Returns current count
    
    @patch('cloudproxy.providers.vultr.main.create_proxy')
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    def test_vultr_deployment_scale_down(self, mock_list, mock_delete, mock_create, 
                                         mock_config, mock_instance_config, mock_instances):
        # Setup - currently have 3 instances, need 1
        mock_list.return_value = mock_instances
        
        # Call function
        result = vultr_deployment(1, mock_instance_config)
        
        # Should delete 2 instances
        assert mock_create.call_count == 0
        assert mock_delete.call_count == 2
        assert result == 3  # Returns current count
    
    @patch('cloudproxy.providers.vultr.main.create_proxy')
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    def test_vultr_deployment_no_change(self, mock_list, mock_delete, mock_create, 
                                        mock_config, mock_instance_config, mock_instances):
        # Setup - currently have 3 instances, need 3
        mock_list.return_value = mock_instances[:3]
        
        # Call function
        result = vultr_deployment(3, mock_instance_config)
        
        # Should not create or delete
        assert mock_create.call_count == 0
        assert mock_delete.call_count == 0
        assert result == 3
    
    @patch('cloudproxy.providers.vultr.main.check_alive')
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    @patch('cloudproxy.providers.vultr.main.dateparser.parse')
    def test_vultr_check_alive_active_instances(self, mock_parse, mock_list, mock_delete, 
                                               mock_check_alive, mock_config, mock_instance_config):
        # Setup
        mock_instances = [
            VultrInstance({
                "id": "active-1",
                "main_ip": "192.168.1.1",
                "status": "active",
                "date_created": "2024-01-01T00:00:00Z"
            }),
            VultrInstance({
                "id": "active-2",
                "main_ip": "192.168.1.2",
                "status": "active",
                "date_created": "2024-01-01T00:00:00Z"
            })
        ]
        mock_list.return_value = mock_instances
        mock_parse.return_value = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
        mock_check_alive.side_effect = [True, True]  # Both instances are alive
        
        # Call function
        result = vultr_check_alive(mock_instance_config)
        
        # Assertions
        assert len(result) == 2
        assert "192.168.1.1" in result
        assert "192.168.1.2" in result
        assert mock_delete.call_count == 0
    
    @patch('cloudproxy.providers.vultr.main.check_alive')
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    @patch('cloudproxy.providers.vultr.main.dateparser.parse')
    def test_vultr_check_alive_age_limit(self, mock_parse, mock_list, mock_delete, 
                                        mock_check_alive, mock_config, mock_instance_config):
        # Setup - instance is older than age limit
        mock_instance = VultrInstance({
            "id": "old-instance",
            "main_ip": "192.168.1.1",
            "status": "active",
            "date_created": "2024-01-01T00:00:00Z"
        })
        mock_list.return_value = [mock_instance]
        # Instance created 2 hours ago, age limit is 1 hour
        mock_parse.return_value = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
        mock_check_alive.return_value = True
        
        # Call function
        result = vultr_check_alive(mock_instance_config)
        
        # Should delete the old instance
        mock_delete.assert_called_once_with(mock_instance, mock_instance_config)
        assert len(result) == 0
    
    @patch('cloudproxy.providers.vultr.main.check_alive')
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    @patch('cloudproxy.providers.vultr.main.dateparser.parse')
    def test_vultr_check_alive_pending_too_long(self, mock_parse, mock_list, mock_delete, 
                                               mock_check_alive, mock_config, mock_instance_config):
        # Setup - instance pending for too long
        mock_instance = VultrInstance({
            "id": "pending-instance",
            "main_ip": "192.168.1.1",
            "status": "pending",
            "date_created": "2024-01-01T00:00:00Z"
        })
        mock_list.return_value = [mock_instance]
        # Instance created 15 minutes ago (too long for pending)
        mock_parse.return_value = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=15)
        mock_check_alive.return_value = False
        
        # Call function
        result = vultr_check_alive(mock_instance_config)
        
        # Should delete the pending instance
        mock_delete.assert_called_once_with(mock_instance, mock_instance_config)
        assert len(result) == 0
    
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    @patch('cloudproxy.providers.vultr.main.delete_queue')
    @patch('cloudproxy.providers.vultr.main.restart_queue')
    def test_vultr_check_delete_with_queue(self, mock_restart_queue, mock_delete_queue, 
                                          mock_list, mock_delete, mock_config, mock_instance_config):
        # Setup
        mock_instances = [
            VultrInstance({"id": "instance-1", "main_ip": "192.168.1.1"}),
            VultrInstance({"id": "instance-2", "main_ip": "192.168.1.2"}),
            VultrInstance({"id": "instance-3", "main_ip": "192.168.1.3"})
        ]
        mock_list.return_value = mock_instances
        
        # Use sets with the required IPs
        mock_delete_queue.__class__ = set
        mock_delete_queue.__iter__ = lambda self: iter(["192.168.1.1"])
        mock_delete_queue.__contains__ = lambda self, x: x == "192.168.1.1"
        mock_delete_queue.__len__ = lambda self: 1
        mock_delete_queue.remove = MagicMock()
        
        mock_restart_queue.__class__ = set
        mock_restart_queue.__iter__ = lambda self: iter(["192.168.1.2"])
        mock_restart_queue.__contains__ = lambda self, x: x == "192.168.1.2"
        mock_restart_queue.__len__ = lambda self: 1
        mock_restart_queue.remove = MagicMock()
        
        mock_delete.return_value = True
        
        # Call function
        vultr_check_delete(mock_instance_config)
        
        # Should delete instances in queues
        assert mock_delete.call_count == 2
        mock_delete_queue.remove.assert_called_once_with("192.168.1.1")
        mock_restart_queue.remove.assert_called_once_with("192.168.1.2")
    
    @patch('cloudproxy.providers.vultr.main.delete_proxy')
    @patch('cloudproxy.providers.vultr.main.list_instances')
    def test_vultr_check_delete_no_instances(self, mock_list, mock_delete, 
                                            mock_config, mock_instance_config):
        # Setup - no instances
        mock_list.return_value = []
        
        # Call function
        vultr_check_delete(mock_instance_config)
        
        # Should not attempt any deletions
        assert mock_delete.call_count == 0
    
    @patch('cloudproxy.providers.vultr.main.create_firewall')
    def test_vultr_fw_success(self, mock_create_fw, mock_config, mock_instance_config):
        # Setup
        mock_create_fw.return_value = "firewall-id-123"
        
        # Call function
        vultr_fw(mock_instance_config)
        
        # Assertions
        mock_create_fw.assert_called_once_with(mock_instance_config)
    
    @patch('cloudproxy.providers.vultr.main.create_firewall')
    def test_vultr_fw_already_exists(self, mock_create_fw, mock_config, mock_instance_config):
        # Setup
        mock_create_fw.side_effect = VultrFirewallExistsException("Firewall exists")
        
        # Call function - should not raise
        vultr_fw(mock_instance_config)
        
        # Assertions
        mock_create_fw.assert_called_once_with(mock_instance_config)
    
    @patch('cloudproxy.providers.vultr.main.vultr_check_alive')
    @patch('cloudproxy.providers.vultr.main.vultr_deployment')
    @patch('cloudproxy.providers.vultr.main.vultr_check_delete')
    @patch('cloudproxy.providers.vultr.main.vultr_fw')
    def test_vultr_start(self, mock_fw, mock_check_delete, mock_deployment, 
                        mock_check_alive, mock_config, mock_instance_config):
        # Setup
        mock_check_alive.side_effect = [
            ["192.168.1.1"],  # First check returns 1 IP
            ["192.168.1.1", "192.168.1.2"]  # Second check returns 2 IPs
        ]
        
        # Call function
        result = vultr_start(mock_instance_config)
        
        # Assertions
        mock_fw.assert_called_once_with(mock_instance_config)
        mock_check_delete.assert_called_once_with(mock_instance_config)
        mock_deployment.assert_called_once_with(
            mock_instance_config["scaling"]["min_scaling"], 
            mock_instance_config
        )
        assert mock_check_alive.call_count == 2
        assert result == ["192.168.1.1", "192.168.1.2"]
    
    def test_vultr_start_with_default_config(self):
        """Test that vultr_start works with default config."""
        with patch('cloudproxy.providers.vultr.main.config') as mock_config:
            with patch('cloudproxy.providers.vultr.main.vultr_fw') as mock_fw:
                with patch('cloudproxy.providers.vultr.main.vultr_check_delete') as mock_check_delete:
                    with patch('cloudproxy.providers.vultr.main.vultr_check_alive') as mock_check_alive:
                        with patch('cloudproxy.providers.vultr.main.vultr_deployment') as mock_deployment:
                            
                            # Setup
                            default_config = {
                                "scaling": {"min_scaling": 2},
                                "display_name": "Default"
                            }
                            mock_config.__getitem__.side_effect = lambda x: {
                                "providers": {
                                    "vultr": {
                                        "instances": {
                                            "default": default_config
                                        }
                                    }
                                }
                            }.get(x, {})
                            mock_check_alive.return_value = []
                            
                            # Call without config argument
                            result = vultr_start()
                            
                            # Should use default config
                            mock_fw.assert_called_once()
                            mock_check_delete.assert_called_once()
                            mock_deployment.assert_called_once()
                            assert mock_check_alive.call_count == 2