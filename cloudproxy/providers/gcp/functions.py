import json
import uuid

from loguru import logger

import googleapiclient.discovery
from google.oauth2 import service_account

from cloudproxy.providers.config import set_auth
from cloudproxy.providers.settings import config

gcp = config["providers"]["gcp"]
if gcp["enabled"] == 'True':
    try:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(gcp["secrets"]["service_account_key"])
        )
        compute = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)
    except TypeError:
        logger.error("GCP -> Invalid service account key")


def create_proxy():
    image_response = compute.images().getFromFamily(
        project=gcp["image_project"], 
        family=gcp["image_family"]
    ).execute()
    source_disk_image = image_response['selfLink']

    body = {
        'name': 'cloudproxy-' + str(uuid.uuid4()),
        'machineType': 
            f"zones/{gcp['zone']}/machineTypes/{gcp['size']}",
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
        project=gcp["project"],
        zone=gcp["zone"],
        body=body
    ).execute()

def delete_proxy(name):
    try:
        return compute.instances().delete(
            project=gcp["project"],
            zone=gcp["zone"],
            instance=name
        ).execute()
    except(googleapiclient.errors.HttpError):
        logger.info(f"GCP --> HTTP Error when trying to delete proxy {name}. Probably has already been deleted.")
        return None

def stop_proxy(name):
    try:
        return compute.instances().stop(
            project=gcp["project"],
            zone=gcp["zone"],
            instance=name
        ).execute()
    except(googleapiclient.errors.HttpError):
        logger.info(f"GCP --> HTTP Error when trying to stop proxy {name}. Probably has already been deleted.")
        return None

def start_proxy(name):
    try:
        return compute.instances().start(
            project=gcp["project"],
            zone=gcp["zone"],
            instance=name
        ).execute()
    except(googleapiclient.errors.HttpError):
        logger.info(f"GCP --> HTTP Error when trying to start proxy {name}. Probably has already been deleted.")
        return None

def list_instances():
    result = compute.instances().list(
        project=gcp["project"], 
        zone=gcp["zone"], 
        filter='labels.cloudproxy eq cloudproxy'
    ).execute()
    return result['items'] if 'items' in result else []
