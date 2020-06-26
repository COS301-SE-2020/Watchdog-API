import json
import boto3
from boto3.dynamodb.conditions import Key
print("DetectIntruder function")


def lambda_handler(event, context, dynamodb = None):
    image_detected = event["queryStringParams"]["image_detected"]
    camera_detected_on = event["queryStringParams"]["camera_detected_on"]
    user_id = event["queryStringParams"]["user_id"]
    # upload_key = event["queryStringParameters"]["upload_key"]
    # folder = event["queryStringParameters"]["folder"]
    if not dynamodb:   # check_if_you_want_this_implementation. otherwise erase
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
        table = dynamodb.Table('Artefacts')
        response = table.query(
            KeyConditionExpression=Key('Videos').eq(camera_detected_on)
        )  # this fetches videos from the Artefacts table in dynamodb
    resp = {
        "message": "Detection!"
    }
    respObj = {
        "statuscode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp)
    }

    return respObj