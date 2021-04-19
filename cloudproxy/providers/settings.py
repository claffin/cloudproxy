import os

from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("DIGITALOCEAN_ACCESS_TOKEN")
min_scaling = os.environ.get("DIGITALOCEAN_MIN_SCALE", 1)
max_scaling = os.environ.get("DIGITALOCEAN_MAX_SCALE", 1)
username = os.environ.get("USERNAME", "proxy")
password = os.environ.get("PASSWORD")

def init():
    global ip_list
    ip_list = []