import os
import random
import sys
import re
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Set, Dict

import uvicorn
from loguru import logger
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, IPvAnyAddress, Field, validator

from cloudproxy.providers import settings
from cloudproxy.providers.settings import delete_queue, restart_queue

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

app.mount("/ui", StaticFiles(directory=(os.path.join(__location__, "../cloudproxy-ui/dist")), html=True), name="static")
app.mount("/css", StaticFiles(directory=(os.path.join(__location__, "../cloudproxy-ui/dist/css")), html=True), name="cssstatic")
app.mount("/js", StaticFiles(directory=(os.path.join(__location__, "../cloudproxy-ui/dist/js"))), name="jsstatic")

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
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProxyAddress(BaseModel):
    ip: IPvAnyAddress
    port: int = 8899
    auth_enabled: bool = True
    url: Optional[str] = None

    @validator('url', always=True)
    def set_url(cls, v, values):
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
    for provider in ['digitalocean', 'aws', 'gcp', 'hetzner']:
        if settings.config["providers"][provider]["ips"]:
            for ip in settings.config["providers"][provider]["ips"]:
                if ip not in delete_queue and ip not in restart_queue:
                    ip_list.append(create_proxy_address(ip))
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
    min_scaling: int = Field(ge=0)
    max_scaling: int = Field(ge=0)

class Provider(BaseModel):
    enabled: bool
    ips: List[str] = []
    scaling: ProviderScaling
    size: str
    region: Optional[str] = None
    location: Optional[str] = None
    zone: Optional[str] = None
    datacenter: Optional[str] = None
    ami: Optional[str] = None
    spot: Optional[bool] = None
    image_project: Optional[str] = None
    image_family: Optional[str] = None

class ProviderList(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    providers: Dict[str, Provider]

class ProviderResponse(BaseModel):
    metadata: Metadata = Field(default_factory=Metadata)
    message: str
    provider: Provider

class ProviderUpdateRequest(BaseModel):
    min_scaling: int = Field(ge=0, description="Minimum number of proxy instances")
    max_scaling: int = Field(ge=0, description="Maximum number of proxy instances")

    @validator('max_scaling')
    def max_scaling_must_be_greater_than_min(cls, v, values):
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
        providers_data[name] = provider_config
    
    return ProviderList(
        providers=providers_data
    )

@app.get("/providers/{provider}", tags=["Provider Management"], response_model=ProviderResponse)
def get_provider(provider: str):
    """
    Get configuration and status for a specific provider.
    
    Args:
        provider: The name of the provider (digitalocean, aws, gcp, hetzner)
        
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

    provider_config = settings.config["providers"][provider].copy()
    provider_config.pop("secrets", None)
    
    return ProviderResponse(
        message=f"Provider '{provider}' configuration retrieved successfully",
        provider=provider_config
    )

@app.patch("/providers/{provider}", tags=["Provider Management"], response_model=ProviderResponse)
def configure(
    provider: str,
    update: ProviderUpdateRequest
):
    """
    Update scaling configuration for a specific provider.
    
    Args:
        provider: The name of the provider (digitalocean, aws, gcp, hetzner)
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

    settings.config["providers"][provider]["scaling"]["min_scaling"] = update.min_scaling
    settings.config["providers"][provider]["scaling"]["max_scaling"] = update.max_scaling
    
    provider_config = settings.config["providers"][provider].copy()
    provider_config.pop("secrets", None)
    
    return ProviderResponse(
        message=f"Provider '{provider}' scaling configuration updated successfully",
        provider=provider_config
    )

if __name__ == "__main__":
    main()

