from warrant.aws_srp import AWSSRP
import os
import requests
from random import randint
import json


BASE_URL = "https://b534kvo5c6.execute-api.af-south-1.amazonaws.com/testing/"
DATA_PATH = "watchdog-api/tests/data/"


def get_authentication():
    aws = AWSSRP(
        username="Test",
        password="Test@123",
        pool_id="eu-west-1_mQ0D78123",
        client_id="5bl2caob065vqodmm3sobp3k7d",
        pool_region="eu-west-1",
    )

    tokens = aws.authenticate_user()
    token = tokens["AuthenticationResult"]["IdToken"]
    print(token)
    return token


def test_add_identity():
    """
    Add profile to the users account
    """
    token = get_authentication()
    fn = "musk.jpeg"
    api_endpoint = BASE_URL + "identities/upload"
    response = requests.post(
        api_endpoint,
        params={"name": "Musk", "filename": str(randint(0, 600)) + "_" + fn},
        headers={"Authorization": token},
    )
    response = json.loads(response.text)
    with open(DATA_PATH + fn, "rb") as binary_object:
        files = {"file": (fn, binary_object)}
        response = requests.post(
            response["data"]["url"], data=response["data"]["fields"], files=files
        )
    assert response.status_code == 204


def test_delete_identity():
    """
    delete identity
    """
    token = get_authentication()
    api_endpoint = BASE_URL + "identities"
    response = requests.delete(
        api_endpoint,
        params={
            "index": 0,
        },
        headers={"Authorization": token},
    )
    response = json.loads(response.text)
