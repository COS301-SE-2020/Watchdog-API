import json

print("getCameras function")


def getcamera_handler(event, context):
    username = event["queryStringParams"]["username"]
    token = event["queryStringParams"]["usertoken"]

    print("the user name provided was " + username)
    print("the token provided was " + token)

    resp = {}
    resp["ip_address"] = "192.168.0.1"
    resp["message"] = "IP address has been found!"

    respObj = {}
    respObj["statuscode"] = 200
    respObj["headers"] = {}
    respObj["headers"]["Content-Type"] = "application/json"
    respObj["body"] = json.dumps(resp)

    return respObj
