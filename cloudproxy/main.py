import os
import random
import sys
import re
import logging

import uvicorn
from loguru import logger
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

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


def get_ip_list():
    ip_list = []
    for provider in ['digitalocean', 'aws', 'gcp', 'hetzner']:
        if settings.config["providers"][provider]["ips"]:
            for ip in settings.config["providers"][provider]["ips"]:
                if ip not in delete_queue and ip not in restart_queue:
                    if settings.config["no_auth"]:
                        ip_list.append("http://" + ip + ":8899")
                    else:
                        ip_list.append(
                            "http://"
                            + settings.config["auth"]["username"]
                            + ":"
                            + settings.config["auth"]["password"]
                            + "@"
                            + ip
                            + ":8899"
                        )
    return ip_list


@app.get("/", tags=["Proxies"])
def read_root():
    """
    Get a list of all available proxy servers.
    
    Returns:
        dict: A dictionary containing a list of proxy URLs with authentication credentials.
    """
    return {"ips": get_ip_list()}


@app.get("/random", tags=["Proxies"])
def read_random():
    """
    Get a random proxy server from the available pool.
    
    Returns:
        dict: A dictionary containing a single random proxy URL with authentication credentials.
    """
    if not get_ip_list():
        return {}
    else:
        return {random.choice(get_ip_list())}


def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


@app.get("/destroy", tags=["Proxy Management"])
def remove_proxy_list():
    """
    Get a list of proxies scheduled for deletion.
    
    Returns:
        list: A list of IP addresses that are queued for deletion.
    """
    response = set_default(delete_queue)
    return JSONResponse(response)


@app.delete("/destroy", tags=["Proxy Management"])
def remove_proxy(ip_address: str):
    """
    Schedule a proxy for deletion.
    
    Args:
        ip_address (str): The IP address of the proxy to be deleted.
        
    Returns:
        dict: A confirmation message that the proxy will be destroyed.
        
    Raises:
        HTTPException: If the IP address is invalid or not found.
    """
    if re.findall(r"[0-9]+(?:\.[0-9]+){3}", ip_address):
        ip = re.findall(r"[0-9]+(?:\.[0-9]+){3}", ip_address)
        delete_queue.add(ip[0])
        return {"Proxy <{}> to be destroyed".format(ip[0])}
    else:
        raise HTTPException(status_code=422, detail="IP not found")


@app.get("/restart", tags=["Proxy Management"])
def restart_proxy_list():
    """
    Get a list of proxies scheduled for restart.
    
    Returns:
        list: A list of IP addresses that are queued for restart.
    """
    response = set_default(restart_queue)
    return JSONResponse(response)


@app.delete("/restart", tags=["Proxy Management"])
def restart_proxy(ip_address: str):
    """
    Schedule a proxy for restart.
    
    Args:
        ip_address (str): The IP address of the proxy to be restarted.
        
    Returns:
        dict: A confirmation message that the proxy will be restarted.
        
    Raises:
        HTTPException: If the IP address is invalid or not found.
    """
    if re.findall(r"[0-9]+(?:\.[0-9]+){3}", ip_address):
        ip = re.findall(r"[0-9]+(?:\.[0-9]+){3}", ip_address)
        restart_queue.add(ip[0])
        return {"Proxy <{}> to be restarted".format(ip[0])}
    else:
        raise HTTPException(status_code=422, detail="IP not found")


@app.get("/providers", tags=["Provider Management"])
def providers():
    """
    Get configuration and status for all providers.
    
    Returns:
        dict: Provider configurations and current status, excluding sensitive information.
    """
    settings_response = settings.config["providers"]
    for provider in settings_response:
        try:
            settings_response[provider].pop("secrets")
        except KeyError:
            pass
    return JSONResponse(settings_response)


@app.get("/providers/{provider}", tags=["Provider Management"])
def providers(provider: str):
    """
    Get configuration and status for a specific provider.
    
    Args:
        provider (str): The name of the provider (digitalocean, aws, gcp, hetzner)
        
    Returns:
        dict: Provider configuration and current status, excluding sensitive information.
        
    Raises:
        HTTPException: If the provider is not found.
    """
    if provider in settings.config["providers"]:
        response = settings.config["providers"][provider]
        if "secrets" in response:
            response.pop("secrets")
        return JSONResponse(response)
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


@app.patch("/providers/{provider}", tags=["Provider Management"])
def configure(provider: str, min_scaling: int, max_scaling: int):
    """
    Update scaling configuration for a specific provider.
    
    Args:
        provider (str): The name of the provider (digitalocean, aws, gcp, hetzner)
        min_scaling (int): Minimum number of proxy instances
        max_scaling (int): Maximum number of proxy instances
        
    Returns:
        dict: Updated provider configuration, excluding sensitive information.
        
    Raises:
        HTTPException: If the provider is not found.
    """
    if provider in settings.config["providers"]:
        settings.config["providers"][provider]["scaling"]["min_scaling"] = min_scaling
        settings.config["providers"][provider]["scaling"]["max_scaling"] = max_scaling
        response = settings.config["providers"][provider]
        if "secrets" in response:
            response.pop("secrets")
        return JSONResponse(response)
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


if __name__ == "__main__":
    main()

