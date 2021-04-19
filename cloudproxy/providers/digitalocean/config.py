import os

from dotenv import load_dotenv

load_dotenv()
token = os.environ.get("DIGITALOCEAN_ACCESS_TOKEN")
min_scaling = os.environ.get("DIGITALOCEAN_MIN_SCALE", 1)
max_scaling = os.environ.get("DIGITALOCEAN_MAX_SCALE", 1)
username = os.environ.get("USERNAME", "proxy")
password = os.environ.get("PASSWORD")

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

def set_auth():
    file = open(os.path.join(__location__, 'user_data.sh'))
    replaced_content = ""
    # looping through the file
    for line in file:
        # stripping line break
        line = line.strip()
        # replacing the texts
        new_line = line.replace("USERNAME:PASSWORD", username + ":" + password)

        #concatenate the new string and add an end-line break
        replaced_content = replaced_content + new_line + "\n"

    # close the file
    file.close()
    # Open file in write mode
    write_file = open("user_data.sh", "w")

    write_file.write(replaced_content)
    # close the file
    write_file.close()
    return True
