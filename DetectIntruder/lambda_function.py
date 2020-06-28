import boto3
import json
import base64
import os
from boto3.dynamodb.conditions import Key

print("DetectIntruder function using detected image being uploaded into S3")


def is_human(photo):
    client = boto3.client('rekognition', region_name='eu-west-1')
    # df = base64.b64decode(ef)
    print(os.environ['BUCKET'])
    response = client.detect_labels(
        Image={
            # "Bytes":df
            'S3Object': {
                'Bucket': os.environ['BUCKET'],
                'Name': photo
            }
        },
        MaxLabels=10,
        MinConfidence=75
    )
    # check to see if human is identified and has confidence > 75
    is_human = False
    for label in response['Labels']:
        if label['Name'] == "Person" and label['Confidence'] > 75:
            print(label['Name'] + "/" + str(label['Confidence']))
            is_human = True
    return is_human


def get_training_locations(uuid):
    # 1.1 Using the RESOURCE and get single item based on UserID
    # dynamodb = boto3.client('dynamodb',region_name='af-south-1')
    # table = dynamodb.Table('UserData')
    # response = table.get_item(Key={'UserID':uuid})

    # 1.2 Using the RESOURCE and query the table for the UserID eq to given uuid
    # response = table.query(KeyConditionExpression=Key('UserID').eq(uuid))

    # 2. Using the CLIENT and getting a single item based on the UserID key
    dynamodb = boto3.client('dynamodb')
    response = dynamodb.get_item(
        TableName="UserData",
        Key={
            "UserID": {
                "S": uuid
            }
        }
    )
    print(response)
    if 'Item' in response:
        return response['Item']
    return None


def is_owner(training_image, detected_image, bucket="watchdog.uservideocontent"):
    pass


def lambda_handler(event, context):
    detected_image = event["image"]
    uuid = event["uuid"]

    is_human(detected_image)
    # face has been detected in detected image - now compare it to other images from user uploads

    # is_intruder = True
    # locations = get_training_locations(event["uuid"])
    # if locations is not None:
    #     for location in locations:
    #         if is_owner(location, detected_image):
    #           is_intruder = False
    #           break

    # if is_intruder:
    # pass onto SNS lambda for notifying user!
    # response = "intruder detected, send to notificaiton SNS"
    # else:
    #     response = "intruder not detected"

    resp = {
        "response": response
    }
    respObj = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp)
    }

    return respObj
