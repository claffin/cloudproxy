import boto3
import os
import json
import botocore as botocore
import botocore.exceptions

from cloudproxy.providers.config import set_auth
from cloudproxy.providers.settings import config
from cloudproxy.credentials import credential_manager
 
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
 
# Module-level variables needed for tests (kept for potential future use or specific test setups, but not used by get_clients for caching)
# ec2 = None
# ec2_client = None

def reset_clients():
    """
    Reset any module-level state if necessary (e.g., for testing).
    For the current get_clients implementation, this function does nothing.
    """
    # global ec2, ec2_client # If we were caching them here per instance_id
    # ec2 = {}
    # ec2_client = {}
    pass

def get_clients(provider_name: str, instance_id: str):
    """
    Initialize and return AWS clients based on credentials from CredentialManager.
    Always creates new clients for the specific instance ID.
    
    Args:
        provider_name: The name of the cloud provider (e.g., "aws")
        instance_id: The ID of the instance configuration
        
    Returns:
        tuple: (ec2_resource, ec2_client) or (None, None) if credentials not found or invalid
    """
    # Do NOT use module-level global variables for caching clients here.
    # Each call gets clients specific to the instance_id.

    if credential_manager is None:
        logger.error("CredentialManager not initialized in aws.functions.get_clients")
        return None, None

    secrets = credential_manager.get_credentials(provider_name, instance_id)

    if not secrets:
        # logger.debug(f"No AWS credentials found for instance '{instance_id}'.") # Use debug for less noise
        return None, None

    aws_access_key_id = secrets.get("access_key_id")
    aws_secret_access_key = secrets.get("secret_access_key")
    region_name = secrets.get("region") # Assuming region is also stored in secrets

    if not aws_access_key_id or not aws_secret_access_key or not region_name:
        logger.warning(f"Incomplete AWS credentials for instance '{instance_id}'. Missing access_key_id, secret_access_key, or region.")
        return None, None
    
    # Always create new clients for this specific call
    try:
        local_ec2_resource = boto3.resource( # Use local variables
            "ec2",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        local_ec2_client = boto3.client( # Use local variables
            "ec2",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        return local_ec2_resource, local_ec2_client
    except Exception as e:
        logger.error(f"Error creating AWS clients for {instance_id}: {e}")
        return None, None

def get_tags(instance_config=None):
    """
    Get tags for AWS resources based on the provided configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        tuple: (tags, tag_specification)
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"]["default"]
    
    # Use instance name in the tag if available
    instance_name = instance_config.get("display_name", "default")
    instance_id = next(
        (name for name, inst in config["providers"]["aws"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    tags = [
        {"Key": "cloudproxy", "Value": "cloudproxy"},
        {"Key": "cloudproxy-instance", "Value": instance_id},
        {"Key": "Name", "Value": f"CloudProxy-{instance_name}"}
    ]
    
    tag_specification = [
        {"ResourceType": "instance", "Tags": tags},
    ]
    
    return tags, tag_specification


def create_proxy(instance_config=None, instance_id="default"):
    """
    Create an AWS proxy instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(instance_id, config["providers"]["aws"]["instances"]["default"])
    
    # Get clients using provider name and instance ID
    ec2, ec2_client = get_clients("aws", instance_id)

    if ec2 is None or ec2_client is None:
        # No credentials found for this instance, cannot create proxy
        print(f"No AWS credentials found for instance '{instance_id}'. Cannot create proxy.")
        return None

    tags, tag_specification = get_tags(instance_config)
    
    # Find default VPC
    vpcs = list((ec2.vpcs.filter()))
    default_vpc = None
    for vpc in vpcs:
        response = ec2_client.describe_vpcs(
            VpcIds=[
                vpc.id,
            ],
        )

        if response["Vpcs"][0]["IsDefault"]:
            default_vpc = response["Vpcs"][0]["VpcId"]
    
    # Setup user data with appropriate authentication
    user_data = set_auth(config["auth"]["username"], config["auth"]["password"])
    
    # Create security group if needed
    try:
        sg = ec2.create_security_group(
            Description=f"SG for CloudProxy {instance_config.get('display_name', 'default')}",
            GroupName=f"cloudproxy-{next((name for name, inst in config['providers']['aws']['instances'].items() if inst == instance_config), 'default')}",
            VpcId=default_vpc
        )
        sg.authorize_ingress(
            CidrIp="0.0.0.0/0", IpProtocol="tcp", FromPort=8899, ToPort=8899
        )
        sg.authorize_ingress(
            CidrIp="0.0.0.0/0", IpProtocol="tcp", FromPort=22, ToPort=22
        )
    except botocore.exceptions.ClientError:
        pass
    
    # Get security group ID
    sg_id = ec2_client.describe_security_groups(
        Filters=[
            {'Name': 'vpc-id', 'Values': [default_vpc]},
            {'Name': 'group-name', 'Values': [f"cloudproxy-{next((name for name, inst in config['providers']['aws']['instances'].items() if inst == instance_config), 'default')}"]}
        ]
    )
    sg_id = sg_id["SecurityGroups"][0]["GroupId"]
    
    # Create instance with appropriate spot configuration
    if instance_config["spot"] == 'persistent':
        instance = ec2.create_instances(
            ImageId=instance_config["ami"],
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_config["size"],
            NetworkInterfaces=[
                {"DeviceIndex": 0, "AssociatePublicIpAddress": True, "Groups": [sg_id]}
            ],
            InstanceMarketOptions={
                "MarketType": "spot",
                "SpotOptions": {
                    "InstanceInterruptionBehavior": "stop",
                    "SpotInstanceType": "persistent"
                }
            },
            TagSpecifications=tag_specification,
            UserData=user_data,
        )
    elif instance_config["spot"] == 'one-time':
            instance = ec2.create_instances(
                ImageId=instance_config["ami"],
                MinCount=1,
                MaxCount=1,
                InstanceType=instance_config["size"],
                NetworkInterfaces=[
                    {"DeviceIndex": 0, "AssociatePublicIpAddress": True, "Groups": [sg_id]}
                ],
                InstanceMarketOptions={
                    "MarketType": "spot",
                    "SpotOptions": {
                        "InstanceInterruptionBehavior": "terminate",
                        "SpotInstanceType": "one-time"
                    }
                },
                TagSpecifications=tag_specification,
                UserData=user_data,
            )
    else:
        instance = ec2.create_instances(
            ImageId=instance_config["ami"],
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_config["size"],
            NetworkInterfaces=[
                {"DeviceIndex": 0, "AssociatePublicIpAddress": True, "Groups": [sg_id]}
            ],
            TagSpecifications=tag_specification,
            UserData=user_data,
        )
    return instance


def delete_proxy(instance_id, instance_config=None, config_instance_id="default"):
    """
    Delete an AWS proxy instance.
    
    Args:
        instance_id: ID of the instance to delete
        instance_config: The specific instance configuration (for non-secret settings)
        config_instance_id: The ID of the instance configuration in settings.config
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(config_instance_id, config["providers"]["aws"]["instances"]["default"])
    
    # Get clients using provider name and instance ID
    ec2, ec2_client = get_clients("aws", config_instance_id)

    if ec2 is None or ec2_client is None:
        # No credentials found for this instance, cannot delete proxy
        print(f"No AWS credentials found for instance '{config_instance_id}'. Cannot delete proxy.")
        return None

    ids = [instance_id]
    deleted = ec2.instances.filter(InstanceIds=ids).terminate()
    if instance_config["spot"]:
        associated_spot_instance_requests = ec2_client.describe_spot_instance_requests(
            Filters=[
                {
                    'Name': 'instance-id',
                    'Values': ids
                }
            ]
        )
        spot_instance_id_list = []
        for spot_instance in associated_spot_instance_requests["SpotInstanceRequests"]:
            spot_instance_id_list.append(spot_instance.get("SpotInstanceRequestId"))
        if spot_instance_id_list:
            ec2_client.cancel_spot_instance_requests(SpotInstanceRequestIds=spot_instance_id_list)
    return deleted


def stop_proxy(instance_id, instance_config=None, config_instance_id="default"):
    """
    Stop an AWS proxy instance.
    
    Args:
        instance_id: ID of the instance to stop
        instance_config: The specific instance configuration (for non-secret settings)
        config_instance_id: The ID of the instance configuration in settings.config
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(config_instance_id, config["providers"]["aws"]["instances"]["default"])
    
    # Get clients using provider name and instance ID
    ec2, ec2_client = get_clients("aws", config_instance_id)

    if ec2 is None or ec2_client is None:
        # No credentials found for this instance, cannot stop proxy
        print(f"No AWS credentials found for instance '{config_instance_id}'. Cannot stop proxy.")
        return None

    ids = [instance_id]
    stopped = ec2.instances.filter(InstanceIds=ids).stop()
    return stopped


def start_proxy(instance_id, instance_config=None, config_instance_id="default"):
    """
    Start an AWS proxy instance.
    
    Args:
        instance_id: ID of the instance to start
        instance_config: The specific instance configuration (for non-secret settings)
        config_instance_id: The ID of the instance configuration in settings.config
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(config_instance_id, config["providers"]["aws"]["instances"]["default"])
    
    # Get clients using provider name and instance ID
    ec2, ec2_client = get_clients("aws", config_instance_id)

    if ec2 is None or ec2_client is None:
        # No credentials found for this instance, cannot start proxy
        print(f"No AWS credentials found for instance '{config_instance_id}'. Cannot start proxy.")
        return None

    ids = [instance_id]
    try:
        started = ec2.instances.filter(InstanceIds=ids).start()
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'IncorrectSpotRequestState':
            return None
        else:
            raise error
    return started


def list_instances(instance_config=None, instance_id="default"):
    """
    List AWS proxy instances for a specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
        
    Returns:
        list: List of AWS instances
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(instance_id, config["providers"]["aws"]["instances"]["default"])
    
    # Get clients using provider name and instance ID
    ec2, ec2_client = get_clients("aws", instance_id)

    if ec2 is None or ec2_client is None:
        # No credentials found for this instance, cannot list instances
        print(f"No AWS credentials found for instance '{instance_id}'. Cannot list instances.")
        return []
    
    # Filter instances for this specific instance
    filters = [
        {"Name": "tag:cloudproxy", "Values": ["cloudproxy"]},
        {"Name": "tag:cloudproxy-instance", "Values": [instance_id]},
        {"Name": "instance-state-name", "Values": ["pending", "running", "stopped", "stopping"]},
    ]
    instances = ec2_client.describe_instances(Filters=filters)
    result = instances["Reservations"]
    
    # If this is the default instance, also find instances created before multi-instance support
    if instance_id == "default":
        # Get all cloudproxy instances without filtering by instance tag
        base_filters = [
            {"Name": "tag:cloudproxy", "Values": ["cloudproxy"]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopped", "stopping"]},
        ]
        all_instances = ec2_client.describe_instances(Filters=base_filters)
        
        # Track IDs we already have in our result
        existing_ids = set()
        for reservation in result:
            for instance in reservation["Instances"]:
                existing_ids.add(instance["InstanceId"])
        
        # Add instances that don't have the cloudproxy-instance tag at all
        for reservation in all_instances["Reservations"]:
            for instance in reservation["Instances"]:
                # Skip if we already have this instance
                if instance["InstanceId"] in existing_ids:
                    continue
                
                # Check if this instance has any cloudproxy-instance tag
                has_instance_tag = False
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "cloudproxy-instance":
                        has_instance_tag = True
                        break
                
                # If no instance tag, add this reservation to our results
                if not has_instance_tag:
                    result.append(reservation)
                    existing_ids.add(instance["InstanceId"])
    
    return result
