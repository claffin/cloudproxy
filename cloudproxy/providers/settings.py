import os
from dotenv import load_dotenv

config = {
    "auth": {
        "username": "",
        "password": ""
    },
    "providers": {
        "digitalocean": {
            "access_token": "",
            "ips": [],
            "scaling": {
                "min_scaling": 0,
                "max_scaling": 0
            }
        }
    }
}

delete_queue = []

load_dotenv()

# Set proxy authentication
config["auth"]["username"] = os.environ.get("USERNAME", "proxy")
config["auth"]["password"] = os.environ.get("PASSWORD")

# Set DigitalOceana config
config["providers"]["digitalocean"]["access_token"] = os.environ.get("DIGITALOCEAN_ACCESS_TOKEN")
config["providers"]["digitalocean"]["scaling"]["min_scaling"] = int(os.environ.get("DIGITALOCEAN_MIN_SCALE", 1))
config["providers"]["digitalocean"]["scaling"]["max_scaling"] = int(os.environ.get("DIGITALOCEAN_MAX_SCALE", 1))