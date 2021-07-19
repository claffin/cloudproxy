import boto3
import os
import json
import botocore as botocore
import botocore.exceptions

from cloudproxy.providers.config import set_auth
from cloudproxy.providers.settings import config

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

ec2 = boto3.resource("ec2", region_name=config["providers"]["aws"]["region"])
ec2_client = boto3.client("ec2", region_name=config["providers"]["aws"]["region"])
tags = [{"Key": "cloudproxy", "Value": "cloudproxy"}]
tag_specification = [
    {"ResourceType": "instance", "Tags": tags},
]


def create_proxy():
    vpcs = list((ec2.vpcs.filter()))
    for vpc in vpcs:
        response = ec2_client.describe_vpcs(
            VpcIds=[
                vpc.id,
            ],
        )

        if response["Vpcs"][0]["IsDefault"]:
            default_vpc = response["Vpcs"][0]["VpcId"]
    user_data = set_auth(config["auth"]["username"], config["auth"]["password"])
    try:
        sg = ec2.create_security_group(
            Description="SG for CloudProxy", GroupName="cloudproxy", VpcId=default_vpc
        )
        sg.authorize_ingress(
            CidrIp="0.0.0.0/0", IpProtocol="tcp", FromPort=8899, ToPort=8899
        )
        sg.authorize_ingress(
            CidrIp="0.0.0.0/0", IpProtocol="tcp", FromPort=22, ToPort=22
        )
    except botocore.exceptions.ClientError:
        pass
    sg_id = ec2_client.describe_security_groups(GroupNames=["cloudproxy"])
    sg_id = sg_id["SecurityGroups"][0]["GroupId"]
    if config["providers"]["aws"]["spot"] == 'persistent':
        instance = ec2.create_instances(
            ImageId=config["providers"]["aws"]["ami"],
            MinCount=1,
            MaxCount=1,
            InstanceType=config["providers"]["aws"]["size"],
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
    elif config["providers"]["aws"]["spot"] == 'one-time':
            instance = ec2.create_instances(
                ImageId=config["providers"]["aws"]["ami"],
                MinCount=1,
                MaxCount=1,
                InstanceType=config["providers"]["aws"]["size"],
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
            ImageId=config["providers"]["aws"]["ami"],
            MinCount=1,
            MaxCount=1,
            InstanceType=config["providers"]["aws"]["size"],
            NetworkInterfaces=[
                {"DeviceIndex": 0, "AssociatePublicIpAddress": True, "Groups": [sg_id]}
            ],
            TagSpecifications=tag_specification,
            UserData=user_data,
        )
    return instance


def delete_proxy(instance_id):
    ids = [instance_id]
    deleted = ec2.instances.filter(InstanceIds=ids).terminate()
    if config["providers"]["aws"]["spot"]:
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


def stop_proxy(instance_id):
    ids = [instance_id]
    stopped = ec2.instances.filter(InstanceIds=ids).stop()
    return stopped


def start_proxy(instance_id):
    ids = [instance_id]
    try:
        started = ec2.instances.filter(InstanceIds=ids).start()
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'IncorrectSpotRequestState':
            return None
        else:
            raise error
    return started


def list_instances():
    filters = [
        {"Name": "tag:cloudproxy", "Values": ["cloudproxy"]},
        {"Name": "instance-state-name", "Values": ["pending", "running", "stopped", "stopping"]},
    ]
    instances = ec2_client.describe_instances(Filters=filters)
    return instances["Reservations"]
