#!/usr/bin/env python
import sys
from loguru import logger
from cloudproxy.providers import manager
from cloudproxy.main import start as start_api
# Importing settings ensures environment variables are loaded for standalone mode
from cloudproxy.providers import settings

if __name__ == "__main__":
    logger.info("Starting CloudProxy in standalone mode...")

    # Configuration is loaded from environment variables via settings.py import

    logger.info("Initializing background scheduler...")
    # Explicitly start the scheduler for standalone mode
    try:
        manager.init_schedule()
        logger.info("Scheduler initialized successfully.")
    except Exception as e:
        logger.exception("Failed to initialize scheduler.")
        sys.exit(1)  # Exit if scheduler fails

    logger.info("Starting API server...")
    # Start the FastAPI/Uvicorn server
    try:
        start_api()  # This function calls uvicorn.run
    except Exception as e:
        logger.exception("Failed to start API server.")
        sys.exit(1)  # Exit if API server fails 