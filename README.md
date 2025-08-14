[![Code Coverage][coverage-shield]][codecov-url]
[![Code Quality][quality-shield]][codacy-url]
[![Docker Build][build-shield]][docker-url]
[![Docker Pulls][docker-pulls-shield]][docker-url]
[![Python Version][python-shield]][python-url]
[![License][license-shield]][license-url]
[![Last Commit][commit-shield]][commit-url]
[![Open Issues][issues-shield]][issues-url]
[![Stars][stars-shield]][stars-url]
[![Contributors][contributors-shield]][contributors-url]

[coverage-shield]: https://img.shields.io/codecov/c/github/claffin/cloudproxy?style=for-the-badge&logo=codecov&logoColor=white
[quality-shield]: https://img.shields.io/codacy/grade/39a9788caa854baebe01beb720e9c5a8?style=for-the-badge&logo=codacy&logoColor=white
[build-shield]: https://img.shields.io/github/actions/workflow/status/claffin/cloudproxy/main.yml?style=for-the-badge&logo=docker&logoColor=white
[docker-pulls-shield]: https://img.shields.io/docker/pulls/laffin/cloudproxy?style=for-the-badge&logo=docker&logoColor=white
[python-shield]: https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python&logoColor=white
[license-shield]: https://img.shields.io/github/license/claffin/cloudproxy?style=for-the-badge&logo=opensourceinitiative&logoColor=white
[commit-shield]: https://img.shields.io/github/last-commit/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white
[issues-shield]: https://img.shields.io/github/issues/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white
[stars-shield]: https://img.shields.io/github/stars/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white
[contributors-shield]: https://img.shields.io/github/contributors/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white

[python-url]: https://www.python.org/downloads/
[codecov-url]: https://app.codecov.io/gh/claffin/cloudproxy
[codacy-url]: https://www.codacy.com/gh/claffin/cloudproxy/dashboard
[docker-url]: https://hub.docker.com/r/laffin/cloudproxy
[license-url]: https://github.com/claffin/cloudproxy/blob/master/LICENSE.txt
[commit-url]: https://github.com/claffin/cloudproxy/commits/main
[issues-url]: https://github.com/claffin/cloudproxy/issues
[stars-url]: https://github.com/claffin/cloudproxy/stargazers
[contributors-url]: https://github.com/claffin/cloudproxy/graphs/contributors
# CloudProxy

![cloudproxy](docs/images/cloudproxy.gif)

## Table of Contents

