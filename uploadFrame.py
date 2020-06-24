import json

print("uploadFrame function")


def gettoken_handler(event, context):
    time = event["queryStringParams"]["time"]
    path = event["queryStringParams"]["path"]
    camera_id = event["queryStringParams"]["camera_id"]
    tag = event["queryStringParams"]["tag"]
    resp = {
        "message": "Frame has been uploaded!"
    }
    respObj = {
        "statuscode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp)
    }
    return respObj
