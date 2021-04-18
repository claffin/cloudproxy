from cloudproxy.providers.digitalocean.main import do_deployment, do_check_alive


def test_do_deployment():
    assert type(do_deployment()) is int

def test_do_check_alive():
    assert type(do_check_alive()) is list