import os
from dotenv import load_dotenv

config = {
    "auth": {"username": "", "password": ""},
    "age_limit": 0,
    "providers": {
        "digitalocean": {
            "enabled": False,
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "region": "",
            "secrets": {"access_token": ""},
        },
        "aws": {
            "enabled": False,
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "region": "",
            "ami": "",
            "secrets": {"access_key_id": "", "secret_access_key": ""},
            "spot": False,
        },
        "gcp": {
            "enabled": False,
            "project": "",
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "zone": "",
            "image_project": "",
            "image_family": "",
            "secrets": {"service_account_key": ""},
        },
        "hetzner": {
            "enabled": False,
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "location": "",
            "datacenter": "",
            "secrets": {"access_token": ""},
        },
    },
}

delete_queue = set()
restart_queue = set()

load_dotenv()

# Set proxy authentication
config["auth"]["username"] = os.environ.get("USERNAME", "changeme")
config["auth"]["password"] = os.environ.get("PASSWORD", "changeme")
config["age_limit"] = int(os.environ.get('AGE_LIMIT', 0))

# Set DigitalOcean config
config["providers"]["digitalocean"]["enabled"] = os.environ.get(
    "DIGITALOCEAN_ENABLED", False
)
config["providers"]["digitalocean"]["secrets"]["access_token"] = os.environ.get(
    "DIGITALOCEAN_ACCESS_TOKEN"
)
config["providers"]["digitalocean"]["scaling"]["min_scaling"] = int(
    os.environ.get("DIGITALOCEAN_MIN_SCALING", 2)
)
config["providers"]["digitalocean"]["scaling"]["max_scaling"] = int(
    os.environ.get("DIGITALOCEAN_MAX_SCALING", 2)
)
config["providers"]["digitalocean"]["size"] = os.environ.get(
    "DIGITALOCEAN_SIZE", "s-1vcpu-1gb"
)
config["providers"]["digitalocean"]["region"] = os.environ.get(
    "DIGITALOCEAN_REGION", "lon1"
)

# Set AWS Config
config["providers"]["aws"]["enabled"] = os.environ.get("AWS_ENABLED", False)
config["providers"]["aws"]["secrets"]["access_key_id"] = os.environ.get(
    "AWS_ACCESS_KEY_ID"
)
config["providers"]["aws"]["secrets"]["secret_access_key"] = os.environ.get(
    "AWS_SECRET_ACCESS_KEY"
)
config["providers"]["aws"]["scaling"]["min_scaling"] = int(
    os.environ.get("AWS_MIN_SCALING", 2)
)
config["providers"]["aws"]["scaling"]["max_scaling"] = int(
    os.environ.get("AWS_MAX_SCALING", 2)
)
config["providers"]["aws"]["size"] = os.environ.get("AWS_SIZE", "t2.micro")
config["providers"]["aws"]["region"] = os.environ.get("AWS_REGION", "eu-west-2")
config["providers"]["aws"]["spot"] = os.environ.get("AWS_SPOT", False)
config["providers"]["aws"]["ami"] = os.environ.get("AWS_AMI", "ami-096cb92bb3580c759")

# Set GCP Config
config["providers"]["gcp"]["enabled"] = os.environ.get("GCP_ENABLED", False)
config["providers"]["gcp"]["project"] = os.environ.get("GCP_PROJECT")
config["providers"]["gcp"]["secrets"]["service_account_key"] = os.environ.get(
    "GCP_SERVICE_ACCOUNT_KEY"
)

config["providers"]["gcp"]["scaling"]["min_scaling"] = int(
    os.environ.get("GCP_MIN_SCALING", 2)
)
config["providers"]["gcp"]["scaling"]["max_scaling"] = int(
    os.environ.get("GCP_MAX_SCALING", 2)
)
config["providers"]["gcp"]["size"] = os.environ.get("GCP_SIZE", "f1-micro")
config["providers"]["gcp"]["zone"] = os.environ.get("GCP_REGION", "us-central1-a")
config["providers"]["gcp"]["image_project"] = os.environ.get("GCP_IMAGE_PROJECT", "ubuntu-os-cloud")
config["providers"]["gcp"]["image_family"] = os.environ.get("GCP_IMAGE_FAMILY", "ubuntu-minimal-2004-lts")

# Set Hetzner config
config["providers"]["hetzner"]["enabled"] = os.environ.get(
    "HETZNER_ENABLED", False
)
config["providers"]["hetzner"]["secrets"]["access_token"] = os.environ.get(
    "HETZNER_ACCESS_TOKEN"
)
config["providers"]["hetzner"]["scaling"]["min_scaling"] = int(
    os.environ.get("HETZNER_MIN_SCALING", 2)
)
config["providers"]["hetzner"]["scaling"]["max_scaling"] = int(
    os.environ.get("HETZNER_MAX_SCALING", 2)
)
config["providers"]["hetzner"]["size"] = os.environ.get(
    "HETZNER_SIZE", "cx11"
)
config["providers"]["hetzner"]["location"] = os.environ.get(
    "HETZNER_LOCATION", "nbg1"
)
# config["providers"]["hetzner"]["datacenter"] = os.environ.get(
#     "HETZNER_DATACENTER", "dc3"
# )
