import boto3
import json


def lambda_handler(event, context):
    # Get the service client.
    s3 = boto3.client('s3')

    # Get request Parameters
    upload_key = event["queryStringParameters"]["upload_key"]
    folder = event["queryStringParameters"]["folder"]

    # Optional Args not implemented yet
    fields = None
    conditions = None

    # Set expiration
    expiration = 3600

    response = s3.generate_presigned_post('watchdog.uservideocontent', f'{folder}/{upload_key}', Fields=fields, Conditions=conditions, ExpiresIn=expiration)

    # Package Response
    respObj = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(response)
    }

    return respObj
