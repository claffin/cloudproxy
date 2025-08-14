"""
Unit tests for rolling deployment functionality.
"""

import datetime
import pytest
from unittest.mock import MagicMock, patch
from cloudproxy.providers.rolling import (
    ProxyState,
    ProxyInfo,
    RollingDeploymentState,
    RollingDeploymentManager
)


class TestRollingDeploymentManager:
    """Test cases for the RollingDeploymentManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = RollingDeploymentManager()
        
    def test_get_state_creates_new(self):
        """Test that get_state creates a new state if it doesn't exist."""
        state = self.manager.get_state("aws", "default")
        assert state.provider == "aws"
        assert state.instance == "default"
        assert len(state.healthy_proxies) == 0
        assert len(state.pending_recycle) == 0
        
    def test_get_state_returns_existing(self):
        """Test that get_state returns existing state."""
        # Create initial state
        state1 = self.manager.get_state("aws", "default")
        state1.healthy_proxies.add("192.168.1.1")
        
        # Get state again
        state2 = self.manager.get_state("aws", "default")
        assert "192.168.1.1" in state2.healthy_proxies
        assert state1 is state2
        
    def test_can_recycle_proxy_rolling_disabled(self):
        """Test that recycling is always allowed when rolling is disabled."""
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip="192.168.1.1",
            total_healthy=5,
            min_available=3,
            batch_size=2,
            rolling_enabled=False
        )
        assert result is True
        
    def test_can_recycle_proxy_batch_size_limit(self):
        """Test that batch size limits recycling."""
        state = self.manager.get_state("aws", "default")
        state.recycling.add("192.168.1.1")
        state.recycling.add("192.168.1.2")
        
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip="192.168.1.3",
            total_healthy=10,
            min_available=3,
            batch_size=2,
            rolling_enabled=True
        )
        assert result is False
        
    def test_can_recycle_proxy_min_available_limit(self):
        """Test that minimum availability prevents recycling."""
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip="192.168.1.1",
            total_healthy=3,
            min_available=3,
            batch_size=2,
            rolling_enabled=True
        )
        assert result is False
        
    def test_can_recycle_proxy_allowed(self):
        """Test successful recycling when all conditions are met."""
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip="192.168.1.1",
            total_healthy=10,
            min_available=3,
            batch_size=2,
            rolling_enabled=True
        )
        assert result is True
        
        # Check that proxy was marked as pending recycle
        state = self.manager.get_state("aws", "default")
        assert "192.168.1.1" in state.pending_recycle
    
    def test_can_recycle_proxy_min_available_exceeds_min_scaling(self):
        """Test that the system adjusts when min_available >= min_scaling."""
        # Test when min_available equals min_scaling
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip="192.168.1.1",
            total_healthy=5,
            min_available=5,  # Same as min_scaling
            batch_size=2,
            rolling_enabled=True,
            min_scaling=5
        )
        # Should still allow recycling with adjusted minimum (min_scaling - 1 = 4)
        assert result is True
        
        # Reset state for second test
        self.manager = RollingDeploymentManager()
        
        # Test when min_available exceeds min_scaling
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip="192.168.1.2",
            total_healthy=5,
            min_available=10,  # Greater than min_scaling
            batch_size=2,
            rolling_enabled=True,
            min_scaling=5
        )
        # Should still allow recycling with adjusted minimum (min_scaling - 1 = 4)
        assert result is True
        
    def test_can_recycle_proxy_min_scaling_one(self):
        """Test edge case when min_scaling is 1."""
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip="192.168.1.1",
            total_healthy=1,
            min_available=1,
            batch_size=1,
            rolling_enabled=True,
            min_scaling=1
        )
        # Should not allow recycling when only one proxy exists
        assert result is False
        
    def test_mark_proxy_recycling(self):
        """Test marking a proxy as actively recycling."""
        state = self.manager.get_state("aws", "default")
        state.pending_recycle.add("192.168.1.1")
        
        self.manager.mark_proxy_recycling("aws", "default", "192.168.1.1")
        
        assert "192.168.1.1" not in state.pending_recycle
        assert "192.168.1.1" in state.recycling
        
    def test_mark_proxy_recycled(self):
        """Test marking a proxy as successfully recycled."""
        state = self.manager.get_state("aws", "default")
        state.recycling.add("192.168.1.1")
        state.healthy_proxies.add("192.168.1.1")
        
        self.manager.mark_proxy_recycled("aws", "default", "192.168.1.1")
        
        assert "192.168.1.1" not in state.recycling
        assert "192.168.1.1" not in state.healthy_proxies
        assert "192.168.1.1" not in state.pending_recycle
        
    def test_update_proxy_health(self):
        """Test updating proxy health status."""
        healthy_ips = ["192.168.1.1", "192.168.1.2"]
        pending_ips = ["192.168.1.3"]
        
        self.manager.update_proxy_health("aws", "default", healthy_ips, pending_ips)
        
        state = self.manager.get_state("aws", "default")
        assert state.healthy_proxies == {"192.168.1.1", "192.168.1.2"}
        assert state.pending == {"192.168.1.3"}
        
    def test_update_proxy_health_cleans_stale_recycling(self):
        """Test that update cleans up stale recycling entries."""
        state = self.manager.get_state("aws", "default")
        state.recycling.add("192.168.1.1")  # No longer exists
        state.recycling.add("192.168.1.2")  # Still exists
        state.pending_recycle.add("192.168.1.3")  # No longer exists
        
        healthy_ips = ["192.168.1.2"]
        self.manager.update_proxy_health("aws", "default", healthy_ips, [])
        
        assert "192.168.1.1" not in state.recycling
        assert "192.168.1.2" in state.recycling
        assert "192.168.1.3" not in state.pending_recycle
        
    def test_get_recycling_status(self):
        """Test getting recycling status."""
        # Set up some state
        state = self.manager.get_state("aws", "default")
        state.healthy_proxies = {"192.168.1.1", "192.168.1.2"}
        state.pending_recycle = {"192.168.1.3"}
        state.recycling = {"192.168.1.4"}
        state.pending = {"192.168.1.5"}
        
        status = self.manager.get_recycling_status()
        
        assert "aws/default" in status
        assert status["aws/default"]["healthy"] == 2
        assert status["aws/default"]["pending"] == 1
        assert status["aws/default"]["pending_recycle"] == 1
        assert status["aws/default"]["recycling"] == 1
        assert "192.168.1.1" in status["aws/default"]["healthy_ips"]
        
    def test_get_recycling_status_filtered(self):
        """Test getting filtered recycling status."""
        # Set up states for multiple providers
        self.manager.get_state("aws", "default").healthy_proxies = {"192.168.1.1"}
        self.manager.get_state("gcp", "default").healthy_proxies = {"192.168.2.1"}
        
        # Filter by provider
        status = self.manager.get_recycling_status(provider="aws")
        assert "aws/default" in status
        assert "gcp/default" not in status
        
        # Filter by provider and instance
        status = self.manager.get_recycling_status(provider="aws", instance="default")
        assert "aws/default" in status
        assert len(status) == 1
        
    def test_should_create_replacement(self):
        """Test determining if replacement proxies should be created."""
        state = self.manager.get_state("aws", "default")
        state.healthy_proxies = {"192.168.1.1", "192.168.1.2"}
        state.pending = {"192.168.1.3"}
        
        # Total is 3, min_scaling is 5, should create replacements
        should_create = self.manager.should_create_replacement("aws", "default", 5)
        assert should_create is True
        
        # Total is 3, min_scaling is 3, should not create replacements
        should_create = self.manager.should_create_replacement("aws", "default", 3)
        assert should_create is False
        
    def test_complex_rolling_scenario(self):
        """Test a complex rolling deployment scenario."""
        # Initial state: 5 healthy proxies
        healthy_ips = [f"192.168.1.{i}" for i in range(1, 6)]
        self.manager.update_proxy_health("aws", "default", healthy_ips, [])
        
        # Try to recycle 3 proxies with batch_size=2, min_available=3
        results = []
        for ip in healthy_ips[:3]:
            result = self.manager.can_recycle_proxy(
                provider="aws",
                instance="default",
                proxy_ip=ip,
                total_healthy=5,
                min_available=3,
                batch_size=2,
                rolling_enabled=True
            )
            results.append(result)
            if result:
                self.manager.mark_proxy_recycling("aws", "default", ip)
        
        # First two should succeed, third should fail (batch size limit)
        assert results == [True, True, False]
        
        # Mark first one as recycled
        self.manager.mark_proxy_recycled("aws", "default", healthy_ips[0])
        
        # The second proxy (192.168.1.2) is still in recycling state
        # So we have: 3 healthy (3,4,5), 1 recycling (2), 1 recycled (1)
        # We can't recycle another one yet because it would drop below min_available
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip=healthy_ips[3],
            total_healthy=4,  # Proxies 2,3,4,5 are still counted as healthy
            min_available=3,
            batch_size=2,
            rolling_enabled=True
        )
        # This should fail because we still have one recycling
        assert result is False
        
        # Now mark the second one as recycled too
        self.manager.mark_proxy_recycled("aws", "default", healthy_ips[1])
        
        # Now we can recycle another one
        result = self.manager.can_recycle_proxy(
            provider="aws",
            instance="default",
            proxy_ip=healthy_ips[3],
            total_healthy=3,  # Only 3,4,5 remain healthy
            min_available=3,
            batch_size=2,
            rolling_enabled=True
        )
        # This should fail because we're at minimum
        assert result is False


