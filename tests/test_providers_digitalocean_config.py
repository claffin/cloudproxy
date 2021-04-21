import os

from cloudproxy.providers.digitalocean.config import set_auth

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def test_set_auth():
    with open(os.path.join(__location__, 'test_user_data.sh')) as file:
        filedata = file.read()
    assert set_auth("testingusername", "testingusername") == filedata
