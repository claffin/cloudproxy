import datetime
import itertools

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.aws.functions import (
    list_instances,
    create_proxy,
    delete_proxy,
)
from cloudproxy.providers.settings import delete_queue, config


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
            if check_alive(instance["Instances"][0]["PublicIpAddress"]):
                logger.info(
                    "Alive: AWS -> " + instance["Instances"][0]["PublicIpAddress"]
                )
                ip_ready.append(instance["Instances"][0]["PublicIpAddress"])
            else:
                elapsed = datetime.datetime.now(
                    datetime.timezone.utc
                ) - dateparser.parse(instance["Instances"][0]["LaunchTime"])
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
            logger.info("Pending: AWS allocating")
    return ip_ready


def aws_check_delete():
    for instance in list_instances():
        if instance["Instances"][0]["PublicIpAddress"] in delete_queue:
            delete_proxy(instance["Instances"][0]["InstanceId"])
            logger.info(
                "Destroyed: not wanted -> "
                + instance["Instances"][0]["PublicIpAddress"]
            )
            delete_queue.remove(instance["Instances"][0]["PublicIpAddress"])
            return True
        else:
            return False


def aws_start():
    aws_deployment(config["providers"]["aws"]["scaling"]["min_scaling"])
    ip_ready = aws_check_alive()
    aws_check_delete()
    return ip_ready