- [About The Project](#about-the-project)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Development](#development)
- [Usage](#usage)
  - [Web Interface](#web-interface)
  - [API Documentation](#api-documentation)
  - [Programmatic Usage](#programmatic-usage)
- [Rolling Deployments](#rolling-deployments)
- [Multi-Account Provider Support](#multi-account-provider-support)
- [API Examples](#cloudproxy-api-examples)
- [Roadmap](#roadmap)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Troubleshooting](#troubleshooting)

<!-- ABOUT THE PROJECT -->
## About The Project

The purpose of CloudProxy is to hide your scrapers IP behind the cloud. It allows you to spin up a pool of proxies using popular cloud providers with just an API token. No configuration needed. 

CloudProxy exposes an API and modern UI for managing your proxy infrastructure. It includes:
- Interactive API documentation with Swagger UI
- Modern web interface for proxy management
- Real-time proxy status monitoring
- Easy scaling controls
- Multi-provider support

### Providers supported:
* [DigitalOcean](docs/digitalocean.md)
* [AWS](docs/aws.md)
* [Google Cloud](docs/gcp.md)
* [Hetzner](docs/hetzner.md)
* [Vultr](docs/vultr.md)

### Planned:
* Azure
* Scaleway

### Features:
* **Docker-first deployment** - Simple, isolated, production-ready
* Modern UI with real-time updates
* Interactive API documentation
* Multi-provider support
* Multiple accounts per provider
* Automatic proxy rotation
* **Rolling deployments** - Zero-downtime proxy recycling
* Health monitoring
* Fixed proxy pool management (maintains target count)

Please always scrape nicely, respectfully.

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

CloudProxy is designed to run as a Docker container:

* **Docker** - Required for running CloudProxy (recommended for all deployments)
* **Python 3.9+** - Only needed for development or custom integrations

### Installation

#### Docker Deployment (Recommended)

CloudProxy is distributed as a Docker image for easy deployment:

```bash
# Quick start with DigitalOcean
docker run -d \
  -e PROXY_USERNAME='your_username' \
  -e PROXY_PASSWORD='your_password' \
  -e DIGITALOCEAN_ENABLED=True \
  -e DIGITALOCEAN_ACCESS_TOKEN='your_token' \
  -p 8000:8000 \
  laffin/cloudproxy:latest

# Using environment file (recommended for production)
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  laffin/cloudproxy:0.6.0-beta  # Use specific version tag
```

**Docker Compose Example:**
```yaml
version: '3.8'
services:
  cloudproxy:
    image: laffin/cloudproxy:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
```

It is recommended to use a Docker image tagged to a specific version (e.g., `laffin/cloudproxy:0.6.0-beta`). See [releases](https://github.com/claffin/cloudproxy/releases) for the latest version.

#### Environment Configuration

##### Authentication
CloudProxy requires authentication configuration for the proxy servers:

- `PROXY_USERNAME`, `PROXY_PASSWORD` - Basic authentication credentials (alphanumeric characters only)
- `ONLY_HOST_IP` - Set to `True` to restrict access to the host server IP only
- Both methods can be used simultaneously for enhanced security

##### Optional Settings
- `AGE_LIMIT` - Proxy age limit in seconds (0 = disabled, default: disabled)

See individual [provider documentation](docs/) for provider-specific environment variables.

#### Python Package (Development & Integration)

For development or integrating CloudProxy into existing Python applications:

```bash
# Install from PyPI
pip install cloudproxy

# Or install from source for development
git clone https://github.com/claffin/cloudproxy.git
cd cloudproxy
pip install -e .
```

See the [Python Package Usage Guide](docs/python-package-usage.md) for development and integration examples.

## Testing

CloudProxy includes a comprehensive test suite to ensure reliability:

### Unit Tests
```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_specific.py -v

# Run with coverage
pytest --cov=cloudproxy tests/
```

### End-to-End Testing
**Warning:** These tests create real cloud instances and will incur costs!

```bash
# Run full end-to-end test
./test_cloudproxy.sh

# Run without cleanup (for debugging)
./test_cloudproxy.sh --no-cleanup --skip-connection-test

# Test specific providers
./test_cloudproxy.sh --provider digitalocean
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/claffin/cloudproxy.git
cd cloudproxy

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt

# Run the application locally
python -m cloudproxy
```

### UI Development

```bash
# Navigate to UI directory
cd cloudproxy-ui

# Install dependencies
npm install

# Run development server (hot reload enabled)
npm run serve

# Build for production
npm run build
```

### Adding a New Provider

1. Create a new directory under `cloudproxy/providers/`
2. Implement `main.py` with the provider orchestration logic
3. Implement `functions.py` with cloud API interactions
4. Follow the standard interface pattern used by existing providers
5. Add configuration handling in `providers/config.py`
6. Add tests in `tests/test_provider_name.py`

### Code Style

- Python code follows PEP 8 standards
- Use type hints for function parameters and returns
- Add comprehensive error handling with Loguru logging
- Write unit tests for all new functionality

<!-- USAGE EXAMPLES -->
## Usage

CloudProxy provides multiple interfaces for managing your proxy infrastructure:

### Web Interface
Access the UI at `http://localhost:8000/ui` to:
- View proxy status across all providers
- Scale proxy instances up/down
- Monitor health status
- Remove individual proxies
- View active proxy count

### API Documentation
Access the interactive API documentation at `http://localhost:8000/docs` to:
- Explore available endpoints
- Test API calls directly
- View request/response schemas
- Understand authentication requirements

### Programmatic Usage
CloudProxy exposes a RESTful API on localhost:8000. Your application can use the API to retrieve and manage proxy servers. All responses include metadata with request ID and timestamp for tracking.

Example of retrieving and using a random proxy:

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

For more detailed examples of using CloudProxy as a Python package, see the [Python Package Usage Guide](docs/python-package-usage.md).

## Rolling Deployments

CloudProxy supports rolling deployments to ensure zero-downtime proxy recycling. This feature maintains a minimum number of healthy proxies during age-based recycling operations.

### Configuration

Enable rolling deployments with these environment variables:

```bash
# Enable rolling deployments
ROLLING_DEPLOYMENT=True

# Minimum proxies to keep available during recycling
ROLLING_MIN_AVAILABLE=3  

# Maximum proxies to recycle simultaneously
ROLLING_BATCH_SIZE=2
```

### How It Works

When proxies reach their age limit:
1. The system checks if recycling would violate minimum availability
2. Proxies are recycled in batches to maintain service continuity
3. New proxies are created as old ones are removed
4. The process continues until all aged proxies are replaced

### Monitoring

Check rolling deployment status via the API:

```bash
# Get overall status
curl http://localhost:8000/rolling

# Get provider-specific status
curl http://localhost:8000/rolling/digitalocean
```

For detailed documentation, see the [Rolling Deployments Guide](docs/rolling-deployments.md).

## Multi-Account Provider Support

CloudProxy now supports multiple accounts per provider, allowing you to:

- Use multiple API keys or access tokens for the same provider
- Configure different regions, sizes, and scaling parameters per account
- Organize proxies by account/instance for better management
- Scale each account independently

Each provider can have multiple "instances", which represent different accounts or configurations. Each instance has its own:

- Scaling parameters (min/max)
- Region settings
- Size configuration
- API credentials
- IP addresses

To configure multiple instances, use environment variables with the instance name in the format:
```
PROVIDERNAME_INSTANCENAME_VARIABLE
```

For example, to configure two DigitalOcean accounts:
```shell
# Default DigitalOcean account
DIGITALOCEAN_ENABLED=True
DIGITALOCEAN_ACCESS_TOKEN=your_first_token
DIGITALOCEAN_DEFAULT_REGION=lon1
DIGITALOCEAN_DEFAULT_MIN_SCALING=2

# Second DigitalOcean account
DIGITALOCEAN_SECONDACCOUNT_ENABLED=True
DIGITALOCEAN_SECONDACCOUNT_ACCESS_TOKEN=your_second_token
DIGITALOCEAN_SECONDACCOUNT_REGION=nyc1
DIGITALOCEAN_SECONDACCOUNT_MIN_SCALING=3
```

## CloudProxy API Examples

CloudProxy exposes a comprehensive REST API for managing your proxy infrastructure. Here are some common examples:

### Quick Examples

#### Get a random proxy
```bash
curl -X 'GET' 'http://localhost:8000/random' -H 'accept: application/json'
```

#### List all proxies
```bash
curl -X 'GET' 'http://localhost:8000/' -H 'accept: application/json'
```

#### Set target proxy count
```bash
# CloudProxy will maintain exactly 5 proxies (DigitalOcean)
curl -X 'PATCH' 'http://localhost:8000/providers/digitalocean' \
  -H 'Content-Type: application/json' \
  -d '{"min_scaling": 5, "max_scaling": 5}'

# Or for Vultr
curl -X 'PATCH' 'http://localhost:8000/providers/vultr' \
  -H 'Content-Type: application/json' \
  -d '{"min_scaling": 3, "max_scaling": 3}'
```

### Python Usage Example
```python
import requests

# Get a random proxy
response = requests.get("http://localhost:8000/random").json()
proxy_url = response["proxy"]["url"]

# Use the proxy
proxies = {"http": proxy_url, "https": proxy_url}
result = requests.get("https://api.ipify.org", proxies=proxies)
```

For comprehensive API documentation with all endpoints, request/response schemas, and advanced usage examples, see the [API Examples Documentation](docs/api-examples.md).

CloudProxy runs on a schedule of every 30 seconds to maintain the target number of proxies specified by MIN_SCALING. If the current count differs from the target, it will create or remove proxies as needed. The new proxy info will appear in IPs once they are deployed and ready to be used.

<!-- ROADMAP -->
## Roadmap

The project is at early alpha with limited features. Future enhancements may include:
- Support for additional cloud providers
- Autoscaling based on demand (MIN_SCALING and MAX_SCALING)
- Enhanced API for blacklisting and recycling of proxies
- Load-based proxy management

See the [open issues](https://github.com/claffin/cloudproxy/issues) for a list of proposed features (and known issues).

## Limitations
This method of scraping via cloud providers has limitations, many websites have anti-bot protections and blacklists in place which can limit the effectiveness of CloudProxy. Many websites block datacenter IPs and IPs may be tarnished already due to IP recycling. Rotating the CloudProxy proxies regularly may improve results. The best solution for scraping is via proxy services providing residential IPs, which are less likely to be blocked, however are much more expensive. CloudProxy is a much cheaper alternative for scraping sites that do not block datacenter IPs nor have advanced anti-bot protection. This a point frequently made when people share this project which is why I am including this in the README. 

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

My target is to review all PRs within a week of being submitted, though sometimes it may be sooner or later.

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Christian Laffin - [@christianlaffin](https://twitter.com/christianlaffin) - christian.laffin@gmail.com

Project Link: [https://github.com/claffin/cloudproxy](https://github.com/claffin/cloudproxy)

<!-- TROUBLESHOOTING -->
## Troubleshooting

### Common Issues

#### Proxies not being created
- Check that the provider is enabled (e.g., `DIGITALOCEAN_ENABLED=True`)
- Verify API credentials are correct and have necessary permissions
- Check the logs for authentication errors
- Ensure minimum scaling is set above 0

#### Authentication failures
- Verify `PROXY_USERNAME` and `PROXY_PASSWORD` are set
- Ensure credentials only contain alphanumeric characters (special characters may cause URL encoding issues)
- Check if `ONLY_HOST_IP` is restricting access

#### Provider-specific issues
- **AWS**: Ensure the AMI ID is valid for your region
- **GCP**: Check that the service account has necessary permissions
- **DigitalOcean**: Verify the access token has write permissions
- **Hetzner**: Ensure the API token is valid
- **Vultr**: Verify the API token has appropriate permissions and the selected plan/region is available

#### Docker container issues
```bash
# Check container logs
docker logs <container-id>

# Verify environment variables are passed correctly
docker exec <container-id> env | grep PROXY

# Test connectivity to the API
curl http://localhost:8000/providers
```

#### Proxies being deleted unexpectedly
- Check the `AGE_LIMIT` setting - proxies older than this will be automatically replaced
- Verify proxies are passing health checks
- Check cloud provider quotas and limits

#### UI not loading
- Ensure you're accessing `/ui` not just the root URL
- Check that the UI files were built correctly (`npm run build` in cloudproxy-ui/)
- Verify the FastAPI server is serving static files

For more detailed debugging, enable verbose logging by checking the application logs in the `logs/` directory.






