import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Tuple

from cloudproxy.credentials import credential_manager
from cloudproxy.providers.aws.functions import reset_clients as reset_aws_clients
from cloudproxy.providers.digitalocean.functions import reset_clients as reset_digitalocean_clients
from cloudproxy.providers.gcp.functions import reset_clients as reset_gcp_clients
from cloudproxy.providers.hetzner.functions import reset_clients as reset_hetzner_clients
# Import reset_clients for other providers as needed

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/credentials",
    tags=["Credentials"],
)

class Secrets(BaseModel):
    # This model is flexible and will accept any key-value pairs
    # Specific validation for each provider's secrets can be added later if needed
    secrets: Dict[str, Any]

@router.post("/{provider_name}/{instance_id}")
async def add_or_update_credentials(provider_name: str, instance_id: str, secrets: Secrets):
    """
    Adds or updates credentials for a specific provider instance.
    """
    if credential_manager is None:
        raise HTTPException(status_code=500, detail="CredentialManager not initialized")

    credential_manager.add_credentials(provider_name, instance_id, secrets.secrets)

    # Trigger client reset for the specific provider
    if provider_name == "aws":
        reset_aws_clients()
    elif provider_name == "digitalocean":
        reset_digitalocean_clients()
    elif provider_name == "gcp":
        reset_gcp_clients()
    elif provider_name == "hetzner":
        reset_hetzner_clients()
    # Add other providers here

    return {"message": f"Credentials added/updated for {provider_name}/{instance_id}"}

@router.get("/")
async def list_credentials_configurations() -> List[Tuple[str, str]]:
    """
    Lists all provider/instance configurations with stored credentials.
    """
    if credential_manager is None:
        raise HTTPException(status_code=500, detail="CredentialManager not initialized")

    return credential_manager.list_configurations()

@router.delete("/{provider_name}/{instance_id}")
async def remove_credentials(provider_name: str, instance_id: str):
    """
    Removes credentials for a specific provider instance.
    """
    if credential_manager is None:
        raise HTTPException(status_code=500, detail="CredentialManager not initialized")

    credential_manager.remove_credentials(provider_name, instance_id)

    # Trigger client reset for the specific provider
    if provider_name == "aws":
        reset_aws_clients()
    elif provider_name == "digitalocean":
        reset_digitalocean_clients()
    elif provider_name == "gcp":
        reset_gcp_clients()
    elif provider_name == "hetzner":
        reset_hetzner_clients()
    # Add other providers here

    return {"message": f"Credentials removed for {provider_name}/{instance_id}"}