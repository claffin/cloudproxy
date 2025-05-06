import datetime
import itertools

from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.gcp.functions import (
    list_instances,
    create_proxy,
    delete_proxy,
    stop_proxy,
    start_proxy,
)
from cloudproxy.providers.settings import delete_queue, restart_queue, config

def gcp_deployment(min_scaling, instance_config=None, instance_id="default"):
    """
    Deploy GCP instances based on min_scaling requirements for a specific instance.
    
    Args:
        min_scaling: The minimum number of instances to maintain
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for GCP instance '{instance_id}'. Skipping deployment.")
        return 0

    total_instances = len(list_instances(instance_id=instance_id))
    display_name = instance_config.get("display_name", instance_id)

    if min_scaling < total_instances:
        logger.info(f"Overprovisioned: GCP {display_name} destroying.....")
        for instance in itertools.islice(
            list_instances(instance_id=instance_id), 0, (total_instances - min_scaling)
        ):
            access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
            msg = f"{instance['name']} {access_configs.get('natIP', '')}"
            delete_proxy(instance['name'], instance_id=instance_id)
            logger.info(f"Destroyed: GCP {display_name} -> " + msg)
    if min_scaling - total_instances < 1:
        logger.info(f"Minimum GCP {display_name} instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info(f"Deploying: {str(total_deploy)} GCP {display_name} instances")
        for _ in range(total_deploy):
            create_proxy(instance_config, instance_id=instance_id)
            logger.info(f"Deployed GCP {display_name} instance")
    return len(list_instances(instance_id=instance_id))

def gcp_check_alive(instance_config=None, instance_id="default"):
    """
    Check if GCP instances are alive and operational for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
        
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for GCP instance '{instance_id}'. Skipping check alive.")
        return []

    display_name = instance_config.get("display_name", instance_id)
    ip_ready = []
    for instance in list_instances(instance_id=instance_id):
        try:
            created_at_str = instance.get("creationTimestamp")
            if not created_at_str:
                 logger.info(f"Pending: GCP {display_name} allocating (no timestamp)")
                 continue

            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.datetime.strptime(created_at_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs.get('natIP', '')}"
                delete_proxy(instance['name'], instance_id=instance_id)
                logger.info(f"Recycling instance, reached age limit GCP {display_name} -> " + msg)
            
            elif instance['status'] == "TERMINATED":
                logger.info(f"Waking up: GCP {display_name} -> Instance " + instance['name'])
                started = start_proxy(instance['name'], instance_id=instance_id)
                if not started:
                    logger.info("Could not wake up, trying again later.")
            
            elif instance['status'] == "STOPPING":
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs.get('natIP', '')}"
                logger.info(f"Stopping: GCP {display_name} -> " + msg)
            
            elif instance['status'] == "PROVISIONING" or instance['status'] == "STAGING":
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs.get('natIP', '')}"
                logger.info(f"Provisioning: GCP {display_name} -> " + msg)
            
            # If none of the above, check if alive or not.
            elif 'natIP' in instance['networkInterfaces'][0]['accessConfigs'][0] and check_alive(instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']):
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP']}"
                logger.info(f"Alive: GCP {display_name} -> " + msg)
                ip_ready.append(access_configs['natIP'])
            
            else:
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs.get('natIP', '')}"
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(instance['name'], instance_id=instance_id)
                    logger.info(f"Destroyed: took too long GCP {display_name} -> " + msg)
                else:
                    logger.info(f"Waiting: GCP {display_name} -> " + msg)
        except (TypeError, KeyError) as e:
            logger.info(f"Pending: GCP {display_name} -> allocating ip (Error: {e})")
    return ip_ready

def gcp_check_delete(instance_config=None, instance_id="default"):
    """
    Check if any GCP instances need to be deleted for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for GCP instance '{instance_id}'. Skipping check delete.")
        return

    display_name = instance_config.get("display_name", instance_id)

    for instance in list_instances(instance_id=instance_id):
        access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
        if 'natIP' in  access_configs and access_configs['natIP'] in delete_queue:
            msg = f"{instance['name']}, {access_configs['natIP']}"
            delete_proxy(instance['name'], instance_id=instance_id)
            logger.info(f"Destroyed: not wanted GCP {display_name} -> " + msg)
            delete_queue.remove(access_configs['natIP'])

def gcp_check_stop(instance_config=None, instance_id="default"):
    """
    Check if any GCP instances need to be stopped for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for GCP instance '{instance_id}'. Skipping check stop.")
        return

    display_name = instance_config.get("display_name", instance_id)

    for instance in list_instances(instance_id=instance_id):
        access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
        if 'natIP' in  access_configs and access_configs['natIP'] in restart_queue:
            msg = f"{instance['name']}, {access_configs['natIP']}"
            stop_proxy(instance['name'], instance_id=instance_id)
            logger.info(f"Stopped: getting new IP GCP {display_name} -> " + msg)
            restart_queue.remove(access_configs['natIP'])

def gcp_start(instance_config=None, instance_id="default"):
    """
    Start the GCP provider lifecycle for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for GCP instance '{instance_id}'. Skipping startup.")
        return []

    gcp_check_delete(instance_config, instance_id=instance_id)
    gcp_check_stop(instance_config, instance_id=instance_id)
    gcp_deployment(instance_config["scaling"]["min_scaling"], instance_config, instance_id=instance_id)
    ip_ready = gcp_check_alive(instance_config, instance_id=instance_id)
    return ip_ready
