import json
import uuid

from loguru import logger

import googleapiclient.discovery
from google.oauth2 import service_account

from cloudproxy.providers.config import set_auth
from cloudproxy.providers.settings import config
from cloudproxy.credentials import credential_manager

# Module-level variables for clients (kept for potential future use or specific test setups, but not used by get_compute_client for caching)
# compute = None

def reset_clients():
    """
    Reset any module-level state if necessary (e.g., for testing).
    For the current get_compute_client implementation, this function does nothing.
    """
    # global compute # If we were caching compute here per instance_id
    # compute = {}
    pass

def get_compute_client(instance_id: str):
    """
    Initialize and return GCP compute client based on credentials from CredentialManager.
    Always creates a new client for the specific instance ID.
    
    Args:
        instance_id: The ID of the instance configuration
        
    Returns:
        googleapiclient.discovery.Resource: Compute client instance, or None if credentials not found or invalid
    """
    # Do NOT use module-level global variables for caching clients here.
    # Each call gets a client specific to the instance_id.

    if credential_manager is None:
        logger.error("CredentialManager not initialized in gcp.functions.get_compute_client")
        return None

    secrets = credential_manager.get_credentials("gcp", instance_id)

    if not secrets or "service_account_key" not in secrets:
        # logger.debug(f"No GCP credentials or service_account_key found for instance '{instance_id}'.")
        return None

    try:
        # Always create a new client for this specific call
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(secrets["service_account_key"])
        )
        local_compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
        return local_compute
    except TypeError: # Specifically for json.loads if service_account_key is not a valid JSON string
        logger.error(f"GCP -> Invalid service account key format (not valid JSON) for instance '{instance_id}'")
        return None
    except ValueError as ve: # Specifically for from_service_account_info if JSON is valid but content is not
        logger.error(f"GCP -> Invalid service account key content for instance '{instance_id}': {ve}")
        return None
    except Exception as e:
        logger.error(f"Error initializing GCP client for instance '{instance_id}': {e}")
        return None


def create_proxy(instance_config=None, instance_id="default"):
    """
    Create a GCP proxy instance.

    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    compute_client = get_compute_client(instance_id)

    if compute_client is None:
        logger.warning(f"No GCP credentials found for instance '{instance_id}'. Cannot create proxy.")
        return None

    image_response = compute_client.images().getFromFamily(
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

    return compute_client.instances().insert(
        project=instance_config["project"],
        zone=instance_config["zone"],
        body=body
    ).execute()

def delete_proxy(name, instance_config=None, instance_id="default"):
    """
    Delete a GCP proxy instance.
    
    Args:
        name: Name of the instance to delete
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    compute_client = get_compute_client(instance_id)

    if compute_client is None:
        logger.warning(f"No GCP credentials found for instance '{instance_id}'. Cannot delete proxy.")
        return None

    try:
        return compute_client.instances().delete(
            project=instance_config["project"],
            zone=instance_config["zone"],
            instance=name
        ).execute()
    except googleapiclient.errors.HttpError:
        logger.info(f"GCP --> HTTP Error when trying to delete proxy {name} for instance '{instance_id}'. Probably has already been deleted.")
        return None


def stop_proxy(name, instance_config=None, instance_id="default"):
    """
    Stop a GCP proxy instance.
    
    Args:
        name: Name of the instance to stop
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    compute_client = get_compute_client(instance_id)

    if compute_client is None:
        logger.warning(f"No GCP credentials found for instance '{instance_id}'. Cannot stop proxy.")
        return None

    try:
        return compute_client.instances().stop(
            project=instance_config["project"],
            zone=instance_config["zone"],
            instance=name
        ).execute()
    except googleapiclient.errors.HttpError:
        logger.info(f"GCP --> HTTP Error when trying to stop proxy {name} for instance '{instance_id}'. Probably has already been deleted.")
        return None


def start_proxy(name, instance_config=None, instance_id="default"):
    """
    Start a GCP proxy instance.
    
    Args:
        name: Name of the instance to start
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    compute_client = get_compute_client(instance_id)

    if compute_client is None:
        logger.warning(f"No GCP credentials found for instance '{instance_id}'. Cannot start proxy.")
        return None

    try:
        return compute_client.instances().start(
            project=instance_config["project"],
            zone=instance_config["zone"],
            instance=name
        ).execute()
    except googleapiclient.errors.HttpError:
        logger.info(f"GCP --> HTTP Error when trying to start proxy {name} for instance '{instance_id}'. Probably has already been deleted.")
        return None


def list_instances(instance_config=None, instance_id="default"):
    """
    List GCP proxy instances for a specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
        
    Returns:
        list: List of instances
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    compute_client = get_compute_client(instance_id)

    if compute_client is None:
        logger.warning(f"No GCP credentials found for instance '{instance_id}'. Cannot list instances.")
        return []

    result = compute_client.instances().list(
        project=instance_config["project"],
        zone=instance_config["zone"],
        filter='labels.cloudproxy eq cloudproxy'
    ).execute()
    return result['items'] if 'items' in result else []
def start_proxy(name, instance_config=None, instance_id="default"):
    """
    Start a GCP proxy instance.

    Args:
        name: Name of the instance to start
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    compute_client = get_compute_client(instance_id)

    if compute_client is None:
        logger.warning(f"No GCP credentials found for instance '{instance_id}'. Cannot start proxy.")
        return None

    try:
        return compute_client.instances().start(
            project=instance_config["project"],
            zone=instance_config["zone"],
            instance=name
        ).execute()
    except googleapiclient.errors.HttpError:
        logger.info(f"GCP --> HTTP Error when trying to start proxy {name} for instance '{instance_id}'. Probably has already been deleted.")
        return None


def list_instances(instance_config=None, instance_id="default"):
    """
    List GCP proxy instances for a specific instance configuration.

    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration

    Returns:
        list: List of instances
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"].get(instance_id, config["providers"]["gcp"]["instances"]["default"])

    compute_client = get_compute_client(instance_id)

    if compute_client is None:
        logger.warning(f"No GCP credentials found for instance '{instance_id}'. Cannot list instances.")
        return []

    result = compute_client.instances().list(
        project=instance_config["project"],
        zone=instance_config["zone"],
        filter='labels.cloudproxy eq cloudproxy'
    ).execute()
    return result['items'] if 'items' in result else []
