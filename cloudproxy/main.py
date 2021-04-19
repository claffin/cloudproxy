import os
import random
import sys

import uvicorn
from fastapi import FastAPI
from uvicorn_loguru_integration import run_uvicorn_loguru

from cloudproxy.providers import settings, manager

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
app = FastAPI()

settings.init()
manager.init_schedule()


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
    return {"ips": settings.ip_list}


@app.get("/random")
def read_root():
    if not settings.ip_list:
        return []
    else:
        return random.choice(settings.ip_list)


if __name__ == "__main__":
    main()
