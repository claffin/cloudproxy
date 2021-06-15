import os


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def set_auth(username, password):
    with open(os.path.join(__location__, "user_data.sh")) as file:
        filedata = file.read()
        filedata = filedata.replace("username", username)
        filedata = filedata.replace("password", password)
    return filedata
