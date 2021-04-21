[![CodeCov Coverage][codecov-shield]][codecov-url]
[![Docker Cloud Build Status][docker-shield]][docker-url]
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
# CloudProxy

![cloudproxy](docs/images/cloudproxy.gif)

<!-- ABOUT THE PROJECT -->
## About The Project

The purpose of CloudProxy is to hide your scrapers IP behind the cloud. It allows you to spin up a pool of proxies using popular cloud providers with just an API token. No configuration needed. 

CloudProxy exposes an API with the IPs and credentials of the provisioned proxies. 

### Providers supported:
* [DigitalOcean](docs/digitalocean.md)

### Planned:
* AWS
* Google Cloud
* Azure
* Scaleway
* Vultr



### Inspired by
This project was inspired by [Scrapoxy](https://github.com/fabienvauchelles/scrapoxy), though that project no longer seems actively maintained. 

The primary advantage of CloudProxy over Scrapoxy is that CloudProxy only requires an API token from a cloud provider. CloudProxy automatically deploys and configures the proxy on the cloud instances without the user needing to preconfigure or copy an image.


<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* Python 3.8

### Installation

#### Docker (recommended)

   ```shell
   docker run -e USERNAME='CHANGE_THIS_USERNAME' \
       -e PASSWORD='CHANGE_THIS_PASSWORD' \
       -e DIGITALOCEAN_ACCESS_TOKEN='YOUR SECRET ACCESS KEY' \
       -e DIGITALOCEAN_MIN_SCALE=2 \
       -it -p 8000:8000 laffin/cloudproxy:main
   ```

#### Run locally

1. Clone the repo
   ```sh
   git clone https://github.com/claffin/cloudproxy.git
   ```
2. Create a Python virtual environment 
   ```sh
   python3 -m venv /path/to/new/virtual/environment
   ```
3. Activate new virtual environment 
   ```sh
   source /path/to/new/virtual/environment/bin/activate
   ```
4. Install requirements
   ```sh
   pip install -r requirements.txt
   ```
5. Create .env file in the project root to set environment variables
   ```sh
   DIGITALOCEAN_ACCESS_TOKEN=YOUR_DO_TOKEN 
   DIGITALOCEAN_MIN_SCALE=2 # number of proxies to deploy
   USERNAME=username # username for http auth for proxies
   PASSWORD=password # password for http auth for prxoies
   ```
6. Start CloudProxy
    ```sh
    python cloudproxy/main.py
    ```

<!-- USAGE EXAMPLES -->
## Usage

CloudProxy exposes an API on localhost:8000. Your application can use the below API to retrieve the IPs with auth for the proxy servers deployed. Then your application can use those IPs to proxy.


### List available proxy servers
#### Request

`GET /`

    curl -X 'GET' 'http://localhost:8000/' -H 'accept: application/json'

#### Response

    {"ips":["http://username:password:192.168.0.1:8899", "http://username:password:192.168.0.2:8899"]}

### List random proxy server
#### Request

`GET /random`

    curl -X 'GET' 'http://localhost:8000/random' -H 'accept: application/json'

#### Response

    ["http://username:password:192.168.0.1:8899"]

### Remove proxy server
#### Request

`DELETE /destroy`

    curl -X 'DELETE' 'http://localhost:8000/destroy?ip_address=192.1.1.1' -H 'accept: application/json'

#### Response

    ["Proxy to be destroyed"]

### Get provider
#### Request

`DELETE /provider/digitalocean`

    curl -X 'GET' 'http://localhost:8000/providers/digitalocean' -H 'accept: application/json'

#### Response

      {
        "ips": [
          "http://changeme:changeme@192.1.1.2:8899",
          "http://changeme:changeme@192.1.1.3:8899"
        ],
        "scaling": {
          "min_scaling": 2,
          "max_scaling": 2
        }
      }

### Update provider
#### Request

`PATCH /provider/digitalocean`

    curl -X 'PATCH' 'http://localhost:8000/providers/digitalocean?min_scaling=5&max_scaling=5' -H 'accept: application/json'

#### Response

      {
        "ips": [
          "http://changeme:changeme@192.1.1.2:8899",
          "http://changeme:changeme@192.1.1.3:8899"
        ],
        "scaling": {
          "min_scaling": 5,
          "max_scaling": 5
        }
      }

CloudProxy runs on a schedule of every 30 seconds, it will check if the minimum scaling has been met, if not then it will deploy the required number of proxies. The new proxy info will appear in IPs once they are deployed and ready to be used.

<!-- ROADMAP -->
## Roadmap

The project is at early alpha with limited features. In the future more providers will be supported, autoscaling will be implemented and a rich API to allow for blacklisting and recycling of proxies.

See the [open issues](https://github.com/claffin/cloudproxy/issues) for a list of proposed features (and known issues).



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->
## Contact

Your Name - [@christianlaffin](https://twitter.com/christianlaffin) - christian.laffin@gmail.com

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
