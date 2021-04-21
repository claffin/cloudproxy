import os
import random
import sys
import re

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from uvicorn_loguru_integration import run_uvicorn_loguru
from cloudproxy.providers import settings
from cloudproxy.providers.settings import delete_queue

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
app = FastAPI()


def main():
    run_uvicorn_loguru(
        uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    )


@app.get("/")
def read_root():
    ip_list = []
    if settings.config["providers"]["digitalocean"]["ips"]:
        for ip in settings.config["providers"]["digitalocean"]["ips"]:
            ip_list.append(ip)
    return {"ips": ip_list}


@app.get("/random")
def read_random():
    ip_list = []
    if settings.config["providers"]["digitalocean"]["ips"]:
        for ip in settings.config["providers"]["digitalocean"]["ips"]:
            ip_list.append(ip)
    if not ip_list:
        return {}
    else:
        return random.choice(ip_list)


@app.delete("/remove")
def remove_proxy(ip_address: str):
    if re.findall( r'[0-9]+(?:\.[0-9]+){3}', ip_address):
        ip = re.findall(r'[0-9]+(?:\.[0-9]+){3}', ip_address)
        delete_queue.append(ip[0])
        return {"Success"}
    else:
        raise HTTPException(status_code=422, detail="IP not found")


@app.get("/providers/{provider}")
def providers(provider: str):
    if provider in settings.config["providers"]:
        response = settings.config["providers"][provider]
        if "access_token" in response:
            response.pop("access_token")
        return JSONResponse(response)
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


@app.patch("/providers/{provider}")
def configure(provider: str, min_scaling: int, max_scaling: int):
    if provider in settings.config["providers"]:
        settings.config["providers"][provider]["scaling"]["min_scaling"] = min_scaling
        settings.config["providers"][provider]["scaling"]["max_scaling"] = max_scaling
        response = settings.config["providers"][provider]
        if "access_token" in response:
            response.pop("access_token")
        return JSONResponse(response)
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


if __name__ == "__main__":
    main()
