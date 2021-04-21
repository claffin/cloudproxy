from cloudproxy.check import check_alive


def test_check_alive(mocker):
    mocker.patch(
        'cloudproxy.check.fetch_ip',
        return_value="192.1.1.1"
    )
    assert check_alive("192.1.1.1") == True
