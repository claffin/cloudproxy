import os
from dotenv import load_dotenv

config = {
    "auth": {"username": "", "password": ""},
    "no_auth": False,
    "only_host_ip": False,
    "age_limit": 0,
    "providers": {
        "digitalocean": {
            "instances": {
                "default": {
            "enabled": False,
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "region": "",
                    "display_name": "DigitalOcean",
            "secrets": {"access_token": ""},
                }
            }
        },
        "aws": {
            "instances": {
                "default": {
            "enabled": False,
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "region": "",
            "ami": "",
                    "display_name": "AWS",
            "secrets": {"access_key_id": "", "secret_access_key": ""},
            "spot": False,
                }
            }
        },
        "gcp": {
            "instances": {
                "default": {
            "enabled": False,
            "project": "",
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "zone": "",
            "image_project": "",
            "image_family": "",
                    "display_name": "GCP",
            "secrets": {"service_account_key": ""},
                }
            }
        },
        "hetzner": {
            "instances": {
                "default": {
            "enabled": False,
            "ips": [],
            "scaling": {"min_scaling": 0, "max_scaling": 0},
            "size": "",
            "location": "",
            "datacenter": "",
                    "display_name": "Hetzner",
            "secrets": {"access_token": ""},
                }
            }
        },
        "azure": {
            "instances": {
                "default": {
                    "enabled": False,
                    "ips": [],
                    "scaling": {"min_scaling": 0, "max_scaling": 0},
                    "size": "",
                    "location": "",
                    "display_name": "Azure",
                    "secrets": {
                        "subscription_id": "",
                        "client_id": "",
                        "client_secret": "",
                        "tenant_id": "",
                        "resource_group": ""
                    },
                }
            }
        },
        "scaleway": {
            "instances": {
                "default": {
                    "enabled": False,
                    "ips": [],
                    "scaling": {"min_scaling": 0, "max_scaling": 0},
                    "size": "",
                    "region": "",
                    "image": "",
                    "organization": "",
                    "display_name": "Scaleway",
                    "secrets": {
                        "auth_token": ""
                    },
                }
            }
        },
    },
}

delete_queue = set()
restart_queue = set()

load_dotenv()

# Set proxy authentication
config["auth"]["username"] = os.environ.get("PROXY_USERNAME", "changeme")
config["auth"]["password"] = os.environ.get("PROXY_PASSWORD", "changeme")
config["age_limit"] = int(os.environ.get('AGE_LIMIT', 0))
config["no_auth"] = config["auth"]["username"] == "changeme" and config["auth"]["password"] == "changeme"
config["only_host_ip"] = os.environ.get("ONLY_HOST_IP", False)

# Set DigitalOcean config - original format for backward compatibility
config["providers"]["digitalocean"]["instances"]["default"]["enabled"] = os.environ.get(
    "DIGITALOCEAN_ENABLED", "False"
) == "True"
config["providers"]["digitalocean"]["instances"]["default"]["secrets"]["access_token"] = os.environ.get(
    "DIGITALOCEAN_ACCESS_TOKEN"
)
config["providers"]["digitalocean"]["instances"]["default"]["scaling"]["min_scaling"] = int(
    os.environ.get("DIGITALOCEAN_MIN_SCALING", 2)
)
config["providers"]["digitalocean"]["instances"]["default"]["scaling"]["max_scaling"] = int(
    os.environ.get("DIGITALOCEAN_MAX_SCALING", 2)
)
config["providers"]["digitalocean"]["instances"]["default"]["size"] = os.environ.get(
    "DIGITALOCEAN_SIZE", "s-1vcpu-1gb"
)
config["providers"]["digitalocean"]["instances"]["default"]["region"] = os.environ.get(
    "DIGITALOCEAN_REGION", "lon1"
)
config["providers"]["digitalocean"]["instances"]["default"]["display_name"] = os.environ.get(
    "DIGITALOCEAN_DISPLAY_NAME", "DigitalOcean"
)

# Set AWS Config - original format for backward compatibility
config["providers"]["aws"]["instances"]["default"]["enabled"] = os.environ.get("AWS_ENABLED", "False") == "True"
config["providers"]["aws"]["instances"]["default"]["secrets"]["access_key_id"] = os.environ.get(
    "AWS_ACCESS_KEY_ID"
)
config["providers"]["aws"]["instances"]["default"]["secrets"]["secret_access_key"] = os.environ.get(
    "AWS_SECRET_ACCESS_KEY"
)
config["providers"]["aws"]["instances"]["default"]["scaling"]["min_scaling"] = int(
    os.environ.get("AWS_MIN_SCALING", 2)
)
config["providers"]["aws"]["instances"]["default"]["scaling"]["max_scaling"] = int(
    os.environ.get("AWS_MAX_SCALING", 2)
)
config["providers"]["aws"]["instances"]["default"]["size"] = os.environ.get("AWS_SIZE", "t2.micro")
config["providers"]["aws"]["instances"]["default"]["region"] = os.environ.get("AWS_REGION", "eu-west-2")
config["providers"]["aws"]["instances"]["default"]["spot"] = os.environ.get("AWS_SPOT", "False") == "True"
config["providers"]["aws"]["instances"]["default"]["ami"] = os.environ.get("AWS_AMI", "ami-096cb92bb3580c759")
config["providers"]["aws"]["instances"]["default"]["display_name"] = os.environ.get("AWS_DISPLAY_NAME", "AWS")

