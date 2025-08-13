# Using CloudProxy as a Python Package (Development & Integration)

> **Note:** Docker is the recommended way to deploy CloudProxy in production. This guide is for developers who need to:
> - Integrate CloudProxy directly into Python applications
> - Develop custom automation workflows
> - Contribute to CloudProxy development
> - Build custom proxy management solutions
>
> For standard deployments, please use the [Docker installation method](../README.md#docker-deployment-recommended).

This guide explains how to install and use CloudProxy as a Python package for development and integration purposes.

## When to Use Docker vs Python Package

### Use Docker When:
- ✅ Deploying CloudProxy in production
- ✅ Running CloudProxy as a standalone service
- ✅ You need isolation from your system Python environment
- ✅ Managing CloudProxy through its web UI and API
- ✅ Running in containers, Kubernetes, or cloud platforms
- ✅ You want the simplest setup and maintenance

### Use Python Package When:
- ✅ Integrating proxy management into existing Python code
- ✅ Building custom automation that needs direct access to CloudProxy internals
- ✅ Developing or testing CloudProxy features
- ✅ Creating specialized proxy rotation logic
- ✅ Embedding CloudProxy in larger Python applications

## Installation

CloudProxy can be installed directly from PyPI for development use:

```bash
pip install cloudproxy
```

Or from source:

```bash
# Clone the repository
git clone https://github.com/claffin/cloudproxy.git
cd cloudproxy

# Install in development mode
pip install -e .

# Or build and install
pip install build
python -m build
pip install dist/cloudproxy-*.whl  # Use the generated wheel file
```

## Basic Usage

### Starting the CloudProxy Service

You can start the CloudProxy service programmatically in your application:

```python
import os
from cloudproxy.providers import manager
import cloudproxy.main as cloudproxy

# Set required environment variables
os.environ["PROXY_USERNAME"] = "your_username"
os.environ["PROXY_PASSWORD"] = "your_password"

# Configure provider(s)
os.environ["DIGITALOCEAN_ENABLED"] = "True"
os.environ["DIGITALOCEAN_ACCESS_TOKEN"] = "your_digitalocean_token"

# Start the CloudProxy service
cloudproxy.start()
```

### Using the API Programmatically

Instead of starting the full service, you can use CloudProxy functionality programmatically:

```python
import os
from cloudproxy.providers import manager

# Configure credentials
os.environ["DIGITALOCEAN_ENABLED"] = "True"
os.environ["DIGITALOCEAN_ACCESS_TOKEN"] = "your_digitalocean_token"

# Initialize the provider manager
manager.init_schedule()

# Get available proxies
proxies = manager.get_all_ips()
print(f"Available proxies: {proxies}")

# Set the target number of proxies for a specific provider
# Note: Only min_scaling is currently used - proxies will be maintained at this exact count
manager.scaling_handler("digitalocean", min_scaling=3, max_scaling=3)
```

## Direct Proxy Access (Without the API)

You can access and manage proxies directly from your code without starting the HTTP API server:

```python
import os
import random
from cloudproxy.providers import manager

# Configure environment
os.environ["PROXY_USERNAME"] = "your_username"
os.environ["PROXY_PASSWORD"] = "your_password"
os.environ["DIGITALOCEAN_ENABLED"] = "True"
os.environ["DIGITALOCEAN_ACCESS_TOKEN"] = "your_digitalocean_token"

# Initialize CloudProxy infrastructure
manager.init_schedule()

# Wait for proxies to be ready (simplified example)
import time
print("Waiting for proxies to be provisioned...")
for _ in range(30):  # Wait up to 5 minutes
    proxies = manager.get_all_ips()
    if proxies:
        break
    time.sleep(10)

# Get all available proxy IPs
all_ips = manager.get_all_ips()
print(f"Available proxies: {all_ips}")

# Format a random proxy for use with requests
if all_ips:
    # Select a random proxy IP
    random_ip = random.choice(all_ips)
    
    # Format as a proxy URL with authentication
    proxy_url = f"http://{os.environ['PROXY_USERNAME']}:{os.environ['PROXY_PASSWORD']}@{random_ip}:8899"
    
    # Use with requests
    import requests
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    response = requests.get("https://api.ipify.org?format=json", proxies=proxies)
    print(f"Your IP is: {response.json()['ip']}")
```

### Accessing Provider-Specific Proxies

You can also get proxies from specific providers or provider instances:

```python
# Get all IPs from a specific provider
do_ips = manager.get_provider_ips("digitalocean")

# Get IPs from a specific provider instance
do_secondary_ips = manager.get_provider_instance_ips("digitalocean", "secondary")

# Get all provider configuration
providers_config = manager.get_config()
```

### Creating Formatted Proxy URLs

CloudProxy stores the IPs of the proxy servers, but you need to format them correctly for use:

```python
def format_proxy_url(ip, username, password, port=8899):
    """Format a proxy IP into a URL with authentication"""
    return f"http://{username}:{password}@{ip}:{port}"

# Get a list of all formatted proxy URLs
username = os.environ.get("PROXY_USERNAME")
password = os.environ.get("PROXY_PASSWORD")
all_ips = manager.get_all_ips()

proxy_urls = [format_proxy_url(ip, username, password) for ip in all_ips]
```

### Load Balancing Across Proxies

You can implement a simple load balancing strategy:

```python
class ProxyRotator:
    """Simple proxy rotator for load balancing"""
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.current_index = 0
        self.proxies = []
        self.update_proxies()
        
    def update_proxies(self):
        """Update the list of available proxies"""
        all_ips = manager.get_all_ips()
        self.proxies = [
            f"http://{self.username}:{self.password}@{ip}:8899" 
            for ip in all_ips
        ]
        
    def get_next_proxy(self):
        """Get the next proxy in the rotation"""
        if not self.proxies:
            self.update_proxies()
            if not self.proxies:
                return None
                
        if self.current_index >= len(self.proxies):
            self.current_index = 0
            
        proxy = self.proxies[self.current_index]
        self.current_index += 1
        return proxy
        
    def get_proxy_dict(self):
        """Get a proxy dictionary for requests"""
        proxy = self.get_next_proxy()
        if not proxy:
            return {}
            
        return {
            "http": proxy,
            "https": proxy
        }

# Usage
rotator = ProxyRotator(
    username=os.environ.get("PROXY_USERNAME"),
    password=os.environ.get("PROXY_PASSWORD")
)

# Make requests with rotating proxies
for url in urls_to_scrape:
    proxies = rotator.get_proxy_dict()
    response = requests.get(url, proxies=proxies)
    # Process response...
```

## Integrating with Web Scraping Libraries

### Using with Requests

```python
import os
import requests

# Setup your proxy credentials
username = os.getenv("PROXY_USERNAME", "your_username")
password = os.getenv("PROXY_PASSWORD", "your_password")

# Function to get a proxy URL from CloudProxy
def get_proxy():
    response = requests.get("http://localhost:8000/random").json()
    return response["proxy"]["url"]

# Use the proxy with requests
def make_proxied_request(url):
    proxy_url = get_proxy()
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    return requests.get(url, proxies=proxies)

# Example usage
response = make_proxied_request("https://api.ipify.org?format=json")
print(f"IP detected: {response.json()}")
```

### Using with Selenium

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests

def get_proxy():
    response = requests.get("http://localhost:8000/random").json()
    proxy_details = response["proxy"]
    return proxy_details["ip"], proxy_details["port"]

def setup_selenium_with_proxy():
    proxy_ip, proxy_port = get_proxy()
    
    options = Options()
    options.add_argument(f'--proxy-server={proxy_ip}:{proxy_port}')
    
    # If proxy requires authentication
    # You'll need to use a proxy authentication extension or plugin
    
    driver = webdriver.Chrome(options=options)
    return driver

# Example usage
driver = setup_selenium_with_proxy()
driver.get("https://www.whatismyip.com/")
# The page should show the IP of your proxy
```

## Advanced Usage

### Managing Multiple Provider Instances

CloudProxy supports multiple instances of the same provider, which allows you to use different API keys or configurations:

```python
import os
from cloudproxy.providers import manager

# Setup the first DigitalOcean instance (default)
os.environ["DIGITALOCEAN_ENABLED"] = "True"
os.environ["DIGITALOCEAN_ACCESS_TOKEN"] = "first_token"
os.environ["DIGITALOCEAN_REGION"] = "lon1"
os.environ["DIGITALOCEAN_MIN_SCALING"] = "2"

# Setup a second DigitalOcean instance
os.environ["DIGITALOCEAN_SECONDARY_ENABLED"] = "True"
os.environ["DIGITALOCEAN_SECONDARY_ACCESS_TOKEN"] = "second_token"
os.environ["DIGITALOCEAN_SECONDARY_REGION"] = "nyc1"
os.environ["DIGITALOCEAN_SECONDARY_MIN_SCALING"] = "3"

# Initialize the manager
manager.init_schedule()

# Get all proxies from the first instance
do_proxies = manager.get_provider_instance_ips("digitalocean", "default")

# Get all proxies from the second instance
do_secondary_proxies = manager.get_provider_instance_ips("digitalocean", "secondary")
```

### Rotating Proxies Automatically

You can set up automatic proxy rotation by configuring the `AGE_LIMIT` environment variable:

```python
import os

# Set proxies to be replaced after 3600 seconds (1 hour)
os.environ["AGE_LIMIT"] = "3600"

# Then start CloudProxy as usual
from cloudproxy.providers import manager
import cloudproxy.main as cloudproxy

manager.init_schedule()
cloudproxy.start()
```

## Environment Configuration Reference

### Required Variables

- `PROXY_USERNAME`, `PROXY_PASSWORD`: Authentication credentials for the proxy servers
  - OR `ONLY_HOST_IP=True`: Restrict access to only the host IP

### Provider-Specific Variables

#### DigitalOcean
- `DIGITALOCEAN_ENABLED`: Set to "True" to enable
- `DIGITALOCEAN_ACCESS_TOKEN`: Your API token
- `DIGITALOCEAN_REGION`: Region to deploy in (default: "lon1")
- `DIGITALOCEAN_SIZE`: Droplet size (default: "s-1vcpu-1gb")
- `DIGITALOCEAN_MIN_SCALING`: Target number of proxies to maintain (default: 2)
- `DIGITALOCEAN_MAX_SCALING`: Reserved for future autoscaling (default: 2)

#### AWS
- `AWS_ENABLED`: Set to "True" to enable
- `AWS_ACCESS_KEY_ID`: Your AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key
- `AWS_REGION`: Region to deploy in (default: "us-east-1")
- `AWS_SIZE`: Instance type (default: "t2.micro")
- `AWS_MIN_SCALING`: Target number of proxies to maintain (default: 2)
- `AWS_MAX_SCALING`: Reserved for future autoscaling (default: 2)
- `AWS_AMI`: AMI ID to use (default varies by region)
- `AWS_SPOT`: Use spot instances (default: "False")

#### Google Cloud Platform
- `GCP_ENABLED`: Set to "True" to enable
- `GCP_SA_JSON`: Path to service account JSON file (preferred)
- `GCP_SERVICE_ACCOUNT_KEY`: Service account JSON content as string (alternative)
- `GCP_ZONE`: Zone to deploy in (default: "us-central1-a")
- `GCP_SIZE`: Machine type (default: "e2-micro")
- `GCP_MIN_SCALING`: Target number of proxies to maintain (default: 2)
- `GCP_MAX_SCALING`: Reserved for future autoscaling (default: 2)
- `GCP_PROJECT`: GCP project ID (required)

#### Hetzner
- `HETZNER_ENABLED`: Set to "True" to enable
- `HETZNER_API_TOKEN`: Your Hetzner API token
- `HETZNER_LOCATION`: Location to deploy in (default: "nbg1")
- `HETZNER_SIZE`: Server type (default: "cx11")
- `HETZNER_MIN_SCALING`: Target number of proxies to maintain (default: 2)
- `HETZNER_MAX_SCALING`: Reserved for future autoscaling (default: 2)

## Troubleshooting

### Common Issues

#### "No proxies available" error
- Check that you've correctly configured your cloud provider credentials
- Verify that MIN_SCALING is set to a value greater than 0
- Allow enough time for proxy deployment (can take 1-3 minutes)
- Remember that CloudProxy maintains exactly MIN_SCALING proxies, not a range

#### Authentication failures
- Ensure `PROXY_USERNAME` and `PROXY_PASSWORD` are correctly set
- Avoid special characters in credentials that might cause URL encoding issues

#### Proxies being blocked
- Consider increasing the `AGE_LIMIT` to rotate proxies more frequently
- Try using different cloud provider regions

### Logging

CloudProxy uses the `loguru` library for logging. You can configure it in your code:

```python
import sys
from loguru import logger

# Configure log level
logger.remove()
logger.add(sys.stderr, level="INFO")  # Change to DEBUG for more detailed logs

# Add file logging
logger.add("cloudproxy.log", rotation="10 MB")

# Then initialize CloudProxy
from cloudproxy.providers import manager
manager.init_schedule()
```