class TestProxyState:
    """Test cases for ProxyState enum."""
    
    def test_proxy_states(self):
        """Test that all expected proxy states exist."""
        assert ProxyState.HEALTHY.value == "healthy"
        assert ProxyState.PENDING_RECYCLE.value == "pending_recycle"
        assert ProxyState.RECYCLING.value == "recycling"
        assert ProxyState.PENDING.value == "pending"


class TestProxyInfo:
    """Test cases for ProxyInfo dataclass."""
    
    def test_proxy_info_creation(self):
        """Test creating a ProxyInfo instance."""
        now = datetime.datetime.now(datetime.timezone.utc)
        info = ProxyInfo(
            ip="192.168.1.1",
            state=ProxyState.HEALTHY,
            created_at=now,
            provider="aws",
            instance="default",
            age_seconds=3600
        )
        
        assert info.ip == "192.168.1.1"
        assert info.state == ProxyState.HEALTHY
        assert info.created_at == now
        assert info.provider == "aws"
        assert info.instance == "default"
        assert info.age_seconds == 3600


class TestRollingDeploymentState:
    """Test cases for RollingDeploymentState dataclass."""
    
    def test_rolling_deployment_state_creation(self):
        """Test creating a RollingDeploymentState instance."""
        state = RollingDeploymentState(
            provider="aws",
            instance="default"
        )
        
        assert state.provider == "aws"
        assert state.instance == "default"
        assert len(state.healthy_proxies) == 0
        assert len(state.pending_recycle) == 0
        assert len(state.recycling) == 0
        assert len(state.pending) == 0
        assert state.last_update is not None