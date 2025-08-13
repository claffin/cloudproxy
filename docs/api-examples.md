# CloudProxy API Examples

This document provides detailed examples of using the CloudProxy REST API with Docker deployments.

## Starting CloudProxy

```bash
# Start CloudProxy with Docker
docker run -d --name cloudproxy \
  -e PROXY_USERNAME='myuser' \
  -e PROXY_PASSWORD='mypass' \
  -e DIGITALOCEAN_ENABLED=True \
  -e DIGITALOCEAN_ACCESS_TOKEN='your_token' \
  -p 8000:8000 \
  laffin/cloudproxy:latest

# Wait for CloudProxy to be ready
until curl -s http://localhost:8000/health > /dev/null; do
  echo "Waiting for CloudProxy to start..."
  sleep 2
done
```

## Authentication

Basic authentication is configured when starting the Docker container:
- `PROXY_USERNAME` - Username for proxy authentication  
- `PROXY_PASSWORD` - Password for proxy authentication

## API Endpoints

### List available proxy servers

#### Request
`GET /?offset=0&limit=10`

```bash
curl -X 'GET' 'http://localhost:8000/?offset=0&limit=10' -H 'accept: application/json'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "total": 2,
  "proxies": [
    {
      "ip": "192.168.1.1",
      "port": 8899,
      "auth_enabled": true,
      "url": "http://username:password@192.168.1.1:8899"
    },
    {
      "ip": "192.168.1.2",
      "port": 8899,
      "auth_enabled": true,
      "url": "http://username:password@192.168.1.2:8899"
    }
  ]
}
```

### Get random proxy server

#### Request
`GET /random`

```bash
curl -X 'GET' 'http://localhost:8000/random' -H 'accept: application/json'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "message": "Random proxy retrieved successfully",
  "proxy": {
    "ip": "192.168.1.1",
    "port": 8899,
    "auth_enabled": true,
    "url": "http://username:password@192.168.1.1:8899"
  }
}
```

### Remove proxy server

#### Request
`DELETE /destroy`

```bash
curl -X 'DELETE' 'http://localhost:8000/destroy?ip_address=192.1.1.1' -H 'accept: application/json'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "message": "Proxy scheduled for deletion",
  "proxy": {
    "ip": "192.1.1.1",
    "port": 8899,
    "auth_enabled": true,
    "url": "http://username:password@192.1.1.1:8899"
  }
}
```

### Restart proxy server

#### Request
`DELETE /restart`

```bash
curl -X 'DELETE' 'http://localhost:8000/restart?ip_address=192.1.1.1' -H 'accept: application/json'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "message": "Proxy scheduled for restart",
  "proxy": {
    "ip": "192.1.1.1",
    "port": 8899,
    "auth_enabled": true,
    "url": "http://username:password@192.1.1.1:8899"
  }
}
```

### Get providers

#### Request
`GET /providers`

```bash
curl -X 'GET' 'http://localhost:8000/providers' -H 'accept: application/json'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "providers": {
    "digitalocean": {
      "enabled": true,
      "ips": ["192.168.1.1"],
      "scaling": {
        "min_scaling": 2,
        "max_scaling": 2
      },
      "size": "s-1vcpu-1gb",
      "region": "lon1",
      "instances": {
        "default": {
          "enabled": true,
          "ips": ["192.168.1.1"],
          "scaling": {
            "min_scaling": 2,
            "max_scaling": 2
          },
          "size": "s-1vcpu-1gb",
          "region": "lon1",
          "display_name": "Default Account"
        },
        "secondary": {
          "enabled": true,
          "ips": ["192.168.1.2"],
          "scaling": {
            "min_scaling": 1,
            "max_scaling": 3
          },
          "size": "s-1vcpu-1gb",
          "region": "nyc1",
          "display_name": "US Account"
        }
      }
    },
    "aws": {
      "enabled": false,
      "ips": [],
      "scaling": {
        "min_scaling": 2,
        "max_scaling": 2
      },
      "size": "t2.micro",
      "region": "eu-west-2",
      "ami": "ami-096cb92bb3580c759",
      "spot": false
    }
  }
}
```

### Update provider scaling

**Note:** CloudProxy currently maintains a fixed number of proxies equal to `min_scaling`. The `max_scaling` parameter is reserved for future autoscaling features.

#### Request
`PATCH /providers/digitalocean`

