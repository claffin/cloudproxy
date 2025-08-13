# API Documentation

CloudProxy provides a comprehensive REST API for managing proxy servers across multiple cloud providers.

## Quick Start

First, start CloudProxy with Docker:
```bash
docker run -d --name cloudproxy \
  -e PROXY_USERNAME='user' \
  -e PROXY_PASSWORD='pass' \
  -e DIGITALOCEAN_ENABLED=True \
  -e DIGITALOCEAN_ACCESS_TOKEN='your_token' \
  -p 8000:8000 \
  laffin/cloudproxy:latest
```

Then access the API:
```bash
# Get a random proxy
curl -X 'GET' 'http://localhost:8000/random' -H 'accept: application/json'

# List all proxies
curl -X 'GET' 'http://localhost:8000/' -H 'accept: application/json'

# Check health status
curl -X 'GET' 'http://localhost:8000/health' -H 'accept: application/json'
```

## Interactive Swagger UI Documentation

Access the interactive API documentation at `http://localhost:8000/docs`. The Swagger UI provides:
- Interactive endpoint testing
- Request/response examples
- Schema definitions
- Authentication details
- Real-time API exploration

## Base URL

When running CloudProxy in Docker:
- **From host machine:** `http://localhost:8000`
- **From other containers:** `http://cloudproxy:8000` (use container name)
- **From external clients:** `http://your-server-ip:8000`

Example Docker network setup:
```bash
# Create a network for your services
docker network create proxy-network

# Run CloudProxy on the network
docker run -d --name cloudproxy \
  --network proxy-network \
  -p 8000:8000 \
  --env-file .env \
  laffin/cloudproxy:latest

# Other containers can access it at http://cloudproxy:8000
docker run --network proxy-network alpine \
  wget -qO- http://cloudproxy:8000/random
```

## API Response Format

All API responses follow a standardized format that includes:

### Metadata Object
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  }
}
```

### Proxy Object
```json
{
  "ip": "192.168.1.1",
  "port": 8899,
  "auth_enabled": true,
  "url": "http://username:password@192.168.1.1:8899",
  "provider": "digitalocean",
  "instance": "default",
  "display_name": "My DigitalOcean Instance"
}
```

### Provider Object
```json
{
  "enabled": true,
  "ips": ["192.168.1.1", "192.168.1.2"],
  "scaling": {
    "min_scaling": 2,
    "max_scaling": 5
  },
  "size": "s-1vcpu-1gb",
  "region": "lon1",
  "instances": {
    "default": {
      "enabled": true,
      "ips": ["192.168.1.1", "192.168.1.2"],
      "scaling": {
        "min_scaling": 2,
        "max_scaling": 5
      },
      "size": "s-1vcpu-1gb",
      "region": "lon1"
    },
    "second-account": {
      "enabled": true,
      "ips": ["192.168.1.3", "192.168.1.4"],
      "scaling": {
        "min_scaling": 1,
        "max_scaling": 3
      },
      "size": "s-1vcpu-1gb",
      "region": "nyc1"
    }
  }
}
```

### Provider Instance Object
```json
{
  "enabled": true,
  "ips": ["192.168.1.1", "192.168.1.2"],
  "scaling": {
    "min_scaling": 2,
    "max_scaling": 5
  },
  "size": "s-1vcpu-1gb",
  "region": "lon1",
  "display_name": "My DigitalOcean Instance"
}
```

## API Endpoints

### Proxy Management

#### List Available Proxies
- `GET /?offset=0&limit=10`
- Supports pagination with offset and limit parameters
- Response format:
```json
{
  "metadata": { ... },
  "total": 5,
  "proxies": [
    {
      "ip": "192.168.1.1",
      "port": 8899,
      "auth_enabled": true,
      "url": "http://username:password@192.168.1.1:8899",
      "provider": "digitalocean",
      "instance": "default",
      "display_name": "My DigitalOcean Instance"
    }
  ]
}
```

#### Get Random Proxy
- `GET /random`
- Returns a single random proxy from the available pool
- Response format:
```json
{
  "metadata": { ... },
  "message": "Random proxy retrieved successfully",
  "proxy": {
    "ip": "192.168.1.1",
    "port": 8899,
    "auth_enabled": true,
    "url": "http://username:password@192.168.1.1:8899",
    "provider": "digitalocean",
    "instance": "default",
    "display_name": "My DigitalOcean Instance"
  }
}
```

#### Remove Proxy
- `DELETE /destroy?ip_address={ip}`
- Removes a specific proxy from the pool
- Response format:
```json
{
  "metadata": { ... },
  "message": "Proxy scheduled for deletion",
  "proxy": {
    "ip": "192.168.1.1",
    "port": 8899,
    "auth_enabled": true,
    "url": "http://username:password@192.168.1.1:8899"
  }
}
```

#### List Proxies Scheduled for Deletion
- `GET /destroy`
- Returns list of proxies scheduled for deletion
- Response format matches List Available Proxies

#### Restart Proxy
- `DELETE /restart?ip_address={ip}`
- Restarts a specific proxy instance
- Response format matches Remove Proxy response

#### List Proxies Scheduled for Restart
- `GET /restart`
- Returns list of proxies scheduled for restart
- Response format matches List Available Proxies

### Health and Status

#### Health Check
- `GET /health`
- Returns the health status of the CloudProxy service
- Response format:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-24T08:00:00Z"
}
```

#### Authentication Configuration
- `GET /auth`
- Returns the current authentication configuration
- Response format:
```json
{
  "metadata": { ... },
  "auth": {
    "username_configured": true,
    "password_configured": true,
    "only_host_ip": false,
    "host_ip": "192.168.1.100"
  }
}
```

