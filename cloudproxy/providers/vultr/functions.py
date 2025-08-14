import uuid
import base64
import requests
from typing import List, Dict, Any, Optional
from loguru import logger

from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth


class VultrFirewallExistsException(Exception):
    pass


class VultrInstance:
    """Wrapper class for Vultr instance data."""

    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('id')
        self.main_ip = data.get('main_ip')
        self.ip_address = data.get('main_ip')  # Alias for compatibility
        self.label = data.get('label', '')
        self.date_created = data.get('date_created')
        self.status = data.get('status')
        self.region = data.get('region')
        self.plan = data.get('plan')
        self.tags = data.get('tags', [])
        self._raw_data = data


def get_api_headers(instance_config: Optional[Dict] = None) -> Dict[str, str]:
    """
    Get API headers with authentication for Vultr API.

    Args:
        instance_config: The specific instance configuration

    Returns:
        dict: Headers for API requests
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["vultr"]["instances"]["default"]

    return {
        "Authorization": f"Bearer {instance_config['secrets']['api_token']}",
        "Content-Type": "application/json"
    }


def create_proxy(instance_config: Optional[Dict] = None) -> bool:
    """
    Create a Vultr proxy instance.

    Args:
        instance_config: The specific instance configuration

    Returns:
        bool: True if creation was successful
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["vultr"]["instances"]["default"]

    # Get instance name for tagging
    instance_id = next(
        (name for name, inst in settings.config["providers"]["vultr"]["instances"].items()
         if inst == instance_config),
        "default"
    )

    # Prepare user data
    user_data = set_auth(
        settings.config["auth"]["username"],
        settings.config["auth"]["password"]
    )

    # Base64 encode the user data
    user_data_encoded = base64.b64encode(user_data.encode()).decode()

    # Prepare instance creation payload
    payload = {
        "region": instance_config["region"],
        "plan": instance_config["plan"],
        # Ubuntu 22.04 LTS x64 default
        "os_id": instance_config.get("os_id", 1743),
        "label": f"cloudproxy-{instance_id}-{str(uuid.uuid1())}",
        "user_data": user_data_encoded,
        "tags": ["cloudproxy", f"cloudproxy-{instance_id}"],
        "enable_ipv6": False,
        "backups": "disabled",
        "ddos_protection": False
    }

    # Add firewall group if it exists
    firewall_group_id = instance_config.get("firewall_group_id")
    if firewall_group_id:
        payload["firewall_group_id"] = firewall_group_id

    try:
        response = requests.post(
            "https://api.vultr.com/v2/instances",
            headers=get_api_headers(instance_config),
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        logger.info(
            f"Created Vultr instance: {data.get('instance', {}).get('id')}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create Vultr instance: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False


def delete_proxy(instance: Any,
                 instance_config: Optional[Dict] = None) -> bool:
    """
    Delete a Vultr proxy instance.

    Args:
        instance: Instance ID or VultrInstance object
        instance_config: The specific instance configuration

    Returns:
        bool: True if deletion was successful
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["vultr"]["instances"]["default"]

    # Extract instance ID
    if hasattr(instance, 'id'):
        instance_id = instance.id
    else:
        instance_id = instance

    try:
        response = requests.delete(
            f"https://api.vultr.com/v2/instances/{instance_id}",
            headers=get_api_headers(instance_config)
        )

        # 204 No Content is success for DELETE
        if response.status_code == 204:
            logger.info(f"Successfully deleted Vultr instance: {instance_id}")
            return True
        elif response.status_code == 404:
            logger.info(
                f"Vultr instance {instance_id} not found, considering it already deleted")
            return True
        else:
            response.raise_for_status()
            return False

    except requests.exceptions.RequestException as e:
        # Check if instance is already gone
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                logger.info(
                    f"Vultr instance {instance_id} not found, considering it already deleted")
                return True

        logger.error(f"Failed to delete Vultr instance {instance_id}: {e}")
        return False


def list_instances(
        instance_config: Optional[Dict] = None) -> List[VultrInstance]:
    """
    List Vultr proxy instances.

    Args:
        instance_config: The specific instance configuration

    Returns:
        list: List of VultrInstance objects
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["vultr"]["instances"]["default"]

    # Get instance name for tagging
    instance_id = next(
        (name for name, inst in settings.config["providers"]["vultr"]["instances"].items()
         if inst == instance_config),
        "default"
    )

    try:
        # Get all instances with the specific tag
        response = requests.get(
            "https://api.vultr.com/v2/instances",
            headers=get_api_headers(instance_config),
            params={"tag": f"cloudproxy-{instance_id}", "per_page": 500}
        )
        response.raise_for_status()

        data = response.json()
        instances = data.get('instances', [])

        # If this is the default instance, also get instances with just the
        # cloudproxy tag
        if instance_id == "default":
            response_old = requests.get(
                "https://api.vultr.com/v2/instances",
                headers=get_api_headers(instance_config),
                params={"tag": "cloudproxy", "per_page": 500}
            )

            if response_old.status_code == 200:
                data_old = response_old.json()
                old_instances = data_old.get('instances', [])

                # Filter out instances that have instance-specific tags
                existing_ids = {inst['id'] for inst in instances}
                for inst in old_instances:
                    tags = inst.get('tags', [])
                    has_instance_tag = any(
                        tag.startswith('cloudproxy-') and tag != 'cloudproxy'
                        for tag in tags
                    )
                    if not has_instance_tag and inst['id'] not in existing_ids:
                        instances.append(inst)

        # Convert to VultrInstance objects
        return [VultrInstance(inst) for inst in instances]

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to list Vultr instances: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return []


def create_firewall(instance_config: Optional[Dict] = None) -> Optional[str]:
    """
    Create a Vultr firewall group for proxy instances.

    Args:
        instance_config: The specific instance configuration

    Returns:
        str: Firewall group ID if created successfully

    Raises:
        VultrFirewallExistsException: If firewall already exists
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["vultr"]["instances"]["default"]

    # Get instance name for firewall naming
    instance_id = next(
        (name for name, inst in settings.config["providers"]["vultr"]["instances"].items()
         if inst == instance_config),
        "default"
    )

    firewall_name = f"cloudproxy-{instance_id}"

    # First check if firewall already exists
    try:
        response = requests.get(
            "https://api.vultr.com/v2/firewalls",
            headers=get_api_headers(instance_config),
            params={"per_page": 500}
        )
        response.raise_for_status()

        data = response.json()
        for fw in data.get('firewall_groups', []):
            if fw.get('description') == firewall_name:
                # Store the firewall group ID in the config
                instance_config['firewall_group_id'] = fw['id']
                raise VultrFirewallExistsException(
                    f"Firewall already exists: {fw['id']}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check existing firewalls: {e}")

    # Create new firewall group
    try:
        response = requests.post(
            "https://api.vultr.com/v2/firewalls",
            headers=get_api_headers(instance_config),
            json={"description": firewall_name}
        )
        response.raise_for_status()

        data = response.json()
        firewall_group_id = data.get('firewall_group', {}).get('id')

        if firewall_group_id:
            # Store the firewall group ID
            instance_config['firewall_group_id'] = firewall_group_id

            # Add firewall rules
            _create_firewall_rules(firewall_group_id, instance_config)

            logger.info(f"Created firewall group: {firewall_group_id}")
            return firewall_group_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create firewall group: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response: {e.response.text}")

    return None


def _create_firewall_rules(firewall_group_id: str,
                           instance_config: Dict) -> None:
    """
    Create firewall rules for the firewall group.

    Args:
        firewall_group_id: The firewall group ID
        instance_config: The instance configuration
    """
    rules = [
        # Allow inbound on port 8899 (proxy port)
        {
            "ip_type": "v4",
            "protocol": "tcp",
            "port": "8899",
            "subnet": "0.0.0.0",
            "subnet_size": 0,
            "notes": "CloudProxy port"
        },
        # Allow all outbound TCP
        {
            "ip_type": "v4",
            "protocol": "tcp",
            "port": "1:65535",
            "subnet": "0.0.0.0",
            "subnet_size": 0,
            "notes": "All outbound TCP"
        },
        # Allow all outbound UDP
        {
            "ip_type": "v4",
            "protocol": "udp",
            "port": "1:65535",
            "subnet": "0.0.0.0",
            "subnet_size": 0,
            "notes": "All outbound UDP"
        }
    ]

    for rule in rules:
        try:
            response = requests.post(
                f"https://api.vultr.com/v2/firewalls/{firewall_group_id}/rules",
                headers=get_api_headers(instance_config),
                json=rule
            )
            response.raise_for_status()
            logger.debug(f"Added firewall rule: {rule['notes']}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add firewall rule: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
