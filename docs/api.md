# API Documentation

CloudProxy provides a comprehensive API for managing proxy servers across multiple cloud providers. The API documentation is available in two formats:

## Interactive Swagger UI Documentation

Access the interactive API documentation at `http://localhost:8000/docs`. The Swagger UI provides:
- Interactive endpoint testing
- Request/response examples
- Schema definitions
- Authentication details
- Real-time API exploration

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
- Updates the scaling configuration for the default instance of a provider
- Request body:
```json
{
  "min_scaling": 2,
  "max_scaling": 5
}
```
- Response format matches Get Provider Details
- Validation ensures max_scaling >= min_scaling

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
- Updates the scaling configuration for a specific instance of a provider
- Request body:
```json
{
  "min_scaling": 2,
  "max_scaling": 5
}
```
- Response format matches Get Provider Instance Details
- Validation ensures max_scaling >= min_scaling

## Proxy of Proxies

CloudProxy can be configured to act as a single proxy endpoint that forwards requests to the managed proxies. This simplifies client configuration and enables features like load distribution and automatic failover.

### Enabling and Configuration

The proxy of proxies feature is controlled by the following environment variables:

- `PROXY_OF_PROXIES_ENABLED`: Set to `True` to enable the proxy server. Defaults to `False`.
- `PROXY_OF_PROXIES_PORT`: The port the proxy server will listen on. Defaults to `8080`.
- `PROXY_SELECTION_STRATEGY`: The strategy used to select a proxy from the available pool. Supported values are `random`, `round-robin`, and `least-used`. Defaults to `random`.

### How to Use

When enabled, the proxy server will run on the configured port (default 8080). Clients can configure their applications to use `http://your_cloudproxy_host:8080` as their proxy. CloudProxy will then handle forwarding the requests to an available managed proxy based on the selected strategy.

Authentication for the proxy of proxies uses the same basic authentication configured for the individual proxies via the `PROXY_USERNAME` and `PROXY_PASSWORD` environment variables.

## Error Responses

All error responses follow a standard format:
```json
{
  "metadata": { ... },
  "error": "ValidationError",
  "detail": "Invalid IP address format"
}
```

Common error codes:
- 404: Resource not found
- 422: Validation error (invalid input)
- 500: Internal server error

## Authentication

The API itself doesn't require authentication, but the proxy servers use basic authentication:
- Username and password are configured via environment variables
- IP-based authentication can be enabled with `ONLY_HOST_IP=True`

## Response Formats

All API responses are in JSON format. Error responses include:
- HTTP status code
- Error message
- Additional details when available

## Rate Limiting

Currently, there are no rate limits on the API endpoints. However, cloud provider API calls may be subject to rate limiting based on your provider's policies. 