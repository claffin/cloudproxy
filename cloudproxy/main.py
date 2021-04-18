from fastapi import FastAPI
from cloudproxy.providers import settings, manager
from uvicorn_loguru_integration import run_uvicorn_loguru
import uvicorn
import random

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
