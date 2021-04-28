import uuid as uuid
import json
from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth
from scaleway.apis import ComputeAPI
from slumber.exceptions import HttpClientError

compute_api = ComputeAPI(
    auth_token=settings.config["providers"]["scaleway"]["secrets"]["access_token"]
)


def create_proxy():
    user_data = set_auth(
        settings.config["auth"]["username"], settings.config["auth"]["password"]
    )
    # try:
    #     res = compute_api.query().images.get()
    #     image = next(image for image in res["images"] if "Ubuntu 20.04" in image["name"])
    # except HttpClientError as exc:
    #     print(json.dumps(exc.response.json(), indent=2))
    # try:
    #     instance = compute_api.query().servers.post(
    #         {
    #             "project": settings.config["providers"]["scaleway"]["secrets"][
    #                 "project"
    #             ],
    #             "name": str(uuid.uuid1()),
    #             "commercial_type": "DEV1-M",
    #             "image": image['id'],
    #             "tags": ["cloudproxy"]
    #         }
    #     )
    # except HttpClientError as exc:
    #     print(json.dumps(exc.response.json(), indent=2))
    try:
        data = (
            compute_api.query()
            .servers("cb2412b2-d983-46be-9ead-9c33777cfdea")
            .user_data("cloud-init")
            .get()
        )
        print(data.decode())
        print(
            compute_api.query()
            .servers("cb2412b2-d983-46be-9ead-9c33777cfdea")
            .user_data("cloud-init")
            .patch()
        )
    except HttpClientError as exc:
        print(json.dumps(exc.response.json(), indent=2))
    return True


# def delete_proxy(droplet_id):
#     deleted =
#     return deleted
#
#
# def list_droplets():
#     my_droplets =
#     return my_droplets

create_proxy()
