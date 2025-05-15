import json
import uuid

from loguru import logger

import googleapiclient.discovery
from google.oauth2 import service_account

from cloudproxy.providers.config import set_auth
from cloudproxy.providers.settings import config

gcp = None
compute = None

def get_client(instance_config=None):
    """
    Initialize and return a GCP client based on the provided configuration.
    
    Args:
        instance_config: The specific instance configuration
    
    Returns:
        tuple: (config, gcp_client)
    """

    global gcp, compute
    if gcp is not None and compute is not None:
        return gcp, compute

    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    gcp = config["providers"]["gcp"]
    try:
        if 'sa_json' in instance_config["secrets"]:
            credentials = service_account.Credentials.from_service_account_file(
                instance_config["secrets"]["sa_json"]
            )
        else:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(instance_config["secrets"]["service_account_key"])
            )
        compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

        return gcp, compute
    except TypeError:
        logger.error("GCP -> Invalid service account key")


def create_proxy(instance_config=None):
    """
    Create a GCP proxy instance.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    gcp, compute = get_client(instance_config)

    image_response = compute.images().getFromFamily(
        project=instance_config["image_project"], 
        family=instance_config["image_family"]
    ).execute()
    source_disk_image = image_response['selfLink']

    body = {
        'name': 'cloudproxy-' + str(uuid.uuid4()),
        'machineType': 
            f"zones/{instance_config['zone']}/machineTypes/{instance_config['size']}",
        'tags': {
            'items': [
                'cloudproxy'
            ]
        },
        "labels": {
            'cloudproxy': 'cloudproxy'
        },
        'disks': [
            {
                'boot': True,
                'autoDelete': True,
                'initializeParams': {
                    'sourceImage': source_disk_image,
                }
            }
        ],
        'networkInterfaces': [{
            'network': 'global/networks/default',
            'accessConfigs': [
                {
                    'name': 'External NAT', 
                    'type': 'ONE_TO_ONE_NAT',
                    'networkTier': 'STANDARD'
                }
            ]
        }],
        'metadata': {
            'items': [{
                'key': 'startup-script',
                'value': set_auth(config["auth"]["username"], config["auth"]["password"])
            }]
        }
    }

    return compute.instances().insert(
        project=instance_config["project"],
        zone=instance_config["zone"],
        body=body
    ).execute()

def delete_proxy(name, instance_config=None):
    """
    Delete a GCP proxy instance.
    
    Args:
        name: Name of the instance to delete
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    gcp, compute = get_client(instance_config)

    try:
        return compute.instances().delete(
            project=instance_config["project"],
            zone=instance_config["zone"],
            instance=name
        ).execute()
    except googleapiclient.errors.HttpError:
        logger.info(f"GCP --> HTTP Error when trying to delete proxy {name}. Probably has already been deleted.")
        return None

def stop_proxy(name, instance_config=None):
    """
    Stop a GCP proxy instance.
    
    Args:
        name: Name of the instance to stop
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    try:
        return compute.instances().stop(
            project=instance_config["project"],
            zone=instance_config["zone"],
            instance=name
        ).execute()
    except googleapiclient.errors.HttpError:
        logger.info(f"GCP --> HTTP Error when trying to stop proxy {name}. Probably has already been deleted.")
        return None

def start_proxy(name, instance_config=None):
    """
    Start a GCP proxy instance.
    
    Args:
        name: Name of the instance to start
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    gcp, compute = get_client(instance_config)

    try:
        return compute.instances().start(
            project=instance_config["project"],
            zone=instance_config["zone"],
            instance=name
        ).execute()
    except googleapiclient.errors.HttpError:
        logger.info(f"GCP --> HTTP Error when trying to start proxy {name}. Probably has already been deleted.")
        return None

def list_instances(instance_config=None):
    """
    List all GCP proxy instances.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    gcp, compute = get_client(instance_config)

    result = compute.instances().list(
        project=instance_config["project"], 
        zone=instance_config["zone"], 
        filter='labels.cloudproxy eq cloudproxy'
    ).execute()
    return result['items'] if 'items' in result else []
