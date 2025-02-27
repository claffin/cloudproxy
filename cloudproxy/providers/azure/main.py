import asyncio
import datetime
import os
import random
import time
from typing import Dict, List

from loguru import logger

from cloudproxy.providers.azure import functions
from cloudproxy.providers import settings
from cloudproxy.providers.models import IpInfo
from cloudproxy.providers.settings import delete_queue, restart_queue


class AzureProvider:
    """Azure provider implementation for CloudProxy."""

    def __init__(self, config, instance_id=None):
        """
        Initialize Azure provider with configuration.

        Args:
            config: Provider configuration
            instance_id: Identifier for this instance (default: None for default instance)
        """
        self.config = config
        self.instance_id = instance_id or "default"
        self.instance_config = config["instances"][self.instance_id]
        # Get max_proxies from scaling configuration instead of proxy_count
        if "scaling" in self.instance_config and "max_scaling" in self.instance_config["scaling"]:
            self.max_proxies = self.instance_config["scaling"]["max_scaling"]
        else:
            self.max_proxies = self.instance_config.get("proxy_count", 1)
        self.base_poll_interval = self.instance_config.get("poll_interval", 60)
        self.poll_jitter = self.instance_config.get("poll_jitter", 15)
        self.startup_grace_period = self.instance_config.get("startup_grace_period", 300)
        self.proxies = []
        self.maintenance_lock = asyncio.Lock()
        self.last_maintenance = datetime.datetime.min
        self.ip_info = IpInfo()

    def get_random_poll_interval(self) -> int:
        """
        Calculate a randomized poll interval to avoid synchronized polling.

        Returns:
            int: Seconds to wait before next poll
        """
        return self.base_poll_interval + random.randint(-self.poll_jitter, self.poll_jitter)

    async def initialize(self):
        """Initialize the provider by refreshing the list of proxies."""
        logger.info(f"Initializing Azure provider (instance: {self.instance_id})")
        try:
            await self.maintenance()
        except Exception as e:
            logger.error(f"Error initializing Azure provider: {e}")
            raise

    async def check_delete(self):
        """
        Check if any Azure VMs need to be deleted based on the delete queue.
        """
        # Log current delete queue state
        if delete_queue:
            logger.info(f"Current delete queue contains {len(delete_queue)} IP addresses: {', '.join(delete_queue)}")
        
        # Ensure resource group exists before proceeding
        try:
            functions.ensure_resource_group_exists(self.instance_config)
        except Exception as e:
            logger.error(f"Error ensuring Azure resource group exists: {e}")
            return
            
        # Refresh the proxies list
        try:
            self.proxies = functions.list_proxies(self.instance_config)
        except Exception as e:
            logger.error(f"Error listing Azure proxies during check_delete: {e}")
            return
            
        if not self.proxies:
            logger.info(f"No Azure proxies found to process for deletion (instance: {self.instance_id})")
            return
            
        logger.info(f"Checking {len(self.proxies)} Azure proxies for deletion (instance: {self.instance_id})")
        
        # Process each proxy
        for proxy in self.proxies:
            try:
                # Skip proxies without an IP address
                if not hasattr(proxy, 'ip_address') or not proxy.ip_address:
                    continue
                    
                proxy_ip = proxy.ip_address
                
                # Check if this proxy's IP is in the delete or restart queue
                if proxy_ip in delete_queue or proxy_ip in restart_queue:
                    logger.info(f"Found proxy {proxy.name} with IP {proxy_ip} in deletion queue - deleting now")
                    
                    # Attempt to delete the proxy
                    delete_result = await self.destroy_proxy(proxy)
                    
                    if delete_result:
                        logger.info(f"Successfully destroyed Azure proxy -> {proxy_ip}")
                        
                        # Remove from queues upon successful deletion
                        if proxy_ip in delete_queue:
                            delete_queue.remove(proxy_ip)
                            logger.info(f"Removed {proxy_ip} from delete queue")
                        if proxy_ip in restart_queue:
                            restart_queue.remove(proxy_ip)
                            logger.info(f"Removed {proxy_ip} from restart queue")
                    else:
                        logger.warning(f"Failed to destroy Azure proxy -> {proxy_ip}")
                        
            except Exception as e:
                logger.error(f"Error processing proxy for deletion: {e}")
                continue
        
        # Report on any IPs that remain in the queues but weren't found
        if delete_queue:
            remaining_delete = [ip for ip in delete_queue if ip not in [
                p.ip_address for p in self.proxies if hasattr(p, 'ip_address') and p.ip_address
            ]]
            if remaining_delete:
                logger.warning(f"IPs remaining in delete queue that weren't found as proxies: {', '.join(remaining_delete)}")

    async def maintenance(self) -> float:
        """
        Perform maintenance on the provider, ensuring the configured number of proxies are running.
        
        Returns:
            float: Seconds until next maintenance should be performed
        """
        async with self.maintenance_lock:
            self.last_maintenance = datetime.datetime.now()
            logger.info(f"Performing maintenance for Azure provider (instance: {self.instance_id})")

            try:
                # First ensure the resource group exists
                logger.info(f"Ensuring Azure resource group exists for instance {self.instance_id}")
                functions.ensure_resource_group_exists(self.instance_config)
                
                # Then check the delete queue
                await self.check_delete()
                
                # Get current proxies
                self.proxies = functions.list_proxies(self.instance_config)
                
                # Get information about current proxies
                logger.info(f"Found {len(self.proxies)} Azure proxies running for instance {self.instance_id}")
                
                # Delete excess proxies if we have too many
                if len(self.proxies) > self.max_proxies:
                    excess_count = len(self.proxies) - self.max_proxies
                    logger.info(f"Deleting {excess_count} excess Azure proxies")
                    
                    # Sort by name to ensure consistent behavior
                    excess_proxies = sorted(self.proxies, key=lambda vm: vm.name)[:excess_count]
                    
                    # Delete excess proxies
                    for proxy in excess_proxies:
                        logger.info(f"Deleting excess Azure proxy: {proxy.name}")
                        functions.delete_proxy(proxy, self.instance_config)
                
                # Create new proxies if we don't have enough
                if len(self.proxies) < self.max_proxies:
                    needed_count = self.max_proxies - len(self.proxies)
                    logger.info(f"Creating {needed_count} new Azure proxies")
                    
                    # Create needed proxies
                    for _ in range(needed_count):
                        functions.create_proxy(self.instance_config)
                
                # Update the proxy list after maintenance
                self.proxies = functions.list_proxies(self.instance_config)
                
                # Return random interval for next maintenance
                interval = self.get_random_poll_interval()
                logger.info(f"Next Azure maintenance in {interval} seconds")
                return interval
            
            except Exception as e:
                logger.error(f"Error during Azure maintenance: {e}")
                # Return shorter interval on error to retry sooner
                return self.base_poll_interval // 2

    async def get_ip_info(self) -> List[Dict]:
        """
        Get information about all proxy IPs.
        
        Returns:
            List[Dict]: List of IP information dictionaries
        """
        # Ensure resource group exists
        try:
            functions.ensure_resource_group_exists(self.instance_config)
        except Exception as e:
            logger.error(f"Error ensuring Azure resource group exists: {e}")
            return []
        
        # First refresh the list of proxies
        try:
            self.proxies = functions.list_proxies(self.instance_config)
        except Exception as e:
            logger.error(f"Error listing Azure proxies: {e}")
            return []
        
        result = []
        for proxy in self.proxies:
            # Skip any proxies without an assigned IP
            if not hasattr(proxy, 'ip_address') or not proxy.ip_address:
                continue
            
            # Calculate how long the proxy has been running
            # The runtime_property might not be available, so falling back to now
            proxy_created_time = datetime.datetime.now(datetime.timezone.utc)
            if hasattr(proxy, 'time_created'):
                proxy_created_time = proxy.time_created
            
            uptime = (datetime.datetime.now(datetime.timezone.utc) - proxy_created_time).total_seconds()
            ready = uptime > self.startup_grace_period
            
            ip_info = {
                "ip": proxy.ip_address,
                "port": 8899,
                "username": settings.config["auth"]["username"],
                "password": settings.config["auth"]["password"],
                "ready": ready,
                "provider": "azure",
                "provider_instance": self.instance_id,
                "id": proxy.name
            }
            
            result.append(ip_info)
        
        return result

    async def destroy_proxy(self, proxy_id: str) -> bool:
        """
        Destroy a specific proxy.
        
        Args:
            proxy_id: ID of the proxy to destroy
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Destroying Azure proxy: {proxy_id}")
        try:
            result = functions.delete_proxy(proxy_id, self.instance_config)
            return result
        except Exception as e:
            logger.error(f"Error destroying Azure proxy {proxy_id}: {e}")
            return False


async def azure_start(instance_config, instance_id="default"):
    """
    Start Azure provider for the given instance configuration.
    
    Args:
        instance_config: Configuration for a specific Azure instance
        instance_id: Identifier for this instance
        
    Returns:
        List[Dict]: List of IP information dictionaries
    """
    provider = AzureProvider(settings.config["providers"]["azure"], 
                            instance_id=instance_id)
    await provider.initialize()
    return await provider.get_ip_info()


async def azure_manager(instance_name="default"):
    """
    Azure manager function for a specific instance.
    
    Args:
        instance_name: Name of the instance to manage
        
    Returns:
        List[Dict]: List of IP information dictionaries
    """
    instance_config = settings.config["providers"]["azure"]["instances"][instance_name]
    ip_info = await azure_start(instance_config, instance_name)
    settings.config["providers"]["azure"]["instances"][instance_name]["ips"] = ip_info
    return ip_info 