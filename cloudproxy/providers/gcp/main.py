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

def gcp_deployment(min_scaling):
    total_instances = len(list_instances())
    if min_scaling < total_instances:
        logger.info("Overprovisioned: GCP destroying.....")
        for instance in itertools.islice(
            list_instances(), 0, (total_instances - min_scaling)
        ):
            access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
            msg = f"{instance['name']} {access_configs['natIP']}"
            delete_proxy(instance['name'])
            logger.info("Destroyed: GCP -> " + msg)
    if min_scaling - total_instances < 1:
        logger.info("Minimum GCP instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info("Deploying: " + str(total_deploy) + " GCP instances")
        for _ in range(total_deploy):
            create_proxy()
            logger.info("Deployed")
    return len(list_instances())

def gcp_check_alive():
    ip_ready = []
    for instance in list_instances():
        try:
            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.datetime.strptime(instance["creationTimestamp"], '%Y-%m-%dT%H:%M:%S.%f%z')
            
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP'] if 'natIP' in access_configs else ''}"
                delete_proxy(instance['name'])
                logger.info("Recycling instance, reached age limit -> " + msg)
            
            elif instance['status'] == "TERMINATED":
                logger.info("Waking up: GCP -> Instance " + instance['name'])
                started = start_proxy(instance['name'])
                if not started:
                    logger.info("Could not wake up, trying again later.")
            
            elif instance['status'] == "STOPPING":
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP'] if 'natIP' in access_configs else ''}"
                logger.info("Stopping: GCP -> " + msg)
            
            elif instance['status'] == "PROVISIONING" or instance['status'] == "STAGING":
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP'] if 'natIP' in access_configs else ''}"
                logger.info("Provisioning: GCP -> " + msg)
            
            # If none of the above, check if alive or not.
            elif check_alive(instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']):
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP']}"
                logger.info("Alive: GCP -> " + msg)
                ip_ready.append(access_configs['natIP'])
            
            else:
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP']}"
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(instance['name'])
                    logger.info("Destroyed: took too long GCP -> " + msg)
                else:
                    logger.info("Waiting: GCP -> " + msg)
        except (TypeError, KeyError):
            logger.info("Pending: GCP -> Allocating IP")
    return ip_ready

def gcp_check_delete():
    for instance in list_instances():
        access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
        if 'natIP' in  access_configs and access_configs['natIP'] in delete_queue: 
            msg = f"{instance['name']}, {access_configs['natIP']}"
            delete_proxy(instance['name'])
            logger.info("Destroyed: not wanted -> " + msg)
            delete_queue.remove(access_configs['natIP'])

def gcp_check_stop():
    for instance in list_instances():
        access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
        if 'natIP' in  access_configs and access_configs['natIP'] in restart_queue:
            msg = f"{instance['name']}, {access_configs['natIP']}"
            stop_proxy(instance['name'])
            logger.info("Stopped: getting new IP -> " + msg)
            restart_queue.remove(access_configs['natIP'])

def gcp_start():
    gcp_check_delete()
    gcp_check_stop()
    gcp_deployment(config["providers"]["gcp"]["scaling"]["min_scaling"])
    ip_ready = gcp_check_alive()
    return ip_ready