import os
import random
import sys
import re

import uvicorn
import json
from loguru import logger
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uvicorn_loguru_integration import run_uvicorn_loguru
from cloudproxy.providers import settings
from cloudproxy.providers.settings import delete_queue

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.add("cloudproxy.log", rotation="20 MB")


def main():
    run_uvicorn_loguru(uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info"))


def get_ip_list():
    ip_list = []
    if settings.config["providers"]["digitalocean"]["ips"]:
        for ip in settings.config["providers"]["digitalocean"]["ips"]:
            ip_list.append(
                "http://"
                + settings.config["auth"]["username"]
                + ":"
                + settings.config["auth"]["password"]
                + "@"
                + ip
                + ":8899"
            )
    if settings.config["providers"]["aws"]["ips"]:
        for ip in settings.config["providers"]["aws"]["ips"]:
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


@app.get("/")
def read_root():
    return {"ips": get_ip_list()}


@app.get("/random")
def read_random():
    if not get_ip_list():
        return {}
    else:
        return {random.choice(get_ip_list())}


def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


@app.get("/destroy")
def remove_proxy_list():
    response = set_default(delete_queue)
    return JSONResponse(response)


@app.delete("/destroy")
def remove_proxy(ip_address: str):
    if re.findall(r"[0-9]+(?:\.[0-9]+){3}", ip_address):
        ip = re.findall(r"[0-9]+(?:\.[0-9]+){3}", ip_address)
        delete_queue.add(ip[0])
        return {"Proxy to be destroyed"}
    else:
        raise HTTPException(status_code=422, detail="IP not found")


@app.get("/providers")
def providers():
    settings_response = settings.config["providers"]
    for provider in settings_response:
        try:
            settings_response[provider].pop("secrets")
        except KeyError:
            pass
    return JSONResponse(settings_response)


@app.get("/providers/{provider}")
def providers(provider: str):
    if provider in settings.config["providers"]:
        response = settings.config["providers"][provider]
        if "secrets" in response:
            response.pop("secrets")
        return JSONResponse(response)
    else:
        raise HTTPException(status_code=404, detail="Provider not found")


@app.patch("/providers/{provider}")
def configure(provider: str, min_scaling: int, max_scaling: int):
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
