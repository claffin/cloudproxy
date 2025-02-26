# Testing CloudProxy

This document describes how to test the CloudProxy application, focusing on the `test_cloudproxy.sh` end-to-end test script.

## End-to-End Testing

The `test_cloudproxy.sh` script provides comprehensive end-to-end testing of CloudProxy, including:

- API testing
- Cloud provider integration
- Proxy deployment
- Proxy connectivity
- Cleanup

### Prerequisites

To run the end-to-end tests, you'll need:

1. Docker installed
2. jq installed (`apt install jq`)
3. Cloud provider credentials configured via environment variables or `.env` file
4. Internet connectivity

### Required Environment Variables

The test script requires various environment variables to interact with cloud providers:

**Authentication (Optional):**
- `PROXY_USERNAME`: Username for proxy authentication
- `PROXY_PASSWORD`: Password for proxy authentication

**DigitalOcean (Enabled by default):**
- `DO_TOKEN`: DigitalOcean API token

**AWS (Enabled by default):**
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

**Hetzner (Disabled by default):**
- `HETZNER_TOKEN`: Hetzner API token
- `HETZNER_ENABLED=true`: To enable Hetzner

**GCP (Disabled by default):**
- `GCP_SERVICE_ACCOUNT`: Path to GCP service account file
- `GCP_ENABLED=true`: To enable GCP

**Azure (Disabled by default):**
- `AZURE_CLIENT_ID`: Azure client ID
- `AZURE_CLIENT_SECRET`: Azure client secret
- `AZURE_TENANT_ID`: Azure tenant ID
- `AZURE_SUBSCRIPTION_ID`: Azure subscription ID
- `AZURE_ENABLED=true`: To enable Azure

### Command-Line Options

The test script supports several command-line options:

```
Usage: ./test_cloudproxy.sh [OPTIONS]
Options:
  --no-cleanup            Don't automatically clean up resources
  --skip-connection-test  Skip testing proxy connectivity
  --proxy-wait=SECONDS    Wait time for proxy initialization (default: 30)
  --help                  Show this help message
```

### Test Process

The script performs these operations in sequence:

1. **Environment Check:** Verifies required environment variables
2. **Docker Build:** Builds the CloudProxy Docker image
3. **Container Setup:** Runs the CloudProxy container
4. **API Tests:** Tests all REST API endpoints
5. **Provider Configuration:** Sets scaling parameters for enabled providers
6. **Proxy Creation:** Waits for proxy instances to be created
7. **Connectivity Test:** Tests connectivity through a random proxy
8. **Proxy Management:** Tests proxy deletion and restart functionality
9. **Scaling Down:** Tests scaling down providers
10. **Web Interface Check:** Verifies the UI and API docs are accessible
11. **Cleanup:** Scales down all providers and removes resources

### Troubleshooting Failed Tests

If proxy connectivity tests fail:

1. Check the logs for the specific proxy instance (the script shows these)
2. Verify your cloud provider firewall allows access to port 8899
3. Confirm the proxy authentication settings match your environment variables
4. Try increasing the `--proxy-wait` time (some providers take longer to initialize)
5. SSH into a proxy instance to check the logs directly:
   - System logs
   - Proxy service status
   - Network configuration

### Cost Considerations

**IMPORTANT:** This test script creates real cloud instances that cost money.

To minimize costs:
- Always allow the cleanup process to run (don't use `--no-cleanup` unless necessary)
- Keep testing sessions short
- Set lower min/max scaling values if you're just testing functionality

## Unit Testing

CloudProxy also includes unit tests that can be run with pytest:

```bash
pytest -v
```

These tests use mocks and don't create actual cloud instances, making them safe to run without incurring costs. 