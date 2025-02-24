# API Documentation

CloudProxy provides a comprehensive API for managing proxy servers across multiple cloud providers. The API documentation is available in two formats:

## Interactive Swagger UI Documentation

Access the interactive API documentation at `http://localhost:8000/docs`. The Swagger UI provides:
- Interactive endpoint testing
- Request/response examples
- Schema definitions
- Authentication details
- Real-time API exploration

## API Endpoints

### Proxy Management

#### List Available Proxies
- `GET /`
- Returns a list of all available proxy servers with authentication credentials
- Response format: `{"ips": ["http://username:password@192.168.0.1:8899", ...]}`

#### Get Random Proxy
- `GET /random`
- Returns a single random proxy from the available pool
- Useful for rotation-based scraping

#### Remove Proxy
- `DELETE /destroy?ip_address={ip}`
- Removes a specific proxy from the pool
- The proxy will be destroyed on the cloud provider

#### Restart Proxy (AWS & GCP only)
- `DELETE /restart?ip_address={ip}`
- Restarts a specific proxy instance
- Only available for AWS and GCP providers

### Provider Management

#### List All Providers
- `GET /providers`
- Returns configuration and status for all providers
- Includes scaling settings, regions, and active IPs
- Excludes sensitive information (API keys, credentials)

#### Get Provider Details
- `GET /providers/{provider}`
- Returns detailed information for a specific provider
- Available providers: digitalocean, aws, gcp, hetzner

#### Update Provider Scaling
- `PATCH /providers/{provider}?min_scaling={min}&max_scaling={max}`
- Updates the scaling configuration for a provider
- Both min_scaling and max_scaling must be provided

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