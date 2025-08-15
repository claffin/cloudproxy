"""
Rolling deployment manager for CloudProxy.

This module handles the logic for rolling deployments, ensuring that a minimum
number of healthy proxies are always available during recycling operations.
"""

import datetime
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class ProxyState(Enum):
    """Represents the state of a proxy in the rolling deployment process."""
    HEALTHY = "healthy"
    PENDING_RECYCLE = "pending_recycle"
    RECYCLING = "recycling"
    PENDING = "pending"  # Newly created, not yet healthy


@dataclass
class ProxyInfo:
    """Information about a proxy for rolling deployment management."""
    ip: str
    state: ProxyState
    created_at: datetime.datetime
    provider: str
    instance: str
    age_seconds: Optional[int] = None


@dataclass
class RollingDeploymentState:
    """Tracks the state of rolling deployment for a provider instance."""
    provider: str
    instance: str
    healthy_proxies: Set[str] = field(default_factory=set)
    pending_recycle: Set[str] = field(default_factory=set)
    recycling: Set[str] = field(default_factory=set)
    pending: Set[str] = field(default_factory=set)
    last_update: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


class RollingDeploymentManager:
    """Manages rolling deployments across all providers."""
    
    def __init__(self):
        self.states: Dict[Tuple[str, str], RollingDeploymentState] = {}
        
    def get_state(self, provider: str, instance: str) -> RollingDeploymentState:
        """Get or create state for a provider instance."""
        key = (provider, instance)
        if key not in self.states:
            self.states[key] = RollingDeploymentState(provider=provider, instance=instance)
        return self.states[key]
    
    def can_recycle_proxy(
        self,
        provider: str,
        instance: str,
        proxy_ip: str,
        total_healthy: int,
        min_available: int,
        batch_size: int,
        rolling_enabled: bool,
        min_scaling: int = None
    ) -> bool:
        """
        Determine if a proxy can be recycled based on rolling deployment rules.
        
        Args:
            provider: The cloud provider name
            instance: The provider instance name
            proxy_ip: IP address of the proxy to recycle
            total_healthy: Total number of currently healthy proxies
            min_available: Minimum number of proxies that must remain available
            batch_size: Maximum number of proxies that can be recycled simultaneously
            rolling_enabled: Whether rolling deployment is enabled
            min_scaling: The minimum scaling configuration for the provider instance
            
        Returns:
            True if the proxy can be recycled, False otherwise
        """
        if not rolling_enabled:
            # If rolling deployment is disabled, always allow recycling
            return True
            
        state = self.get_state(provider, instance)
        
        # Validate configuration: min_available should not exceed min_scaling
        if min_scaling is not None and min_available >= min_scaling:
            logger.warning(
                f"Rolling deployment: Configuration issue for {provider}/{instance}. "
                f"min_available ({min_available}) >= min_scaling ({min_scaling}). "
                f"This would prevent all recycling. Using min_scaling - 1 as effective minimum."
            )
            # Use a sensible default: ensure at least one proxy can be recycled
            effective_min_available = max(1, min_scaling - 1)
        else:
            effective_min_available = min_available
        
        # Check if we're already recycling too many proxies
        currently_recycling = len(state.recycling) + len(state.pending_recycle)
        if currently_recycling >= batch_size:
            logger.info(
                f"Rolling deployment: Cannot recycle {proxy_ip} for {provider}/{instance}. "
                f"Already recycling {currently_recycling}/{batch_size} proxies"
            )
            return False
        
        # Check if recycling this proxy would violate minimum availability
        available_after_recycle = total_healthy - currently_recycling - 1
        if available_after_recycle < effective_min_available:
            logger.info(
                f"Rolling deployment: Cannot recycle {proxy_ip} for {provider}/{instance}. "
                f"Would reduce available proxies below minimum ({available_after_recycle} < {effective_min_available})"
            )
            return False
            
        # Mark proxy as pending recycle
        state.pending_recycle.add(proxy_ip)
        state.healthy_proxies.discard(proxy_ip)
        logger.info(
            f"Rolling deployment: Marked {proxy_ip} for recycling in {provider}/{instance}. "
            f"Currently recycling {currently_recycling + 1}/{batch_size} proxies"
        )
        return True
    
    def mark_proxy_recycling(self, provider: str, instance: str, proxy_ip: str):
        """Mark a proxy as actively being recycled."""
        state = self.get_state(provider, instance)
        state.pending_recycle.discard(proxy_ip)
        state.recycling.add(proxy_ip)
        state.last_update = datetime.datetime.now(datetime.timezone.utc)
        
    def mark_proxy_recycled(self, provider: str, instance: str, proxy_ip: str):
        """Mark a proxy as successfully recycled (deleted)."""
        state = self.get_state(provider, instance)
        state.pending_recycle.discard(proxy_ip)
        state.recycling.discard(proxy_ip)
        state.healthy_proxies.discard(proxy_ip)
        state.pending.discard(proxy_ip)
        state.last_update = datetime.datetime.now(datetime.timezone.utc)
        logger.info(f"Rolling deployment: Completed recycling {proxy_ip} in {provider}/{instance}")
    
    def update_proxy_health(
        self,
        provider: str,
        instance: str,
        healthy_ips: List[str],
        pending_ips: List[str] = None
    ):
        """
        Update the health status of proxies for a provider instance.
        
        Args:
            provider: The cloud provider name
            instance: The provider instance name
            healthy_ips: List of IPs that are currently healthy
            pending_ips: List of IPs that are pending (newly created)
        """
        state = self.get_state(provider, instance)
        
        # Update healthy proxies
        state.healthy_proxies = set(healthy_ips)
        
        # Update pending proxies if provided
        if pending_ips is not None:
            state.pending = set(pending_ips)
            
        # Clean up recycling list if proxies no longer exist
        existing_ips = state.healthy_proxies | state.pending
        state.recycling = state.recycling & existing_ips
        state.pending_recycle = state.pending_recycle & existing_ips
        
        state.last_update = datetime.datetime.now(datetime.timezone.utc)
        
    def get_recycling_status(self, provider: str = None, instance: str = None) -> Dict:
        """
        Get the current rolling deployment status.
        
        Args:
            provider: Optional provider filter
            instance: Optional instance filter
            
        Returns:
            Dictionary containing rolling deployment status
        """
        status = {}
        
        for (prov, inst), state in self.states.items():
            if provider and prov != provider:
                continue
            if instance and inst != instance:
                continue
                
            key = f"{prov}/{inst}"
            status[key] = {
                "healthy": len(state.healthy_proxies),
                "pending": len(state.pending),
                "pending_recycle": len(state.pending_recycle),
                "recycling": len(state.recycling),
                "last_update": state.last_update.isoformat(),
                "healthy_ips": list(state.healthy_proxies),
                "pending_recycle_ips": list(state.pending_recycle),
                "recycling_ips": list(state.recycling),
            }
            
        return status
    
    def should_create_replacement(
        self,
        provider: str,
        instance: str,
        min_scaling: int
    ) -> bool:
        """
        Determine if we should create replacement proxies proactively.
        
        Args:
            provider: The cloud provider name
            instance: The provider instance name
            min_scaling: Minimum number of proxies to maintain
            
        Returns:
            True if replacements should be created
        """
        state = self.get_state(provider, instance)
        
        # Total expected proxies after recycling completes
        total_after_recycle = len(state.healthy_proxies) + len(state.pending)
        
        # We should create replacements if we'll be below min_scaling
        return total_after_recycle < min_scaling


# Global instance
rolling_manager = RollingDeploymentManager()