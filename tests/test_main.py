from fastapi.testclient import TestClient
import os

from cloudproxy.main import app
from cloudproxy.providers.settings import delete_queue, config

# Configure test environment
os.environ["DIGITALOCEAN_ENABLED"] = "false"
os.environ["PROXY_USERNAME"] = "test_user"
os.environ["PROXY_PASSWORD"] = "test_pass"
os.environ["ONLY_HOST_IP"] = "False"

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

# Update auth config with test values
config["auth"]["username"] = os.environ["PROXY_USERNAME"]
config["auth"]["password"] = os.environ["PROXY_PASSWORD"]
config["no_auth"] = False


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "total" in data
    assert "proxies" in data
    assert isinstance(data["proxies"], list)
    assert data["total"] == 0


def test_random():
    response = client.get("/random")
    assert response.status_code == 404
    assert response.json() == {"detail": "No proxies available"}


def test_remove_proxy_list():
    response = client.get("/destroy")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "total" in data
    assert "proxies" in data
    assert isinstance(data["proxies"], list)
    assert data["total"] == len(data["proxies"])


def test_remove_proxy():
    response = client.delete("/destroy?ip_address=192.168.1.1")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "message" in data
    assert "proxy" in data
    assert data["message"] == "Proxy scheduled for deletion"
    assert data["proxy"]["ip"] == "192.168.1.1"


def test_restart_proxy_list():
    response = client.get("/restart")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "total" in data
    assert "proxies" in data
    assert isinstance(data["proxies"], list)
    assert data["total"] == len(data["proxies"])


def test_restart_proxy():
    response = client.delete("/restart?ip_address=192.168.1.1")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "message" in data
    assert "proxy" in data
    assert data["message"] == "Proxy scheduled for restart"
    assert data["proxy"]["ip"] == "192.168.1.1"


def test_providers_digitalocean():
    response = client.get("/providers/digitalocean")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "message" in data
    assert "provider" in data
    assert data["provider"] == {
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
    response = client.patch("/providers/digitalocean", json={
        "min_scaling": 4,
        "max_scaling": 4
    })
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "message" in data
    assert "provider" in data
    assert data["provider"] == {
        "enabled": False,
        "ips": [],
        "scaling": {
            "min_scaling": 4,
            "max_scaling": 4
        },
        "size": "s-1vcpu-1gb",
        "region": "lon1"
    }
