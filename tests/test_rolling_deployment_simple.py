"""Simple unit tests for rolling deployment feature."""

import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta, timezone

from cloudproxy.providers.rolling import rolling_manager
from cloudproxy.providers.settings import config


class TestRollingDeploymentSimple:
    """Simple tests for rolling deployment functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test."""
        # Save original config
        self.original_rolling = config["rolling_deployment"]["enabled"]
        self.original_min_available = config["rolling_deployment"]["min_available"]
        self.original_batch_size = config["rolling_deployment"]["batch_size"]
        
        # Reset rolling manager state
        rolling_manager.states.clear()
        
        yield
        
        # Restore original config
        config["rolling_deployment"]["enabled"] = self.original_rolling
        config["rolling_deployment"]["min_available"] = self.original_min_available
        config["rolling_deployment"]["batch_size"] = self.original_batch_size
        rolling_manager.states.clear()
    
    def test_can_recycle_with_sufficient_proxies(self):
        """Test that recycling is allowed when we have sufficient proxies."""
        # Setup
        config["rolling_deployment"]["enabled"] = True
        
        # Update health status first
        rolling_manager.update_proxy_health(
            "test", "default",
            healthy_ips=["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4"],
            pending_ips=[]
        )
        
        # Test recycling with sufficient proxies
        can_recycle = rolling_manager.can_recycle_proxy(
            provider="test",
            instance="default",
            proxy_ip="1.1.1.1",
            total_healthy=4,
            min_available=2,
            batch_size=2,
            rolling_enabled=True
        )
        
        assert can_recycle is True
    
    def test_cannot_recycle_below_minimum(self):
        """Test that recycling is blocked when it would go below minimum."""
        # Setup
        config["rolling_deployment"]["enabled"] = True
        
        # Update health status first
        rolling_manager.update_proxy_health(
            "test", "default",
            healthy_ips=["1.1.1.1", "2.2.2.2"],
            pending_ips=[]
        )
        
        # Test recycling that would go below minimum
        can_recycle = rolling_manager.can_recycle_proxy(
            provider="test",
            instance="default",
            proxy_ip="1.1.1.1",
            total_healthy=2,
            min_available=2,
            batch_size=1,
            rolling_enabled=True
        )
        
        assert can_recycle is False
    
    def test_batch_size_limit(self):
        """Test that batch size limits concurrent recycling."""
        # Setup
        config["rolling_deployment"]["enabled"] = True
        
        # Update health status first
        rolling_manager.update_proxy_health(
            "test", "default",
            healthy_ips=["1.1.1.1", "2.2.2.2", "3.3.3.3", "4.4.4.4", "5.5.5.5"],
            pending_ips=[]
        )
        
        # Try to recycle multiple proxies with batch_size=2
        recycled = []
        for ip in ["1.1.1.1", "2.2.2.2", "3.3.3.3"]:
            if rolling_manager.can_recycle_proxy(
                provider="test",
                instance="default",
                proxy_ip=ip,
                total_healthy=5,
                min_available=2,
                batch_size=2,
                rolling_enabled=True
            ):
                recycled.append(ip)
        
        # Should only allow 2 due to batch size
        assert len(recycled) == 2
    
    def test_disabled_rolling_allows_all_deletions(self):
        """Test that disabling rolling deployment allows unrestricted deletions."""
        # Setup
        config["rolling_deployment"]["enabled"] = False
        
        # Test recycling with rolling disabled
        can_recycle = rolling_manager.can_recycle_proxy(
            provider="test",
            instance="default",
            proxy_ip="1.1.1.1",
            total_healthy=1,
            min_available=5,  # Much higher than healthy
            batch_size=1,
            rolling_enabled=False
        )
        
        assert can_recycle is True
    
    def test_state_tracking(self):
        """Test that proxy states are tracked correctly."""
        # Update proxy health
        rolling_manager.update_proxy_health(
            "test", "default",
            healthy_ips=["1.1.1.1", "2.2.2.2"],
            pending_ips=["3.3.3.3"]
        )
        
        # Check state
        state = rolling_manager.get_state("test", "default")
        assert len(state.healthy_proxies) == 2
        assert len(state.pending) == 1
        assert "1.1.1.1" in state.healthy_proxies
        assert "3.3.3.3" in state.pending
        
        # Mark as recycling
        rolling_manager.mark_proxy_recycling("test", "default", "1.1.1.1")
        state = rolling_manager.get_state("test", "default")
        assert len(state.recycling) == 1
        assert "1.1.1.1" in state.recycling
        
        # Mark as recycled
        rolling_manager.mark_proxy_recycled("test", "default", "1.1.1.1")
        state = rolling_manager.get_state("test", "default")
        assert len(state.recycling) == 0
        assert "1.1.1.1" not in state.recycling
    
    def test_min_scaling_adjustment(self):
        """Test that min_scaling adjusts the effective minimum when appropriate."""
        # Setup
        config["rolling_deployment"]["enabled"] = True
        
        # Update health status first
        rolling_manager.update_proxy_health(
            "test", "default",
            healthy_ips=["1.1.1.1", "2.2.2.2", "3.3.3.3"],
            pending_ips=[]
        )
        
        # Test with min_scaling that adjusts effective minimum
        can_recycle = rolling_manager.can_recycle_proxy(
            provider="test",
            instance="default",
            proxy_ip="1.1.1.1",
            total_healthy=3,
            min_available=3,  # Would normally block all recycling
            batch_size=1,
            rolling_enabled=True,
            min_scaling=3  # But min_scaling adjusts it to max(1, 3-1) = 2
        )
        
        # Should allow recycling because effective_min_available = 2
        assert can_recycle is True
    
    def test_recycling_status_report(self):
        """Test getting the recycling status report."""
        # Setup some state
        rolling_manager.update_proxy_health(
            "aws", "default",
            healthy_ips=["1.1.1.1", "2.2.2.2"],
            pending_ips=["3.3.3.3"]
        )
        
        rolling_manager.update_proxy_health(
            "gcp", "production",
            healthy_ips=["4.4.4.4"],
            pending_ips=[]
        )
        
        # Get status
        status = rolling_manager.get_recycling_status()
        
        assert "aws/default" in status
        assert status["aws/default"]["healthy"] == 2
        assert status["aws/default"]["pending"] == 1
        
        assert "gcp/production" in status
        assert status["gcp/production"]["healthy"] == 1
        assert status["gcp/production"]["pending"] == 0
    
    def test_should_create_replacement(self):
        """Test determining if replacement proxies should be created."""
        # Setup state with proxies being recycled
        rolling_manager.update_proxy_health(
            "test", "default",
            healthy_ips=["1.1.1.1"],
            pending_ips=[]
        )
        
        # Test with min_scaling higher than current count
        should_create = rolling_manager.should_create_replacement(
            provider="test",
            instance="default",
            min_scaling=3
        )
        
        assert should_create is True
        
        # Test with min_scaling met
        should_create = rolling_manager.should_create_replacement(
            provider="test",
            instance="default",
            min_scaling=1
        )
        
        assert should_create is False