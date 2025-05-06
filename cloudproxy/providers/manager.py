from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from cloudproxy.providers import settings
from cloudproxy.providers.aws.main import aws_start
from cloudproxy.providers.gcp.main import gcp_start
from cloudproxy.providers.digitalocean.main import do_start
from cloudproxy.providers.hetzner.main import hetzner_start


def do_manager(instance_name="default"):
    """
    DigitalOcean manager function for a specific instance.
    """
    # Fetch instance_config for non-secret settings
    instance_config = settings.config["providers"]["digitalocean"]["instances"].get(instance_name)
    
    # do_start will now handle fetching credentials via credential_manager
    ip_list = do_start(instance_config, instance_id=instance_name)
    
    # Update IPs in settings.config (only if instance_config exists)
    if instance_config:
        settings.config["providers"]["digitalocean"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    
    return ip_list


def aws_manager(instance_name="default"):
    """
    AWS manager function for a specific instance.
    """
    # Fetch instance_config for non-secret settings
    instance_config = settings.config["providers"]["aws"]["instances"].get(instance_name)
    
    # aws_start will now handle fetching credentials via credential_manager
    ip_list = aws_start(instance_config, instance_id=instance_name)
    
    # Update IPs in settings.config (only if instance_config exists)
    if instance_config:
        settings.config["providers"]["aws"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    
    return ip_list


def gcp_manager(instance_name="default"):
    """
    GCP manager function for a specific instance.
    """
    # Fetch instance_config for non-secret settings
    instance_config = settings.config["providers"]["gcp"]["instances"].get(instance_name)
    
    # gcp_start will now handle fetching credentials via credential_manager
    ip_list = gcp_start(instance_config, instance_id=instance_name)
    
    # Update IPs in settings.config (only if instance_config exists)
    if instance_config:
        settings.config["providers"]["gcp"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    
    return ip_list


def hetzner_manager(instance_name="default"):
    """
    Hetzner manager function for a specific instance.
    """
    # Fetch instance_config for non-secret settings
    instance_config = settings.config["providers"]["hetzner"]["instances"].get(instance_name)
    
    # hetzner_start will now handle fetching credentials via credential_manager
    ip_list = hetzner_start(instance_config, instance_id=instance_name)
    
    # Update IPs in settings.config (only if instance_config exists)
    if instance_config:
        settings.config["providers"]["hetzner"]["instances"][instance_name]["ips"] = [ip for ip in ip_list]
    
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
