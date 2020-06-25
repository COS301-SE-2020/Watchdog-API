import json

print("getCameras function")


def getcamera_handler(event, context):
    username = event["queryStringParams"]["username"]
    token = event["queryStringParams"]["usertoken"]

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
        "body": json.dumps(resp)
    }

    return respObj
