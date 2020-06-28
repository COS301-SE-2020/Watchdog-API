import json
import boto3
import hashlib

print("controlPanelConfig function")


# helper functions

# POST to configure either the HCP or Camera
def creation(event, user_record):
    # get specific function requested
    try:
        response = None
        function = event["queryStringParameters"]["function"]
        print(function)
        if function is None:
            raise Exception("Please specify what fucntion you want to create using 'route' in body")

        if function is "HCP":
            print("Inserting Credentials for the HCP into User table")
            Item = {}
            response = 200, {
                "Successfully inserted into the HCP"
            }

        elif function is "Camera":
            pass


    except Exception as e:
        response = 501, {
            "Exception": e
        }
    return response


def lambda_handler(event, context, dynamodb=None):
    # authentication
    # if event["queryStringParameters"]["function"] is None:
    # response = f"Could not find the target function {target} that you were looking for"
    # statuscode = 204
    # if event["queryStringParameters"]["uuid"] is None:
    # pass
    # if event["queryStringParameters"]["type"] is None:
    # pass

    # functionality

    # TODO: Hash the values necessary to get unique record in UserData class
    # uuid = event["queryStringParameters"]["uuid"]
    # print(f"current event: {event}")

    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
    user_data_tbl = dynamodb.Table("UserData")
    # user_record = user_data_tbl.query(KeyConditionExpression=Key('UserID').eq(uuid))
    user_record = user_data_tbl.scan()
    user_record = json.loads(user_record)
    # print(f"Record: {user_record}")

    try:
        # functionality
        # target = event["queryStringParameters"]["target"]
        target = "update"
        if target is "create":
            statuscode, response = creation(event, user_record)
        if target is "retreieve":
            pass
        if target is "update":
            pass
        if target is "delete":
            pass

        # response = f"Could not find the target function {target} that you were looking for"
        statuscode = 200
    except Exception as e:
        # print(f"Exception! {e}")
        response = e
        statuscode = 501
        response = user_record
    respObj = {
        "statuscode": statuscode,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(response)
    }

    # user_id = event["queryStringParams"]["user_id"]
    print(respObj)
    return respObj
