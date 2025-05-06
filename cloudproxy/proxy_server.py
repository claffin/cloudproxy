import random
import asyncio
from typing import List, Optional
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from starlette.background import BackgroundTask
from starlette.responses import StreamingResponse

from cloudproxy.providers import settings
from cloudproxy.main import get_ip_list
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, status

class ProxySelector:
    def __init__(self, strategy="random"):
        self.strategy = strategy
        self.current_index = 0
        self.usage_count = {}

    def select_proxy(self, proxies):
        if not proxies:
            return None

        if self.strategy == "random":
            return random.choice(proxies)
        elif self.strategy == "round-robin":
            proxy = proxies[self.current_index % len(proxies)]
            self.current_index += 1
            return proxy
        elif self.strategy == "least-used":
            # Select the proxy with the least usage count
            for proxy in proxies:
                if proxy.ip not in self.usage_count:
                    self.usage_count[proxy.ip] = 0

            selected = min(proxies, key=lambda p: self.usage_count.get(p.ip, 0))
            self.usage_count[selected.ip] = self.usage_count.get(selected.ip, 0) + 1
            return selected
        else:
            # Default to random
            return random.choice(proxies)

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = settings.config["auth"]["username"]
    correct_password = settings.config["auth"]["password"]

    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials


proxy_app = FastAPI(title="CloudProxy Proxy Server")

# Initialize ProxySelector with the configured strategy
proxy_selector = ProxySelector(strategy=settings.config["proxy_of_proxies"]["selection_strategy"])

@proxy_app.middleware("http")
async def proxy_middleware(request: Request, call_next, credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    # Get available proxies
    proxies = get_ip_list()
    if not proxies:
        return Response(
            content="No proxies available",
            status_code=503,
            media_type="text/plain"
        )

    # Select a proxy using the configured strategy
    selected_proxy = proxy_selector.select_proxy(proxies)
    if not selected_proxy:
         return Response(
            content="No proxies available for selection",
            status_code=503,
            media_type="text/plain"
        )
    proxy_url = selected_proxy.url

    # Build target URL
    path = request.url.path
    query_string = request.url.query.decode()
    target_url = f"{proxy_url}{path}"
    if query_string:
        target_url = f"{target_url}?{query_string}"

    # Forward the request
    client = httpx.AsyncClient(follow_redirects=True)

    try:
        # Get request body
        body = await request.body()

        # Forward the request with the same method, headers, and body
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=request.headers.raw,
            content=body,
            timeout=60.0
        )

        # Return the response
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            background=BackgroundTask(client.aclose)
        )
    except Exception as e:
        await client.aclose()
        return Response(
            content=f"Error forwarding request: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )