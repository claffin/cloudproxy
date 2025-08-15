import os
import random
import sys
import re
import logging
import uuid
from datetime import datetime, UTC
from typing import List, Optional, Set, Dict, Any

import uvicorn
from loguru import logger
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, IPvAnyAddress, Field, field_validator

from cloudproxy.providers import settings
from cloudproxy.providers.settings import delete_queue, restart_queue
from cloudproxy.providers.rolling import rolling_manager

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="CloudProxy API",
        version="1.0.0",
        description="""
        CloudProxy API allows you to manage proxy servers across multiple cloud providers.
        
        ## Features
        * Deploy and scale proxies across multiple cloud providers
        * Automatic proxy rotation
        * Provider-specific configuration
        * Health monitoring
        
        ## Authentication
        Basic authentication is used for proxy access. Configure via environment variables:
        * USERNAME
        * PASSWORD
        """,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(
    title="CloudProxy",
    description="Cloud-based Proxy Management API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="CloudProxy API",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    return custom_openapi()

# Check if UI directories exist before mounting
ui_dir = os.path.join(__location__, "../cloudproxy-ui/dist")
css_dir = os.path.join(__location__, "../cloudproxy-ui/dist/css")
js_dir = os.path.join(__location__, "../cloudproxy-ui/dist/js")

if os.path.exists(ui_dir):
    app.mount("/ui", StaticFiles(directory=ui_dir, html=True), name="static")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir, html=True), name="cssstatic")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="jsstatic")
else:
    logger.warning(f"UI directory {ui_dir} does not exist. UI will not be available.")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger.add("cloudproxy.log", rotation="20 MB")

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def main():
    # Intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.INFO)
    
    # Remove every other logger's handlers and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    
    # Start uvicorn with modified logging config
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


