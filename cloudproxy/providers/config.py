import os


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def set_proxy(username, password, allowed_ip, proxy_stealth):
    with open(os.path.join(__location__, "user_data.sh")) as file:
        filedata = file.read()
        if username != "changeme":
            filedata = filedata.replace("username", username)
            filedata = filedata.replace("password", password)
        else:
            filedata = filedata.replace("BasicAuth username password", "#BasicAuth username password")
        if len(allowed_ip) > 0:
            filedata = filedata.replace("#Allow 127.0.0.1", "Allow " + allowed_ip + "\/24")
        if proxy_stealth:
            filedata = filedata.replace("DisableViaHeader No", "DisableViaHeader Yes")
    return filedata