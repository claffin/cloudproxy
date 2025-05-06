import logging

logger = logging.getLogger(__name__)

class CredentialManager:
    def __init__(self):
        # Stores credentials in memory: {"provider_name": {"instance_id": {"key1": "value1", ...}}}
        self._credentials = {}
        logger.info("CredentialManager initialized.")

    def add_credentials(self, provider_name: str, instance_id: str, secrets: dict):
        """Adds or updates credentials for a specific provider instance."""
        if provider_name not in self._credentials:
            self._credentials[provider_name] = {}

        self._credentials[provider_name][instance_id] = secrets
        logger.info(f"Credentials added/updated for {provider_name}/{instance_id}")

    def get_credentials(self, provider_name: str, instance_id: str) -> dict | None:
        """Retrieves credentials for a specific provider instance."""
        return self._credentials.get(provider_name, {}).get(instance_id)

    def remove_credentials(self, provider_name: str, instance_id: str):
        """Removes credentials for a specific provider instance."""
        if provider_name in self._credentials and instance_id in self._credentials[provider_name]:
            del self._credentials[provider_name][instance_id]
            logger.info(f"Credentials removed for {provider_name}/{instance_id}")
            if not self._credentials[provider_name]:
                del self._credentials[provider_name]
        else:
            logger.warning(f"Attempted to remove non-existent credentials for {provider_name}/{instance_id}")

    def list_configurations(self) -> list[tuple[str, str]]:
        """Lists all provider/instance configurations with stored credentials."""
        configurations = []
        for provider_name, instances in self._credentials.items():
            for instance_id in instances:
                configurations.append((provider_name, instance_id))
        return configurations

# Global instance of the CredentialManager
# This will be initialized in main.py
credential_manager = None