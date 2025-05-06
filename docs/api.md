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

### Credential Management

These endpoints allow for dynamic management of cloud provider credentials while the application is running. Credentials managed via these endpoints are stored in-memory and will need to be re-added after an application restart.

#### Add or Update Credentials
- `POST /api/credentials/{provider_name}/{instance_id}`
- Adds new credentials or updates existing credentials for a specific provider instance.
- The `provider_name` should be one of `aws`, `gcp`, `digitalocean`, `hetzner`, etc.
- The `instance_id` is a user-defined identifier for this set of credentials (e.g., "my-work-account", "project-x-gcp"). This `instance_id` will be used by the application to find the appropriate credentials when interacting with the provider for the instance configuration defined in `settings.config` that has the same name.
- Request body:
```json
{
  "secrets": {
    "key1": "value1",
    "key2": "value2"
    // ... other provider-specific secrets
  }
}
```
- **Example for AWS (note the inclusion of `region`):**
```json
{
  "secrets": {
    "access_key_id": "YOUR_AWS_ACCESS_KEY_ID",
    "secret_access_key": "YOUR_AWS_SECRET_ACCESS_KEY",
    "region": "us-west-2" 
  }
}
```
- **Example for DigitalOcean:**
```json
{
  "secrets": {
    "access_token": "YOUR_DIGITALOCEAN_ACCESS_TOKEN"
  }
}
```
- **Example for GCP:**
```json
{
  "secrets": {
    "service_account_key": "{ \"type\": \"service_account\", ... }" 
  }
}
```
- **Example for Hetzner:**
```json
{
  "secrets": {
    "access_token": "YOUR_HETZNER_ACCESS_TOKEN"
  }
}
```
- Response format:
```json
{
  "message": "Credentials added/updated for {provider_name}/{instance_id}"
}
```

#### List Credential Configurations
- `GET /api/credentials`
- Lists all provider and instance ID combinations for which credentials are currently stored.
- Response format:
```json
[
  [
    "aws",
    "my-work-account"
  ],
  [
    "digitalocean",
    "default"
  ]
]
```

#### Remove Credentials
- `DELETE /api/credentials/{provider_name}/{instance_id}`
- Removes the stored credentials for a specific provider instance.
- Response format:
```json
{
  "message": "Credentials removed for {provider_name}/{instance_id}"
}
```

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
