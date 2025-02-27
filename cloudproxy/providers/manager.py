import asyncio
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from cloudproxy.providers import settings
from cloudproxy.providers.aws.main import aws_start
from cloudproxy.providers.gcp.main import gcp_start
from cloudproxy.providers.digitalocean.main import do_start
from cloudproxy.providers.hetzner.main import hetzner_start
from cloudproxy.providers.azure.main import azure_start, azure_manager
from cloudproxy.providers.models import IpInfo


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


def run_async_safely(coro):
    """
    Helper function to run a coroutine from a background thread safely.
    Creates a new event loop if needed and runs the coroutine to completion.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    try:
        # Try to get the current event loop, or create a new one if there isn't one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the coroutine and return its result
        if loop.is_running():
            # If the loop is already running (unlikely in this context),
            # create a future and run the coroutine as a task
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result()
        else:
            # Otherwise, just run the coroutine directly
            return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async task: {e}")
        # Return None on error
        return None


def async_manager_wrapper(manager_func, instance_name):
    """
    Wrapper function for async provider managers.
    
    Args:
        manager_func: The async manager function to call
        instance_name: The instance name to pass to the manager
        
    Returns:
        The result of the manager function
    """
    return run_async_safely(manager_func(instance_name))


def init_schedule(scheduler=None):
    """Initialize the scheduler for provider management."""
    if scheduler is None:
        scheduler = BackgroundScheduler()
    scheduler.start()
    
    # Define provider manager mapping
    provider_managers = {
        "digitalocean": do_manager,
        "aws": aws_manager,
        "gcp": gcp_manager,
        "hetzner": hetzner_manager,
        "azure": azure_manager,
    }
    
    # Schedule jobs for all provider instances
    for provider_name, provider_config in settings.config["providers"].items():
        # Skip providers not in our manager mapping
        if provider_name not in provider_managers:
            continue
            
        for instance_name, instance_config in provider_config["instances"].items():
            if instance_config.get("enabled", False):
                manager_func = provider_managers.get(provider_name)
                if manager_func:
                    logger.info(f"Scheduling {provider_name} provider for instance {instance_name}")
                    
                    # Get the poll interval for this instance
                    poll_interval = instance_config.get("poll_interval", 60)
                    
                    # Determine if the manager is async or sync
                    is_async_manager = asyncio.iscoroutinefunction(manager_func)
                    
                    if is_async_manager:
                        # For async managers, use the wrapper function
                        scheduler.add_job(
                            async_manager_wrapper,
                            'interval',
                            seconds=poll_interval,
                            args=[manager_func, instance_name],
                            id=f"{provider_name}-{instance_name}",
                            replace_existing=True,
                            next_run_time=datetime.datetime.now()
                        )
                    else:
                        # For sync managers, call directly
                        scheduler.add_job(
                            manager_func,
                            'interval',
                            seconds=poll_interval,
                            args=[instance_name],
                            id=f"{provider_name}-{instance_name}",
                            replace_existing=True,
                            next_run_time=datetime.datetime.now()
                        )
                    
                    logger.info(f"{provider_name.capitalize()} {instance_name} enabled")
            else:
                logger.info(f"{provider_name.capitalize()} {instance_name} not enabled")
