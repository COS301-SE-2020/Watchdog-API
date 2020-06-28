import json

print("getCameras function")


def lambda_handler(event, context):
    username = event["queryStringParameters"]["username"]
    token = event["queryStringParameters"]["usertoken"]

    print("the user name provided was " + username)
    print("the token provided was " + token)

    resp = {
        "ip_address": "192.168.0.1",
        "message": "IP address has been found!"
    }
    respObj = {
        "statuscode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": resp
    }

    return respObj