```bash
curl -X 'PATCH' 'http://localhost:8000/providers/digitalocean' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"min_scaling": 5, "max_scaling": 5}'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "message": "Provider 'digitalocean' scaling configuration updated successfully",
  "provider": {
    "enabled": true,
    "ips": ["192.168.1.1", "192.168.1.2"],
    "scaling": {
      "min_scaling": 5,  // CloudProxy will maintain exactly 5 proxies
      "max_scaling": 5   // Reserved for future use
    },
    "size": "s-1vcpu-1gb",
    "region": "lon1"
  }
}
```

### Get provider instance

#### Request
`GET /providers/digitalocean/secondary`

```bash
curl -X 'GET' 'http://localhost:8000/providers/digitalocean/secondary' -H 'accept: application/json'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "message": "Provider 'digitalocean' instance 'secondary' configuration retrieved successfully",
  "provider": "digitalocean",
  "instance": "secondary",
  "config": {
    "enabled": true,
    "ips": ["192.168.1.2"],
    "scaling": {
      "min_scaling": 1,
      "max_scaling": 3
    },
    "size": "s-1vcpu-1gb",
    "region": "nyc1",
    "display_name": "US Account"
  }
}
```

### Update provider instance scaling

#### Request
`PATCH /providers/digitalocean/secondary`

```bash
curl -X 'PATCH' 'http://localhost:8000/providers/digitalocean/secondary' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"min_scaling": 2, "max_scaling": 5}'
```

#### Response
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "message": "Provider 'digitalocean' instance 'secondary' scaling configuration updated successfully",
  "provider": "digitalocean",
  "instance": "secondary",
  "config": {
    "enabled": true,
    "ips": ["192.168.1.2"],
    "scaling": {
      "min_scaling": 2,
      "max_scaling": 5
    },
    "size": "s-1vcpu-1gb",
    "region": "nyc1",
    "display_name": "US Account"
  }
}
```

## Python Usage Examples

### Basic proxy retrieval and usage

```python
import random
import requests

def get_random_proxy():
    response = requests.get("http://localhost:8000/random").json()
    return response["proxy"]["url"]

proxies = {
    "http": get_random_proxy(),
    "https": get_random_proxy()
}
my_request = requests.get("https://api.ipify.org", proxies=proxies)
```

### Managing proxy pool

```python
import requests

# Get all available proxies
response = requests.get("http://localhost:8000/").json()
proxy_list = response["proxies"]

# Scale up DigitalOcean proxies
requests.patch(
    "http://localhost:8000/providers/digitalocean",
    json={"min_scaling": 10, "max_scaling": 20}
)

# Remove a specific proxy
requests.delete(
    "http://localhost:8000/destroy",
    params={"ip_address": "192.168.1.1"}
)
```

### Advanced proxy rotation

```python
import requests
import time
from typing import List, Optional

class ProxyRotator:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.proxy_cache: List[str] = []
        self.last_refresh = 0
        self.refresh_interval = 300  # 5 minutes
    
    def get_proxy(self) -> Optional[str]:
        """Get a random proxy, refreshing cache if needed."""
        if time.time() - self.last_refresh > self.refresh_interval:
            self.refresh_cache()
        
        if not self.proxy_cache:
            return None
        
        return random.choice(self.proxy_cache)
    
    def refresh_cache(self):
        """Refresh the proxy cache from the API."""
        try:
            response = requests.get(f"{self.api_url}/").json()
            self.proxy_cache = [p["url"] for p in response["proxies"]]
            self.last_refresh = time.time()
        except Exception as e:
            print(f"Failed to refresh proxy cache: {e}")
    
    def remove_bad_proxy(self, proxy_url: str):
        """Remove a non-working proxy from the pool."""
        # Extract IP from proxy URL
        ip = proxy_url.split("@")[1].split(":")[0]
        
        # Remove from cache
        self.proxy_cache = [p for p in self.proxy_cache if ip not in p]
        
        # Request deletion from CloudProxy
        requests.delete(
            f"{self.api_url}/destroy",
            params={"ip_address": ip}
        )

# Usage
rotator = ProxyRotator()
proxy = rotator.get_proxy()

try:
    response = requests.get(
        "https://example.com",
        proxies={"http": proxy, "https": proxy},
        timeout=10
    )
except requests.exceptions.RequestException:
    # Remove bad proxy and try another
    rotator.remove_bad_proxy(proxy)
    proxy = rotator.get_proxy()
```

## Notes

- CloudProxy runs on a schedule of every 30 seconds to maintain the exact number of proxies specified by `min_scaling`
- Proxy deletion and restart operations are queued and processed asynchronously
- All API responses include metadata with request_id and timestamp for tracking
- The API documentation is also available interactively at `http://localhost:8000/docs`