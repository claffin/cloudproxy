import datetime
import itertools

from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.aws.functions import (
    list_instances,
    create_proxy,
    delete_proxy,
    stop_proxy,
    start_proxy,
)
from cloudproxy.providers.settings import delete_queue, restart_queue, config


def aws_deployment(min_scaling):
    total_instances = len(list_instances())
    if min_scaling < total_instances:
        logger.info("Overprovisioned: AWS destroying.....")
        for instance in itertools.islice(
            list_instances(), 0, (total_instances - min_scaling)
        ):
            delete_proxy(instance["Instances"][0]["InstanceId"])
            try:
                msg = instance["Instances"][0]["PublicIpAddress"]
            except KeyError:
                msg = instance["Instances"][0]["InstanceId"]

            logger.info("Destroyed: AWS -> " + msg)
    if min_scaling - total_instances < 1:
        logger.info("Minimum AWS instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info("Deploying: " + str(total_deploy) + " AWS instances")
        for _ in range(total_deploy):
            create_proxy()
            logger.info("Deployed")
    return len(list_instances())


def aws_check_alive():
    ip_ready = []
    for instance in list_instances():
        try:
            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - instance["Instances"][0]["LaunchTime"]
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                delete_proxy(instance["Instances"][0]["InstanceId"])
                logger.info(
                    "Recycling droplet, reached age limit -> " + instance["Instances"][0]["PublicIpAddress"]
                )
            elif instance["Instances"][0]["State"]["Name"] == "stopped":
                logger.info(
                    "Waking up: AWS -> Instance " + instance["Instances"][0]["InstanceId"]
                )
                started = start_proxy(instance["Instances"][0]["InstanceId"])
                if not started:
                    logger.info(
                        "Could not wake up due to IncorrectSpotRequestState, trying again later."
                    )
            elif instance["Instances"][0]["State"]["Name"] == "stopping":
                logger.info(
                    "Stopping: AWS -> " + instance["Instances"][0]["PublicIpAddress"]
                )
            elif instance["Instances"][0]["State"]["Name"] == "pending":
                logger.info(
                    "Pending: AWS -> " + instance["Instances"][0]["PublicIpAddress"]
                )
            # Must be "pending" if none of the above, check if alive or not.
            elif check_alive(instance["Instances"][0]["PublicIpAddress"]):
                logger.info(
                    "Alive: AWS -> " + instance["Instances"][0]["PublicIpAddress"]
                )
                ip_ready.append(instance["Instances"][0]["PublicIpAddress"])
            else:
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(instance["Instances"][0]["InstanceId"])
                    logger.info(
                        "Destroyed: took too long AWS -> "
                        + instance["Instances"][0]["PublicIpAddress"]
                    )
                else:
                    logger.info(
                        "Waiting: AWS -> " + instance["Instances"][0]["PublicIpAddress"]
                    )
        except (TypeError, KeyError):
            logger.info("Pending: AWS -> allocating ip")
    return ip_ready


def aws_check_delete():
    for instance in list_instances():
        if instance["Instances"][0].get("PublicIpAddress") in delete_queue:
            delete_proxy(instance["Instances"][0]["InstanceId"])
            logger.info(
                "Destroyed: not wanted -> "
                + instance["Instances"][0]["PublicIpAddress"]
            )
            delete_queue.remove(instance["Instances"][0]["PublicIpAddress"])


def aws_check_stop():
    for instance in list_instances():
        if instance["Instances"][0].get("PublicIpAddress") in restart_queue:
            stop_proxy(instance["Instances"][0]["InstanceId"])
            logger.info(
                "Stopped: getting new IP -> "
                + instance["Instances"][0]["PublicIpAddress"]
            )
            restart_queue.remove(instance["Instances"][0]["PublicIpAddress"])


def aws_start():
    aws_check_delete()
    aws_check_stop()
    aws_deployment(config["providers"]["aws"]["scaling"]["min_scaling"])
    ip_ready = aws_check_alive()
    return ip_ready
