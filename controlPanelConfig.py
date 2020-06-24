import json

print("controlPanelConfig function")


def gettoken_handler(event, context):
    privatekey = event["queryStringParams"]["privatekey"]
    ip_address = event["queryStringParams"]["ip_address"]
    broadcast_ip = event["queryStringParams"]["broadcast_ip"]
    physical_address = event["queryStringParams"]["physical_address"]
    cameras = event["queryStringParams"]["cameras"]
    resp = {}
    resp["message"] = "Control Panel has been configured!"

    respObj = {}
    respObj["statusCode"] = 200
    respObj["headers"] = {}
    respObj["headers"]["Content-Type"] = "application/json"
    respObj["body"] = json.dumps(resp)

    return respObj