# Pydantic Models for Request/Response
class Metadata(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

class ProxyAddress(BaseModel):
    ip: IPvAnyAddress
    port: int = 8899
    auth_enabled: bool = True
    url: Optional[str] = None
    provider: Optional[str] = None
    instance: Optional[str] = None
    display_name: Optional[str] = None

    @field_validator('url', mode='before')
    @classmethod
    def set_url(cls, v, info):
        values = info.data
        ip = str(values.get('ip'))
        port = values.get('port', 8899)
        if values.get('auth_enabled'):
            return f"http://{settings.config['auth']['username']}:{settings.config['auth']['password']}@{ip}:{port}"
        return f"http://{ip}:{port}"

class ProxyList(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    total: int
    proxies: List[ProxyAddress]

class ProxyResponse(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    message: str
    proxy: ProxyAddress

class ErrorResponse(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    error: str
    detail: str

# Helper function to convert IP string to ProxyAddress
def create_proxy_address(ip: str) -> ProxyAddress:
    return ProxyAddress(
        ip=ip,
        auth_enabled=not settings.config["no_auth"]
    )

# Updated get_ip_list function
def get_ip_list() -> List[ProxyAddress]:
    ip_list = []
    for provider_name, provider_config in settings.config["providers"].items():
        # Handle top-level IPs (for backward compatibility)
        if "ips" in provider_config:
            for ip in provider_config["ips"]:
                if ip not in delete_queue and ip not in restart_queue:
                    proxy = create_proxy_address(ip)
                    proxy.provider = provider_name
                    proxy.instance = "default"  # Assume default instance for top-level IPs
                    proxy.display_name = provider_config.get("display_name", provider_name)
                    ip_list.append(proxy)
                    
        # Skip providers that don't have an instances field (like azure)
        if "instances" not in provider_config:
            continue
            
        # Process each instance
        for instance_name, instance_config in provider_config["instances"].items():
            if "ips" in instance_config:
                for ip in instance_config["ips"]:
                    if ip not in delete_queue and ip not in restart_queue:
                        proxy = create_proxy_address(ip)
                        proxy.provider = provider_name
                        proxy.instance = instance_name
                        proxy.display_name = instance_config.get("display_name")
                        ip_list.append(proxy)
                        
    return ip_list

# Updated API endpoints
@app.get("/", tags=["Proxies"], response_model=ProxyList)
def read_root(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get a list of all available proxy servers.
    
    Args:
        offset: Number of items to skip (pagination)
        limit: Maximum number of items to return
        
    Returns:
        ProxyList: A paginated list of proxy servers with metadata
    """
    all_proxies = get_ip_list()
    return ProxyList(
        total=len(all_proxies),
        proxies=all_proxies[offset:offset + limit]
    )

@app.get("/random", tags=["Proxies"], response_model=ProxyResponse)
def read_random():
    """
    Get a random proxy server from the available pool.
    
    Returns:
        ProxyResponse: A single random proxy with metadata
        
    Raises:
        HTTPException: If no proxies are available
    """
    proxies = get_ip_list()
    if not proxies:
        raise HTTPException(
            status_code=404,
            detail="No proxies available"
        )
    proxy = random.choice(proxies)
    return ProxyResponse(
        message="Random proxy retrieved successfully",
        proxy=proxy
    )

@app.get("/destroy", tags=["Proxy Management"], response_model=ProxyList)
def remove_proxy_list():
    """
    Get a list of proxies scheduled for deletion.
    
    Returns:
        ProxyList: A list of proxies queued for deletion with metadata
    """
    proxies = [create_proxy_address(ip) for ip in delete_queue]
    return ProxyList(
        total=len(proxies),
        proxies=proxies
    )

@app.delete("/destroy", tags=["Proxy Management"], response_model=ProxyResponse)
async def remove_proxy(ip_address: str):
    """
    Schedule a proxy for deletion.
    
    Args:
        ip_address: The IP address of the proxy to be deleted
        
    Returns:
        ProxyResponse: Confirmation message with proxy details
        
    Raises:
        HTTPException: If the IP address is invalid or not found
    """
    try:
        proxy = create_proxy_address(ip_address)
        delete_queue.add(str(proxy.ip))
        return ProxyResponse(
            message=f"Proxy scheduled for deletion",
            proxy=proxy
        )
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid IP address format"
        )

@app.get("/restart", tags=["Proxy Management"], response_model=ProxyList)
def restart_proxy_list():
    """
    Get a list of proxies scheduled for restart.
    
    Returns:
        ProxyList: A list of proxies queued for restart with metadata
    """
    proxies = [create_proxy_address(ip) for ip in restart_queue]
    return ProxyList(
        total=len(proxies),
        proxies=proxies
    )

@app.delete("/restart", tags=["Proxy Management"], response_model=ProxyResponse)
async def restart_proxy(ip_address: str):
    """
    Schedule a proxy for restart.
    
    Args:
        ip_address: The IP address of the proxy to be restarted
        
    Returns:
        ProxyResponse: Confirmation message with proxy details
        
    Raises:
        HTTPException: If the IP address is invalid or not found
    """
    try:
        proxy = create_proxy_address(ip_address)
        restart_queue.add(str(proxy.ip))
        return ProxyResponse(
            message=f"Proxy scheduled for restart",
            proxy=proxy
        )
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid IP address format"
        )

# Add new Pydantic models for providers
class ProviderScaling(BaseModel):
    min_scaling: int = Field(ge=0, default=0)
    max_scaling: int = Field(ge=0, default=0)

# Provider instance model for multi-instance support
class ProviderInstance(BaseModel):
    enabled: bool
    ips: List[str] = []
    scaling: ProviderScaling
    size: Optional[str] = None  # Made optional, some providers use different naming
    plan: Optional[str] = None  # For Vultr provider
    region: Optional[str] = None
    location: Optional[str] = None
    datacenter: Optional[str] = None
    zone: Optional[str] = None
    image_project: Optional[str] = None
    image_family: Optional[str] = None
    ami: Optional[str] = None
    os_id: Optional[int] = None  # For Vultr provider
    spot: Optional[bool] = None
    display_name: Optional[str] = None
    project: Optional[str] = None

class BaseProvider(BaseModel):
    enabled: bool = False
    ips: List[str] = Field(default_factory=list)
    region: str = ""
    size: Optional[str] = ""
    image: Optional[str] = ""
    scaling: ProviderScaling = Field(default_factory=lambda: ProviderScaling())
    instances: Dict[str, ProviderInstance] = Field(default_factory=dict)

class DigitalOceanProvider(BaseProvider):
    region: str

class AWSProvider(BaseProvider):
    region: Optional[str] = ""
    ami: Optional[str] = ""
    spot: bool = False

class GCPProvider(BaseProvider):
    zone: str
    image_project: str
    image_family: str

class HetznerProvider(BaseProvider):
    location: Optional[str] = None
    datacenter: Optional[str] = None

class ProviderList(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    providers: Dict[str, BaseProvider]

class ProviderResponse(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    message: str
    provider: Dict[str, Any]
    instances: Dict[str, Any] = Field(default_factory=dict)

# Update ProviderInstanceResponse model for instance-specific responses
class ProviderInstanceResponse(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    message: str
    provider: str
    instance: str
    config: ProviderInstance

def get_provider_model(provider_name: str, provider_config: Dict) -> BaseProvider:
    """
    Get the appropriate Pydantic model for a provider based on the provider name.
    
    Args:
        provider_name: The name of the provider
        provider_config: The provider configuration
        
    Returns:
        A provider model instance
    """
    # Extract instances separately from the config to handle it correctly
    instances_dict = {}
    if "instances" in provider_config:
        for instance_name, instance_config in provider_config["instances"].items():
            # Ensure the scaling is a dict for the instance
            if isinstance(instance_config.get("scaling"), ProviderScaling):
                instance_config["scaling"] = {
                    "min_scaling": instance_config["scaling"].min_scaling,
                    "max_scaling": instance_config["scaling"].max_scaling
                }
            instances_dict[instance_name] = ProviderInstance(**instance_config)
    
    # Create a shallow copy to avoid modifying the original
    config_copy = provider_config.copy()
    
    # Remove instances from the copy to avoid duplication
    if "instances" in config_copy:
        del config_copy["instances"]
    
    # Ensure the scaling is a dict
    if isinstance(config_copy.get("scaling"), ProviderScaling):
        config_copy["scaling"] = {
            "min_scaling": config_copy["scaling"].min_scaling,
            "max_scaling": config_copy["scaling"].max_scaling
        }
    
    # Get the appropriate provider model
    if provider_name == "digitalocean":
        # For DigitalOcean, ensure region is set (required by model)
        if "region" not in config_copy and "instances" in provider_config and "default" in provider_config["instances"]:
            config_copy["region"] = provider_config["instances"]["default"].get("region", "")
        provider_model = DigitalOceanProvider(**config_copy, instances=instances_dict)
    elif provider_name == "aws":
        # For AWS, ensure region and ami are set (required by model)
        if "region" not in config_copy and "instances" in provider_config and "default" in provider_config["instances"]:
            config_copy["region"] = provider_config["instances"]["default"].get("region", "")
        if "ami" not in config_copy and "instances" in provider_config and "default" in provider_config["instances"]:
            config_copy["ami"] = provider_config["instances"]["default"].get("ami", "")
        provider_model = AWSProvider(**config_copy, instances=instances_dict)
    elif provider_name == "gcp":
        provider_model = GCPProvider(**config_copy, instances=instances_dict)
    elif provider_name == "hetzner":
        provider_model = HetznerProvider(**config_copy, instances=instances_dict)
    else:
        provider_model = BaseProvider(**config_copy, instances=instances_dict)
    
    return provider_model

class AuthSettings(BaseModel):
    username: str
    password: str
    auth_enabled: bool = True

@app.get("/auth", tags=["Authentication"], response_model=AuthSettings)
def get_auth_settings():
    """
    Get the current authentication settings.
    
    Returns:
        AuthSettings: The current username and password configuration
    """
    return AuthSettings(
        username=settings.config["auth"]["username"],
        password=settings.config["auth"]["password"],
        auth_enabled=not settings.config["no_auth"]
    )

class ProviderUpdateRequest(BaseModel):
    min_scaling: int = Field(ge=0, description="Minimum number of proxy instances")
    max_scaling: int = Field(ge=0, description="Maximum number of proxy instances")

    @field_validator('max_scaling')
    @classmethod
    def max_scaling_must_be_greater_than_min(cls, v, info):
        values = info.data
        if 'min_scaling' in values and v < values['min_scaling']:
            raise ValueError('max_scaling must be greater than or equal to min_scaling')
        return v

@app.get("/providers", tags=["Provider Management"], response_model=ProviderList)
def providers():
    """
    Get configuration and status for all providers.
    
    Returns:
        ProviderList: Configuration and status for all providers, excluding sensitive information.
    """
    providers_data = {}
    for name, config in settings.config["providers"].items():
        provider_config = config.copy()
        provider_config.pop("secrets", None)
        providers_data[name] = get_provider_model(name, provider_config)
    
    return ProviderList(
        providers=providers_data
    )

@app.get("/providers/{provider}", tags=["Provider Management"], response_model=ProviderResponse)
async def get_provider(provider: str):
    """
    Get configuration and status for a provider.
    
    Args:
        provider: The name of the provider (digitalocean, aws, gcp, hetzner, azure)
        
    Returns:
        ProviderResponse: Provider configuration and status with metadata
        
    Raises:
        HTTPException: If the provider is not found
    """
    if provider not in settings.config["providers"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found"
        )

    # Get the provider configuration directly
    provider_config = settings.config["providers"][provider]
    
    # Extract instances for top-level inclusion
    instances = provider_config.get("instances", {})
    
    # Create the exact expected response format without using models
    provider_response = {
        "enabled": provider_config.get("enabled", False),
        "ips": provider_config.get("ips", []),
        "scaling": {
            "min_scaling": provider_config.get("scaling", {}).get("min_scaling", 0),
            "max_scaling": provider_config.get("scaling", {}).get("max_scaling", 0)
        },
        "size": provider_config.get("size", ""),
        "region": provider_config.get("region", "")
    }
    
    # Return the provider configuration
    return {
        "message": f"Provider '{provider}' configuration retrieved successfully",
        "metadata": Metadata().model_dump(),
        "provider": provider_response,
        "instances": instances
    }

@app.patch("/providers/{provider}", tags=["Provider Management"], response_model=ProviderResponse)
def configure(
    provider: str,
    update: ProviderUpdateRequest
):
    """
    Update scaling configuration for the default instance of a provider.
    
    Args:
        provider: The name of the provider (digitalocean, aws, gcp, hetzner, azure)
        update: The scaling configuration to update
        
    Returns:
        ProviderResponse: Updated provider configuration with metadata
        
    Raises:
        HTTPException: If the provider is not found
    """
    if provider not in settings.config["providers"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found"
        )

    # If scaling is a dict, update directly
    if isinstance(settings.config["providers"][provider]["instances"]["default"]["scaling"], dict):
        settings.config["providers"][provider]["instances"]["default"]["scaling"]["min_scaling"] = update.min_scaling
        settings.config["providers"][provider]["instances"]["default"]["scaling"]["max_scaling"] = update.max_scaling
    else:
        # Create a new ProviderScaling object
        settings.config["providers"][provider]["instances"]["default"]["scaling"] = {
            "min_scaling": update.min_scaling,
            "max_scaling": update.max_scaling
        }
    
    # Update top-level scaling for backward compatibility
    if isinstance(settings.config["providers"][provider]["scaling"], dict):
        settings.config["providers"][provider]["scaling"]["min_scaling"] = update.min_scaling
        settings.config["providers"][provider]["scaling"]["max_scaling"] = update.max_scaling
    else:
        settings.config["providers"][provider]["scaling"] = {
            "min_scaling": update.min_scaling,
            "max_scaling": update.max_scaling
        }
    
    # Get provider config
    provider_config = settings.config["providers"][provider]
    
    # Extract instances for top-level inclusion
    instances = provider_config.get("instances", {})
    
    # Create the exact expected response format without using models
    provider_response = {
        "enabled": provider_config.get("enabled", False),
        "ips": provider_config.get("ips", []),
        "scaling": {
            "min_scaling": update.min_scaling,
            "max_scaling": update.max_scaling
        },
        "size": provider_config.get("size", ""),
        "region": provider_config.get("region", "")
    }
    
    # Return the response with only the specific fields
    return {
        "metadata": Metadata().model_dump(),
        "message": f"Provider '{provider}' scaling configuration updated successfully",
        "provider": provider_response,
        "instances": instances
    }

@app.get("/providers/{provider}/{instance}", tags=["Provider Management"], response_model=ProviderInstanceResponse)
def get_provider_instance(provider: str, instance: str):
    """
    Get configuration and status for a specific provider instance.
    
    Args:
        provider: The name of the provider (digitalocean, aws, gcp, hetzner)
        instance: The name of the instance
        
    Returns:
        ProviderInstanceResponse: Provider instance configuration and status with metadata
        
    Raises:
        HTTPException: If the provider or instance is not found
    """
    if provider not in settings.config["providers"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found"
        )
    
    if instance not in settings.config["providers"][provider]["instances"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' instance '{instance}' not found"
        )

    instance_config = settings.config["providers"][provider]["instances"][instance].copy()
    instance_config.pop("secrets", None)
    
    return ProviderInstanceResponse(
        message=f"Provider '{provider}' instance '{instance}' configuration retrieved successfully",
        provider=provider,
        instance=instance,
        config=ProviderInstance(**instance_config)
    )

@app.patch("/providers/{provider}/{instance}", tags=["Provider Management"], response_model=ProviderInstanceResponse)
def configure_instance(
    provider: str,
    instance: str,
    update: ProviderUpdateRequest
):
    """
    Update scaling configuration for a specific instance of a provider.
    
    Args:
        provider: The name of the provider (digitalocean, aws, gcp, hetzner)
        instance: The name of the instance
        update: The scaling configuration to update
        
    Returns:
        ProviderInstanceResponse: Updated provider instance configuration with metadata
        
    Raises:
        HTTPException: If the provider or instance is not found
    """
    if provider not in settings.config["providers"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found"
        )
    
    if instance not in settings.config["providers"][provider]["instances"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' instance '{instance}' not found"
        )
    
    # If scaling is a dict, update directly
    if isinstance(settings.config["providers"][provider]["instances"][instance]["scaling"], dict):
        settings.config["providers"][provider]["instances"][instance]["scaling"]["min_scaling"] = update.min_scaling
        settings.config["providers"][provider]["instances"][instance]["scaling"]["max_scaling"] = update.max_scaling
    else:
        # Create a new scaling dictionary
        settings.config["providers"][provider]["instances"][instance]["scaling"] = {
            "min_scaling": update.min_scaling,
            "max_scaling": update.max_scaling
        }
    
    # Update top-level scaling for backward compatibility if this is the default instance
    if instance == "default":
        if isinstance(settings.config["providers"][provider]["scaling"], dict):
            settings.config["providers"][provider]["scaling"]["min_scaling"] = update.min_scaling
            settings.config["providers"][provider]["scaling"]["max_scaling"] = update.max_scaling
        else:
            settings.config["providers"][provider]["scaling"] = {
                "min_scaling": update.min_scaling,
                "max_scaling": update.max_scaling
            }
    
    instance_config = settings.config["providers"][provider]["instances"][instance].copy()
    instance_config.pop("secrets", None)
    
    return ProviderInstanceResponse(
        message=f"Provider '{provider}' instance '{instance}' scaling configuration updated successfully",
        provider=provider,
        instance=instance,
        config=ProviderInstance(**instance_config)
    )

# Rolling Deployment Models
class RollingDeploymentConfig(BaseModel):
    enabled: bool = Field(description="Whether rolling deployment is enabled")
    min_available: int = Field(ge=0, description="Minimum number of proxies to keep available during recycling")
    batch_size: int = Field(ge=1, description="Maximum number of proxies to recycle simultaneously")

class RollingDeploymentStatus(BaseModel):
    healthy: int = Field(description="Number of healthy proxies")
    pending: int = Field(description="Number of pending proxies")
    pending_recycle: int = Field(description="Number of proxies pending recycling")
    recycling: int = Field(description="Number of proxies currently being recycled")
    last_update: str = Field(description="Last update timestamp")
    healthy_ips: List[str] = Field(description="List of healthy proxy IPs")
    pending_recycle_ips: List[str] = Field(description="List of IPs pending recycling")
    recycling_ips: List[str] = Field(description="List of IPs currently being recycled")

class RollingDeploymentResponse(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    message: str
    config: RollingDeploymentConfig
    status: Dict[str, RollingDeploymentStatus] = Field(description="Status by provider/instance")

@app.get("/rolling", tags=["Rolling Deployment"], response_model=RollingDeploymentResponse)
def get_rolling_deployment_status():
    """
    Get the current rolling deployment configuration and status.
    
    Returns:
        RollingDeploymentResponse: Current rolling deployment configuration and status
    """
    config = RollingDeploymentConfig(
        enabled=settings.config["rolling_deployment"]["enabled"],
        min_available=settings.config["rolling_deployment"]["min_available"],
        batch_size=settings.config["rolling_deployment"]["batch_size"]
    )
    
    raw_status = rolling_manager.get_recycling_status()
    status = {}
    for key, data in raw_status.items():
        status[key] = RollingDeploymentStatus(**data)
    
    return RollingDeploymentResponse(
        message="Rolling deployment status retrieved successfully",
        config=config,
        status=status
    )

@app.patch("/rolling", tags=["Rolling Deployment"], response_model=RollingDeploymentResponse)
def update_rolling_deployment_config(update: RollingDeploymentConfig):
    """
    Update the rolling deployment configuration.
    
    Args:
        update: New rolling deployment configuration
        
    Returns:
        RollingDeploymentResponse: Updated configuration and current status
    """
    # Update configuration
    settings.config["rolling_deployment"]["enabled"] = update.enabled
    settings.config["rolling_deployment"]["min_available"] = update.min_available
    settings.config["rolling_deployment"]["batch_size"] = update.batch_size
    
    # Get current status
    raw_status = rolling_manager.get_recycling_status()
    status = {}
    for key, data in raw_status.items():
        status[key] = RollingDeploymentStatus(**data)
    
    return RollingDeploymentResponse(
        message="Rolling deployment configuration updated successfully",
        config=update,
        status=status
    )

@app.get("/rolling/{provider}", tags=["Rolling Deployment"], response_model=RollingDeploymentResponse)
def get_provider_rolling_status(provider: str):
    """
    Get rolling deployment status for a specific provider.
    
    Args:
        provider: The name of the provider
        
    Returns:
        RollingDeploymentResponse: Rolling deployment status for the provider
        
    Raises:
        HTTPException: If the provider is not found
    """
    if provider not in settings.config["providers"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found"
        )
    
    config = RollingDeploymentConfig(
        enabled=settings.config["rolling_deployment"]["enabled"],
        min_available=settings.config["rolling_deployment"]["min_available"],
        batch_size=settings.config["rolling_deployment"]["batch_size"]
    )
    
    raw_status = rolling_manager.get_recycling_status(provider=provider)
    status = {}
    for key, data in raw_status.items():
        status[key] = RollingDeploymentStatus(**data)
    
    return RollingDeploymentResponse(
        message=f"Rolling deployment status for '{provider}' retrieved successfully",
        config=config,
        status=status
    )

@app.get("/rolling/{provider}/{instance}", tags=["Rolling Deployment"], response_model=RollingDeploymentResponse)
def get_instance_rolling_status(provider: str, instance: str):
    """
    Get rolling deployment status for a specific provider instance.
    
    Args:
        provider: The name of the provider
        instance: The name of the instance
        
    Returns:
        RollingDeploymentResponse: Rolling deployment status for the instance
        
    Raises:
        HTTPException: If the provider or instance is not found
    """
    if provider not in settings.config["providers"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found"
        )
    
    if instance not in settings.config["providers"][provider]["instances"]:
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' instance '{instance}' not found"
        )
    
    config = RollingDeploymentConfig(
        enabled=settings.config["rolling_deployment"]["enabled"],
        min_available=settings.config["rolling_deployment"]["min_available"],
        batch_size=settings.config["rolling_deployment"]["batch_size"]
    )
    
    raw_status = rolling_manager.get_recycling_status(provider=provider, instance=instance)
    status = {}
    for key, data in raw_status.items():
        status[key] = RollingDeploymentStatus(**data)
    
    return RollingDeploymentResponse(
        message=f"Rolling deployment status for '{provider}/{instance}' retrieved successfully",
        config=config,
        status=status
    )

if __name__ == "__main__":
    main()