### Provider Management

#### List All Providers
- `GET /providers`
- Returns configuration and status for all providers, including all instances
- Response format:
```json
{
  "metadata": { ... },
  "providers": {
    "digitalocean": {
      "enabled": true,
      "ips": ["192.168.1.1"],
      "scaling": {
        "min_scaling": 2,
        "max_scaling": 5
      },
      "size": "s-1vcpu-1gb",
      "region": "lon1",
      "instances": {
        "default": {
          "enabled": true,
          "ips": ["192.168.1.1", "192.168.1.2"],
          "scaling": {
            "min_scaling": 2,
            "max_scaling": 5
          },
          "size": "s-1vcpu-1gb",
          "region": "lon1"
        },
        "second-account": {
          "enabled": true,
          "ips": ["192.168.1.3", "192.168.1.4"],
          "scaling": {
            "min_scaling": 1,
            "max_scaling": 3
          },
          "size": "s-1vcpu-1gb",
          "region": "nyc1"
        }
      }
    },
    "aws": { ... }
  }
}
```

#### Get Provider Details
- `GET /providers/{provider}`
- Returns detailed information for a specific provider, including all instances
- Response format:
```json
{
  "metadata": { ... },
  "message": "Provider 'digitalocean' configuration retrieved successfully",
  "provider": {
    "enabled": true,
    "ips": ["192.168.1.1"],
    "scaling": {
      "min_scaling": 2,
      "max_scaling": 5
    },
    "size": "s-1vcpu-1gb",
    "region": "lon1"
  },
  "instances": {
    "default": {
      "enabled": true,
      "ips": ["192.168.1.1", "192.168.1.2"],
      "scaling": {
        "min_scaling": 2,
        "max_scaling": 5
      },
      "size": "s-1vcpu-1gb",
      "region": "lon1"
    },
    "second-account": {
      "enabled": true,
      "ips": ["192.168.1.3", "192.168.1.4"],
      "scaling": {
        "min_scaling": 1,
        "max_scaling": 3
      },
      "size": "s-1vcpu-1gb",
      "region": "nyc1"
    }
  }
}
```

#### Update Provider Scaling
- `PATCH /providers/{provider}`
- Updates the target proxy count for the default instance of a provider
- Request body:
```json
{
  "min_scaling": 2,  // Target number of proxies to maintain
  "max_scaling": 5   // Reserved for future use (must be >= min_scaling)
}
```
- Response format matches Get Provider Details
- Note: Currently only `min_scaling` affects proxy deployment. The system maintains exactly this number of proxies.

#### Get Provider Instance Details
- `GET /providers/{provider}/{instance}`
- Returns detailed information for a specific instance of a provider
- Response format:
```json
{
  "metadata": { ... },
  "message": "Provider 'digitalocean' instance 'default' configuration retrieved successfully",
  "provider": "digitalocean",
  "instance": "default",
  "config": {
    "enabled": true,
    "ips": ["192.168.1.1", "192.168.1.2"],
    "scaling": {
      "min_scaling": 2,
      "max_scaling": 5
    },
    "size": "s-1vcpu-1gb",
    "region": "lon1",
    "display_name": "My DigitalOcean Instance"
  }
}
```

#### Update Provider Instance Scaling
- `PATCH /providers/{provider}/{instance}`
- Updates the target proxy count for a specific instance of a provider
- Request body:
```json
{
  "min_scaling": 2,  // Target number of proxies to maintain
  "max_scaling": 5   // Reserved for future use (must be >= min_scaling)
}
```
- Response format matches Get Provider Instance Details
- Note: Currently only `min_scaling` affects proxy deployment. The system maintains exactly this number of proxies.

## Error Responses

All error responses follow a standard format:
```json
{
  "metadata": {
    "request_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2024-02-24T08:00:00Z"
  },
  "error": "ValidationError",
  "detail": "Invalid IP address format"
}
```

### Common HTTP Status Codes

| Status Code | Description | Example |
|------------|-------------|---------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Proxy IP or provider not found |
| 422 | Validation Error | Invalid input data format |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | CloudProxy service is starting up |

### Error Handling Examples

```python
import requests

try:
    response = requests.get("http://localhost:8000/random")
    response.raise_for_status()
    proxy = response.json()["proxy"]
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("No proxies available")
    elif e.response.status_code == 503:
        print("Service is starting up, please wait")
    else:
        print(f"API error: {e.response.json()['detail']}")
except requests.ConnectionError:
    print("Cannot connect to CloudProxy API")
```

## Authentication

### API Authentication
The CloudProxy API itself doesn't require authentication for accessing endpoints.

### Proxy Authentication
The proxy servers themselves use basic authentication configured via environment variables:

- **Basic Auth**: Set `PROXY_USERNAME` and `PROXY_PASSWORD`
- **IP-based Auth**: Set `ONLY_HOST_IP=True` to restrict access to the host server IP
- **Combined Auth**: Use both username/password and IP restriction for maximum security

Example proxy URL with authentication:
```
http://username:password@proxy-ip:8899
```

## Rate Limiting

Currently, CloudProxy API endpoints do not implement rate limiting. However:

- Cloud provider APIs may have their own rate limits
- Proxy creation is naturally limited by the scheduler (runs every 30 seconds)
- Bulk operations should be batched responsibly

## CORS Configuration

CloudProxy allows cross-origin requests from any origin by default. In production environments, you may want to restrict this using a reverse proxy or API gateway.

## See Also

- [API Examples with Code](api-examples.md) - Detailed examples in multiple languages
- [Python Package Usage](python-package-usage.md) - Using CloudProxy as a Python library
- [Provider Configuration](digitalocean.md) - Setting up cloud providers 