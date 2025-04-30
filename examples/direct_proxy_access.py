#!/usr/bin/env python
"""
Example script demonstrating how to use CloudProxy directly without the API
"""
import os
import time
import sys
import random
import requests
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("direct_proxy_example.log", rotation="5 MB")

def setup_environment():
    """Setup required environment variables"""
    # Proxy authentication
    os.environ["PROXY_USERNAME"] = "example_user"
    os.environ["PROXY_PASSWORD"] = "example_pass"
    
    # Enable DigitalOcean provider
    # Replace with your own API token in production
    os.environ["DIGITALOCEAN_ENABLED"] = "True"
    os.environ["DIGITALOCEAN_ACCESS_TOKEN"] = "your_digitalocean_token"
    os.environ["DIGITALOCEAN_DEFAULT_MIN_SCALING"] = "1"
    os.environ["DIGITALOCEAN_DEFAULT_MAX_SCALING"] = "3"
    
    # Set proxy rotation (optional) - rotate after 1 hour
    os.environ["AGE_LIMIT"] = "3600"
    
    logger.info("Environment variables set up")

def initialize_cloudproxy():
    """Initialize CloudProxy directly without starting the API server"""
    from cloudproxy.providers import manager
    
    # Initialize the manager, which will start creating proxies based on min_scaling
    logger.info("Initializing CloudProxy manager")
    manager.init_schedule()
    
    # Wait for at least one proxy to be available
    logger.info("Waiting for proxies to be available...")
    max_wait = 180  # Maximum wait time of 3 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        proxies = manager.get_all_ips()
        if proxies:
            logger.info(f"Proxies are ready: {proxies}")
            return True
        logger.info("No proxies available yet, waiting 10 seconds...")
        time.sleep(10)
    
    logger.error("Timed out waiting for proxies")
    return False

class ProxyRotator:
    """Class to manage and rotate proxies"""
    def __init__(self):
        from cloudproxy.providers import manager
        self.manager = manager
        self.username = os.environ.get("PROXY_USERNAME")
        self.password = os.environ.get("PROXY_PASSWORD")
        self.port = 8899  # Default port for CloudProxy proxies
        self.current_index = 0
        self.proxies = []
        self.update_proxies()
    
    def update_proxies(self):
        """Get the latest list of available proxies"""
        ips = self.manager.get_all_ips()
        self.proxies = [
            f"http://{self.username}:{self.password}@{ip}:{self.port}"
            for ip in ips
        ]
        logger.info(f"Updated proxy list, {len(self.proxies)} proxies available")
    
    def get_random_proxy(self):
        """Get a random proxy from the available proxies"""
        if not self.proxies:
            self.update_proxies()
            
        if not self.proxies:
            logger.warning("No proxies available")
            return None
            
        return random.choice(self.proxies)
    
    def get_next_proxy(self):
        """Get the next proxy in the rotation"""
        if not self.proxies:
            self.update_proxies()
            
        if not self.proxies:
            logger.warning("No proxies available")
            return None
            
        if self.current_index >= len(self.proxies):
            self.current_index = 0
            
        proxy = self.proxies[self.current_index]
        self.current_index += 1
        return proxy
    
    def get_proxy_dict(self, proxy_url=None):
        """Convert a proxy URL to a requests proxy dictionary"""
        if proxy_url is None:
            proxy_url = self.get_next_proxy()
            
        if not proxy_url:
            return {}
            
        return {
            "http": proxy_url,
            "https": proxy_url
        }
    
    def get_all_providers(self):
        """Get information about all providers"""
        return self.manager.get_config()
    
    def scale_provider(self, provider, min_scaling, max_scaling):
        """Scale a specific provider"""
        self.manager.scaling_handler(provider, min_scaling, max_scaling)
        logger.info(f"Scaled {provider} to min:{min_scaling}, max:{max_scaling}")

def test_requests(rotator):
    """Test making requests through the proxy"""
    urls = [
        "https://api.ipify.org?format=json",
        "https://httpbin.org/ip",
        "https://icanhazip.com"
    ]
    
    for url in urls:
        try:
            # Get a proxy
            proxy_dict = rotator.get_proxy_dict()
            
            if not proxy_dict:
                logger.error("No proxy available for testing")
                continue
                
            # Make the request
            logger.info(f"Making request to {url} through {proxy_dict['http']}")
            response = requests.get(url, proxies=proxy_dict, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Request successful: {response.text.strip()}")
            else:
                logger.error(f"Request failed with status code {response.status_code}")
        
        except Exception as e:
            logger.exception(f"Error making request to {url}: {str(e)}")

def demonstrate_provider_management(rotator):
    """Demonstrate managing providers directly"""
    # Get all providers
    providers = rotator.get_all_providers()
    for provider, config in providers.items():
        if config.get("enabled"):
            logger.info(f"Provider {provider} is enabled")
            logger.info(f"  Current scaling: min={config.get('scaling', {}).get('min_scaling')}, max={config.get('scaling', {}).get('max_scaling')}")
            logger.info(f"  IPs: {config.get('ips', [])}")
    
    # Scale a provider
    logger.info("Scaling DigitalOcean to min:2, max:4")
    rotator.scale_provider("digitalocean", 2, 4)
    
    # Get updated configuration
    updated_providers = rotator.get_all_providers()
    digitalocean = updated_providers.get("digitalocean", {})
    logger.info(f"Updated DigitalOcean configuration: {digitalocean}")

def main():
    """Main function"""
    logger.info("Starting direct proxy access example")
    
    # Setup environment variables
    setup_environment()
    
    # Initialize CloudProxy without the API server
    if not initialize_cloudproxy():
        logger.error("Failed to initialize CloudProxy")
        return
    
    # Create proxy rotator
    rotator = ProxyRotator()
    
    # Test making requests through the proxies
    logger.info("Testing requests through proxies")
    test_requests(rotator)
    
    # Demonstrate provider management
    logger.info("Demonstrating provider management")
    demonstrate_provider_management(rotator)
    
    logger.info("Example completed")

if __name__ == "__main__":
    main() 