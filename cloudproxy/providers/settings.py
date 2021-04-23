import os
from dotenv import load_dotenv

config = {
    "auth": {"username": "", "password": ""},
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
            "secrets": {"access_key_id": "", "secret_access_key": ""},
        },
    },
}

delete_queue = []

load_dotenv()

# Set proxy authentication
config["auth"]["username"] = os.environ.get("USERNAME", "changeme")
config["auth"]["password"] = os.environ.get("PASSWORD", "changeme")

# Set DigitalOceana config
config["providers"]["digitalocean"]["enabled"] = os.environ.get(
    "DIGITALOCEAN_ENABLED", False
)
config["providers"]["digitalocean"]["secrets"]["access_token"] = os.environ.get(
    "DIGITALOCEAN_ACCESS_TOKEN"
)
config["providers"]["digitalocean"]["scaling"]["min_scaling"] = int(
    os.environ.get("DIGITALOCEAN_MIN_SCALE", 2)
)
config["providers"]["digitalocean"]["scaling"]["max_scaling"] = int(
    os.environ.get("DIGITALOCEAN_MAX_SCALE", 2)
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
    os.environ.get("AWS_MIN_SCALE", 2)
)
config["providers"]["aws"]["scaling"]["max_scaling"] = int(
    os.environ.get("AWS_MAX_SCALE", 2)
)
config["providers"]["aws"]["size"] = os.environ.get("AWS_SIZE", "t2.micro")
config["providers"]["aws"]["region"] = os.environ.get("AWS_REGION", "eu-west-2")