# Set GCP Config - original format for backward compatibility
config["providers"]["gcp"]["instances"]["default"]["enabled"] = os.environ.get("GCP_ENABLED", "False") == "True"
config["providers"]["gcp"]["instances"]["default"]["project"] = os.environ.get("GCP_PROJECT")
config["providers"]["gcp"]["instances"]["default"]["secrets"]["service_account_key"] = os.environ.get(
    "GCP_SERVICE_ACCOUNT_KEY"
)
config["providers"]["gcp"]["instances"]["default"]["scaling"]["min_scaling"] = int(
    os.environ.get("GCP_MIN_SCALING", 2)
)
config["providers"]["gcp"]["instances"]["default"]["scaling"]["max_scaling"] = int(
    os.environ.get("GCP_MAX_SCALING", 2)
)
config["providers"]["gcp"]["instances"]["default"]["size"] = os.environ.get("GCP_SIZE", "f1-micro")
config["providers"]["gcp"]["instances"]["default"]["zone"] = os.environ.get("GCP_REGION", "us-central1-a")
config["providers"]["gcp"]["instances"]["default"]["image_project"] = os.environ.get("GCP_IMAGE_PROJECT", "ubuntu-os-cloud")
config["providers"]["gcp"]["instances"]["default"]["image_family"] = os.environ.get("GCP_IMAGE_FAMILY", "ubuntu-minimal-2004-lts")
config["providers"]["gcp"]["instances"]["default"]["display_name"] = os.environ.get("GCP_DISPLAY_NAME", "GCP")

# Set Hetzner config - original format for backward compatibility
config["providers"]["hetzner"]["instances"]["default"]["enabled"] = os.environ.get(
    "HETZNER_ENABLED", "False"
) == "True"
config["providers"]["hetzner"]["instances"]["default"]["secrets"]["access_token"] = os.environ.get(
    "HETZNER_ACCESS_TOKEN"
)
config["providers"]["hetzner"]["instances"]["default"]["scaling"]["min_scaling"] = int(
    os.environ.get("HETZNER_MIN_SCALING", 2)
)
config["providers"]["hetzner"]["instances"]["default"]["scaling"]["max_scaling"] = int(
    os.environ.get("HETZNER_MAX_SCALING", 2)
)
config["providers"]["hetzner"]["instances"]["default"]["size"] = os.environ.get(
    "HETZNER_SIZE", "cx21"
)
config["providers"]["hetzner"]["instances"]["default"]["location"] = os.environ.get(
    "HETZNER_LOCATION", "nbg1"
)
config["providers"]["hetzner"]["instances"]["default"]["display_name"] = os.environ.get(
    "HETZNER_DISPLAY_NAME", "Hetzner"
)

# Set Azure config - original format for backward compatibility
config["providers"]["azure"]["instances"]["default"]["enabled"] = os.environ.get(
    "AZURE_ENABLED", "False"
) == "True"
config["providers"]["azure"]["instances"]["default"]["secrets"]["subscription_id"] = os.environ.get(
    "AZURE_SUBSCRIPTION_ID"
)
config["providers"]["azure"]["instances"]["default"]["secrets"]["client_id"] = os.environ.get(
    "AZURE_CLIENT_ID"
)
config["providers"]["azure"]["instances"]["default"]["secrets"]["client_secret"] = os.environ.get(
    "AZURE_CLIENT_SECRET"
)
config["providers"]["azure"]["instances"]["default"]["secrets"]["tenant_id"] = os.environ.get(
    "AZURE_TENANT_ID"
)
config["providers"]["azure"]["instances"]["default"]["secrets"]["resource_group"] = os.environ.get(
    "AZURE_RESOURCE_GROUP", "cloudproxy-rg"
)
config["providers"]["azure"]["instances"]["default"]["scaling"]["min_scaling"] = int(
    os.environ.get("AZURE_MIN_SCALING", 2)
)
config["providers"]["azure"]["instances"]["default"]["scaling"]["max_scaling"] = int(
    os.environ.get("AZURE_MAX_SCALING", 2)
)
config["providers"]["azure"]["instances"]["default"]["size"] = os.environ.get(
    "AZURE_SIZE", "Standard_B1s"
)
config["providers"]["azure"]["instances"]["default"]["location"] = os.environ.get(
    "AZURE_LOCATION", "eastus"
)
config["providers"]["azure"]["instances"]["default"]["display_name"] = os.environ.get(
    "AZURE_DISPLAY_NAME", "Azure"
)

