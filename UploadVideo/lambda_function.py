import json

print("UploadVideo function")


def lambda_handler(event, context):
    timestamp = event["queryStringParams"]["timestamp"]
    camera_id = event["queryStringParams"]["camera_id"]
    tag = event["queryStringParams"]["tag"]
    resp = {
        "message": "Video has been uploaded!"
    }
    respObj = {
        "statuscode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp)
    }

    return respObj