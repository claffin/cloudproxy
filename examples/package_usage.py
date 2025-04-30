#!/usr/bin/env python
"""
Example script demonstrating how to use CloudProxy as a Python package
"""
import os
import time
import sys
import requests
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("cloudproxy_example.log", rotation="5 MB")

# Set required environment variables
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
    """Initialize CloudProxy programmatically"""
    from cloudproxy.providers import manager
    
    # Initialize the manager, which will start creating proxies based on min_scaling
    logger.info("Initializing CloudProxy manager")
    manager.init_schedule()
    
    # Wait for at least one proxy to be available
    # In production, you might want to implement a retry mechanism or queue
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

def start_api_server():
    """Start the FastAPI server to expose the API endpoints"""
    import cloudproxy.main as cloudproxy
    import threading
    
    # Start the API server in a background thread
    logger.info("Starting CloudProxy API server")
    api_thread = threading.Thread(target=cloudproxy.start, daemon=True)
    api_thread.start()
    
    # Give the server time to start
    time.sleep(3)
    logger.info("API server started")
    return api_thread

def test_proxy():
    """Test a random proxy by making a request to ipify.org"""
    try:
        # Get a random proxy from the CloudProxy API
        response = requests.get("http://localhost:8000/random")
        if response.status_code != 200:
            logger.error(f"Failed to get a random proxy: {response.text}")
            return False
        
        proxy_data = response.json()
        proxy_url = proxy_data["proxy"]["url"]
        logger.info(f"Using proxy: {proxy_url}")
        
        # Use the proxy to make a request to ipify.org
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        ip_response = requests.get("https://api.ipify.org?format=json", proxies=proxies)
        if ip_response.status_code == 200:
            ip_data = ip_response.json()
            logger.info(f"Request successful - IP address: {ip_data['ip']}")
            return True
        else:
            logger.error(f"Request failed: {ip_response.status_code}")
            return False
            
    except Exception as e:
        logger.exception(f"Error testing proxy: {str(e)}")
        return False

def list_all_proxies():
    """List all available proxies"""
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            proxy_data = response.json()
            logger.info(f"Total proxies: {proxy_data['total']}")
            for i, proxy in enumerate(proxy_data['proxies']):
                logger.info(f"Proxy {i+1}: {proxy['ip']}:{proxy['port']}")
            return True
        else:
            logger.error(f"Failed to get proxies: {response.status_code}")
            return False
    except Exception as e:
        logger.exception(f"Error listing proxies: {str(e)}")
        return False

def programmatic_management():
    """Demonstrate programmatic management of proxies"""
    from cloudproxy.providers import manager
    
    # Get all IPs
    all_ips = manager.get_all_ips()
    logger.info(f"All IPs: {all_ips}")
    
    # Get provider-specific IPs
    do_ips = manager.get_provider_ips("digitalocean")
    logger.info(f"DigitalOcean IPs: {do_ips}")
    
    # Update scaling
    logger.info("Updating scaling for DigitalOcean")
    manager.scaling_handler("digitalocean", min_scaling=2, max_scaling=4)
    
    # Get updated provider configuration
    providers = manager.get_config()
    do_config = providers.get("digitalocean", {})
    logger.info(f"Updated DigitalOcean configuration: {do_config}")

def main():
    """Main function"""
    logger.info("Starting CloudProxy example script")
    
    # Setup environment variables
    setup_environment()
    
    # Initialize CloudProxy
    if not initialize_cloudproxy():
        logger.error("Failed to initialize CloudProxy")
        return
    
    # Start the API server
    api_thread = start_api_server()
    
    # Run examples
    logger.info("Testing proxy functionality")
    test_proxy()
    
    logger.info("Listing all available proxies")
    list_all_proxies()
    
    logger.info("Demonstrating programmatic management")
    programmatic_management()
    
    logger.info("Example completed")
    
    # Keep the script running to maintain the API server
    # In a real application, this would be part of your main program logic
    try:
        while api_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down")

if __name__ == "__main__":
    main() 