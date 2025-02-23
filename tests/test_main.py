from fastapi.testclient import TestClient
import os

from cloudproxy.main import app
from cloudproxy.providers.settings import delete_queue, config

# Configure test environment
os.environ["DIGITALOCEAN_ENABLED"] = "false"

# Create test client
# Note: The HTTPX deprecation warning is internal to the library and doesn't affect functionality
client = TestClient(app)

# Set up test environment
config["providers"]["digitalocean"]["enabled"] = False
config["providers"]["digitalocean"]["ips"] = []
config["providers"]["digitalocean"]["scaling"]["min_scaling"] = 2
config["providers"]["digitalocean"]["scaling"]["max_scaling"] = 2
config["providers"]["digitalocean"]["size"] = "s-1vcpu-1gb"
config["providers"]["digitalocean"]["region"] = "lon1"


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"ips": []}


def test_random():
    response = client.get("/random")
    assert response.status_code == 200
    assert response.json() == {}


def test_remove_proxy():
    response = client.delete("/destroy?ip_address=192.168.0.0")
    assert response.status_code == 200
    assert response.json() == ["Proxy <192.168.0.0> to be destroyed"]
    assert delete_queue == {"192.168.0.0"}


def test_remove_proxy_failure():
    response = client.delete("/destroy?ip_address=thisisnotanip")
    assert response.status_code == 422


def test_providers_digitalocean():
    response = client.get("/providers/digitalocean")
    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "ips": [],
        "scaling": {
            "min_scaling": 2,
            "max_scaling": 2
        },
        "size": "s-1vcpu-1gb",
        "region": "lon1"
    }


def test_providers_404():
    response = client.get("/providers/notaprovider")
    assert response.status_code == 404


def test_configure():
    response = client.patch("/providers/digitalocean?min_scaling=4&max_scaling=4")
    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "ips": [],
        "scaling": {
            "min_scaling": 4,
            "max_scaling": 4
        },
        "size": "s-1vcpu-1gb",
        "region": "lon1"
    }
