import json

print("controlPanelConfig function")


def lambda_handler(event, context):
    privatekey = event["queryStringParams"]["privatekey"]
    ip_address = event["queryStringParams"]["ip_address"]
    broadcast_ip = event["queryStringParams"]["broadcast_ip"]
    physical_address = event["queryStringParams"]["physical_address"]
    cameras = event["queryStringParams"]["cameras"]
    resp = {
        "message": "Control Panel has been configured!"
    }
    respObj = {
        "statuscode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp)
    }

    return respObj
