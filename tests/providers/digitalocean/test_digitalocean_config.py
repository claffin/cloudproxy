from cloudproxy.providers.digitalocean.config import set_auth


def test_set_auth():
    assert set_auth() == True
