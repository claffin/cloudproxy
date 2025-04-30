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
[python-shield]: https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white
[license-shield]: https://img.shields.io/github/license/claffin/cloudproxy?style=for-the-badge&logo=opensourceinitiative&logoColor=white
[commit-shield]: https://img.shields.io/github/last-commit/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white
[issues-shield]: https://img.shields.io/github/issues/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white
[stars-shield]: https://img.shields.io/github/stars/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white
[contributors-shield]: https://img.shields.io/github/contributors/claffin/cloudproxy?style=for-the-badge&logo=github&logoColor=white

[python-url]: https://www.python.org/downloads/release/python-3110/
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

### Planned:
* Azure
* Scaleway
* Vultr

### Features:
* Modern UI with real-time updates
* Interactive API documentation
* Multi-provider support
* Multiple accounts per provider
* Automatic proxy rotation
* Health monitoring
* Easy scaling controls
* Docker-based deployment

Please always scrape nicely, respectfully.

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

You can use CloudProxy in two ways:

1. **Docker (recommended for running the service)**
   * Docker installed on your system

2. **Python Package (for development or integration)**
   * Python 3.9 or higher

### Installation

#### As a Python Package

CloudProxy is available as a Python package that you can install directly from PyPI:

```bash
pip install cloudproxy
```

Or install from source:

```bash
# Clone the repository
git clone https://github.com/claffin/cloudproxy.git
cd cloudproxy

# Install in development mode
pip install -e .

# Or build and install
pip install build
python -m build
pip install dist/cloudproxy-0.1.0-py3-none-any.whl
```

Once installed, you can import and use CloudProxy in your Python applications:

```python
from cloudproxy.providers import manager
import cloudproxy.main as cloudproxy

# Setup your environment variables first
# Start the CloudProxy service
cloudproxy.start()
```

#### Environment variables:

Basic authentication is used for proxy access. Configure via environment variables:
* PROXY_USERNAME
* PROXY_PASSWORD

##### Required
You have two available methods of proxy authentication: username and password or IP restriction. You can use either one or both simultaneously.

- `PROXY_USERNAME`, `PROXY_PASSWORD` - set the username and password for the forward proxy. The username and password should consist of alphanumeric characters. Using special characters may cause issues due to how URL encoding works.
- `ONLY_HOST_IP` - set this variable to true if you want to restrict access to the proxy only to the host server (i.e., the IP address of the server running the CloudProxy Docker container).

##### Optional
- `AGE_LIMIT` - set the age limit for your forward proxies in seconds. Once the age limit is reached, the proxy is replaced. A value of 0 disables the feature. Default: disabled.

See individual provider pages for environment variables required in above providers supported section.

#### Docker (recommended)

For example:

   ```shell
   docker run -e PROXY_USERNAME='CHANGE_THIS_USERNAME' \
       -e PROXY_PASSWORD='CHANGE_THIS_PASSWORD' \
       -e ONLY_HOST_IP=True \
       -e DIGITALOCEAN_ENABLED=True \
       -e DIGITALOCEAN_ACCESS_TOKEN='YOUR SECRET ACCESS KEY' \
       -it -p 8000:8000 laffin/cloudproxy:latest
   ```

It is recommended to use a Docker image tagged to a version e.g. `laffin/cloudproxy:0.6.0-beta`, see [releases](https://github.com/claffin/cloudproxy/releases) for latest version.

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

### List available proxy servers
#### Request

`GET /?offset=0&limit=10`

    curl -X 'GET' 'http://localhost:8000/?offset=0&limit=10' -H 'accept: application/json'

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

    curl -X 'GET' 'http://localhost:8000/random' -H 'accept: application/json'

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

    curl -X 'DELETE' 'http://localhost:8000/destroy?ip_address=192.1.1.1' -H 'accept: application/json'

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

    curl -X 'DELETE' 'http://localhost:8000/restart?ip_address=192.1.1.1' -H 'accept: application/json'

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

    curl -X 'GET' 'http://localhost:8000/providers' -H 'accept: application/json'

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
#### Request

`PATCH /providers/digitalocean`

    curl -X 'PATCH' 'http://localhost:8000/providers/digitalocean' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{"min_scaling": 5, "max_scaling": 5}'

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
      "min_scaling": 5,
      "max_scaling": 5
    },
    "size": "s-1vcpu-1gb",
    "region": "lon1"
  }
}
```

### Get provider instance
#### Request

`GET /providers/digitalocean/secondary`

    curl -X 'GET' 'http://localhost:8000/providers/digitalocean/secondary' -H 'accept: application/json'

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

    curl -X 'PATCH' 'http://localhost:8000/providers/digitalocean/secondary' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{"min_scaling": 2, "max_scaling": 5}'

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

CloudProxy runs on a schedule of every 30 seconds, it will check if the minimum scaling has been met, if not then it will deploy the required number of proxies. The new proxy info will appear in IPs once they are deployed and ready to be used.

<!-- ROADMAP -->
## Roadmap

The project is at early alpha with limited features. In the future more providers will be supported, autoscaling will be implemented and a rich API to allow for blacklisting and recycling of proxies.

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



<!-- ACKNOWLEDGEMENTS -->
## Acknowledgements

* []()
* []()
* []()





<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/claffin/cloudproxy.svg?style=flat-square
[contributors-url]: https://github.com/claffin/cloudproxy/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/claffin/cloudproxy.svg?style=flat-square
[forks-url]: https://github.com/claffin/cloudproxy/network/members
[stars-shield]: https://img.shields.io/github/stars/claffin/cloudproxy.svg?style=flat-square
[stars-url]: https://github.com/claffin/cloudproxy/stargazers
[issues-shield]: https://img.shields.io/github/issues/claffin/cloudproxy.svg?style=flat-square
[issues-url]: https://github.com/claffin/cloudproxy/issues
[license-shield]: https://img.shields.io/github/license/claffin/cloudproxy.svg?style=flat-square
[license-url]: https://github.com/claffin/cloudproxy/blob/master/LICENSE.txt
[docker-url]: https://hub.docker.com/r/laffin/cloudproxy
[docker-shield]: https://img.shields.io/github/workflow/status/claffin/cloudproxy/CI?style=flat-square
[codecov-url]: https://app.codecov.io/gh/claffin/cloudproxy
[codecov-shield]: https://img.shields.io/codecov/c/github/claffin/cloudproxy?style=flat-square
[codacy-shield]: https://img.shields.io/codacy/grade/39a9788caa854baebe01beb720e9c5a8?style=flat-square
[codacy-url]: https://www.codacy.com/gh/claffin/cloudproxy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=claffin/cloudproxy&amp;utm_campaign=Badge_Grade