# Set Scaleway config
config["providers"]["scaleway"]["instances"]["default"]["enabled"] = os.environ.get(
    "SCALEWAY_ENABLED", "False"
) == "True"
config["providers"]["scaleway"]["instances"]["default"]["secrets"]["auth_token"] = os.environ.get(
    "SCALEWAY_AUTH_TOKEN"
)
config["providers"]["scaleway"]["instances"]["default"]["scaling"]["min_scaling"] = int(
    os.environ.get("SCALEWAY_MIN_SCALING", 2)
)
config["providers"]["scaleway"]["instances"]["default"]["scaling"]["max_scaling"] = int(
    os.environ.get("SCALEWAY_MAX_SCALING", 2)
)
config["providers"]["scaleway"]["instances"]["default"]["size"] = os.environ.get(
    "SCALEWAY_SIZE", "DEV1-S"
)
config["providers"]["scaleway"]["instances"]["default"]["region"] = os.environ.get(
    "SCALEWAY_REGION", "fr-par-1"
)
config["providers"]["scaleway"]["instances"]["default"]["image"] = os.environ.get(
    "SCALEWAY_IMAGE", "ubuntu_focal"
)
config["providers"]["scaleway"]["instances"]["default"]["organization"] = os.environ.get(
    "SCALEWAY_ORGANIZATION"
)
config["providers"]["scaleway"]["instances"]["default"]["display_name"] = os.environ.get(
    "SCALEWAY_DISPLAY_NAME", "Scaleway"
)

# Check for additional provider instances using the new format pattern
for provider_key in config["providers"].keys():
    provider_upper = provider_key.upper()
    
    # Find all environment variables matching the pattern {PROVIDER}_INSTANCE_{NAME}_ENABLED
    instance_vars = {key: value for key, value in os.environ.items() 
                    if key.startswith(f"{provider_upper}_INSTANCE_") and key.endswith("_ENABLED")}
    
    for instance_var, enabled_value in instance_vars.items():
        # Extract instance name from the environment variable key
        # Format: {PROVIDER}_INSTANCE_{NAME}_ENABLED
        instance_name = instance_var[len(f"{provider_upper}_INSTANCE_"):-8].lower()
        
        if enabled_value == "True":
            # Create a new instance configuration
            if instance_name not in config["providers"][provider_key]["instances"]:
                # Clone the default instance configuration as a starting point
                config["providers"][provider_key]["instances"][instance_name] = {
                    "enabled": True,
                    "ips": [],
                    "scaling": {"min_scaling": 0, "max_scaling": 0},
                    "size": "",
                    "display_name": f"{provider_key.capitalize()} {instance_name}",
                    "secrets": {},
                }
                
                # Copy relevant fields from default instance
                default_instance = config["providers"][provider_key]["instances"]["default"]
                for field in ["region", "zone", "location", "ami", "spot", "datacenter", 
                             "image_project", "image_family", "project"]:
                    if field in default_instance:
                        config["providers"][provider_key]["instances"][instance_name][field] = default_instance[field]
                
                # Copy secrets structure (but not values)
                for secret_key in default_instance["secrets"].keys():
                    config["providers"][provider_key]["instances"][instance_name]["secrets"][secret_key] = None
            
            # Set instance-specific values from environment variables
            instance_prefix = f"{provider_upper}_INSTANCE_{instance_name.upper()}_"
            
            # Process all environment variables for this instance
            for env_key, env_value in os.environ.items():
                if env_key.startswith(instance_prefix):
                    # Extract the setting name
                    setting_name = env_key[len(instance_prefix):].lower()
                    
                    if setting_name == "min_scaling":
                        config["providers"][provider_key]["instances"][instance_name]["scaling"]["min_scaling"] = int(env_value)
                    elif setting_name == "max_scaling":
                        config["providers"][provider_key]["instances"][instance_name]["scaling"]["max_scaling"] = int(env_value)
                    elif setting_name == "display_name":
                        config["providers"][provider_key]["instances"][instance_name]["display_name"] = env_value
                    elif setting_name in ["size", "region", "zone", "location", "ami", "project", 
                                          "image_project", "image_family", "datacenter"]:
                        config["providers"][provider_key]["instances"][instance_name][setting_name] = env_value
                    elif setting_name == "spot":
                        config["providers"][provider_key]["instances"][instance_name]["spot"] = env_value == "True"
                    elif setting_name in default_instance["secrets"]:
                        # Handle secret values
                        config["providers"][provider_key]["instances"][instance_name]["secrets"][setting_name] = env_value

# For backward compatibility - maintain top-level properties for the default instance
for provider_key in config["providers"].keys():
    default_instance = config["providers"][provider_key]["instances"]["default"]
    for key, value in default_instance.items():
        if key != "secrets":  # Don't include secrets in top-level
            config["providers"][provider_key][key] = value
