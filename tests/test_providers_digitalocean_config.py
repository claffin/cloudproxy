import os

from cloudproxy.providers.config import set_auth
from cloudproxy.providers import settings

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def test_set_auth():
    with open(os.path.join(__location__, 'test_user_data.sh')) as file:
        filedata = file.read()
    settings.config["no_auth"] = False
    assert set_auth("testingusername", "testinguserpassword") == filedata
    