from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from cloudproxy.providers import settings
from cloudproxy.providers.aws.main import aws_start
from cloudproxy.providers.gcp.main import gcp_start
from cloudproxy.providers.digitalocean.main import do_start
from cloudproxy.providers.hetzner.main import hetzner_start
from cloudproxy.providers.scaleway.main import scaleway_start


def do_manager(instance_name="default"):
    """
    DigitalOcean manager function for a specific instance.
    """
    instance_config = settings.config["providers"]["digitalocean"]["instances"][instance_name]
    ip_list = do_start(instance_config)
    settings.config["providers"]["digitalocean"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    return ip_list


def aws_manager(instance_name="default"):
    """
    AWS manager function for a specific instance.
    """
    instance_config = settings.config["providers"]["aws"]["instances"][instance_name]
    ip_list = aws_start(instance_config)
    settings.config["providers"]["aws"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    return ip_list


def gcp_manager(instance_name="default"):
    """
    GCP manager function for a specific instance.
    """
    instance_config = settings.config["providers"]["gcp"]["instances"][instance_name]
    ip_list = gcp_start(instance_config)
    settings.config["providers"]["gcp"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    return ip_list


def hetzner_manager(instance_name="default"):
    """
    Hetzner manager function for a specific instance.
    """
    instance_config = settings.config["providers"]["hetzner"]["instances"][instance_name]
    ip_list = hetzner_start(instance_config)
    settings.config["providers"]["hetzner"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    return ip_list


def scaleway_manager(instance_name="default"):
    """
    Scaleway manager function for a specific instance.
    """
    instance_config = settings.config["providers"]["scaleway"]["instances"][instance_name]
    ip_list = scaleway_start(instance_config)
    settings.config["providers"]["scaleway"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    return ip_list


def init_schedule():
    sched = BackgroundScheduler()
    sched.start()
    
    # Define provider manager mapping
    provider_managers = {
        "digitalocean": do_manager,
        "aws": aws_manager,
        "gcp": gcp_manager,
        "hetzner": hetzner_manager,
        "scaleway": scaleway_manager,
    }
    
    # Schedule jobs for all provider instances
    for provider_name, provider_config in settings.config["providers"].items():
        # Skip providers not in our manager mapping
        if provider_name not in provider_managers:
            continue
            
        for instance_name, instance_config in provider_config["instances"].items():
            if instance_config["enabled"]:
                manager_func = provider_managers.get(provider_name)
                if manager_func:
                    # Create a function that preserves the original name
                    def scheduled_func(func=manager_func, instance=instance_name):
                        return func(instance)
                    
                    # Preserve the original function name for testing
                    scheduled_func.__name__ = manager_func.__name__
                    
                    sched.add_job(scheduled_func, "interval", seconds=20)
                    logger.info(f"{provider_name.capitalize()} {instance_name} enabled")
            else:
                logger.info(f"{provider_name.capitalize()} {instance_name} not enabled")
