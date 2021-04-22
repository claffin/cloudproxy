import os
from dotenv import load_dotenv

config = {
    "auth": {
        "username": "",
        "password": ""
    },
    "providers": {
        "digitalocean": {
            "ips": [],
            "scaling": {
                "min_scaling": 0,
                "max_scaling": 0
            },
            "secrets": {
                "access_token": ""
            }
        }
    }
}

delete_queue = []

load_dotenv()

# Set proxy authentication
config["auth"]["username"] = os.environ.get("USERNAME", "changeme")
config["auth"]["password"] = os.environ.get("PASSWORD", "changeme")

# Set DigitalOceana config
config["providers"]["digitalocean"]["secrets"]["access_token"] = os.environ.get("DIGITALOCEAN_ACCESS_TOKEN")
config["providers"]["digitalocean"]["scaling"]["min_scaling"] = int(os.environ.get("DIGITALOCEAN_MIN_SCALE", 2))
config["providers"]["digitalocean"]["scaling"]["max_scaling"] = int(os.environ.get("DIGITALOCEAN_MAX_SCALE", 2))
