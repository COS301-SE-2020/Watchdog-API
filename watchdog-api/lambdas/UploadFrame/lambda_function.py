import json
import boto3
import os
from botocore.exceptions import ClientError
import datetime
import uuid


# Bundle the Response with an ERROR
def error(msg, extra={}):
    return {
            "status": "ERROR",
            "message": f'Encountered an Unexpected Error: {msg}',
            **extra
    }
    
# Bundle the response with an OK
def success(msg, extra={}):
    return {
        "status": "OK",
        "message": f'Operation Completed with Message: {msg}',
        "data": {**extra}
    }

def lambda_handler(event, context):
    # tag = event['queryStringParameters']['tag']
    user_id = event['requestContext']['authorizer']['claims']['sub']
    name = event['queryStringParameters']['name']
    timestamp = str(datetime.datetime.now().timestamp())
    filename = event['queryStringParameters']['filename']
    ext = filename.split(".")[-1]
    # key = os.environ['OBJECT_DIRECTORY'] + user_id+"_"+ str(hash(filename)) +"." + ext
    LENGTH_OF_UNIQUE_STRING = 6
    uniqueString = uuid.uuid4().hex[:LENGTH_OF_UNIQUE_STRING]
    # key = os.environ['OBJECT_DIRECTORY'] + filename
    key = f'{os.environ["OBJECT_DIRECTORY"]}{uniqueString}_{filename}'
    
    fields = {
        "x-amz-meta-uuid": user_id,
        "x-amz-meta-name": name,
        "x-amz-meta-timestamp": timestamp
    }
    
    # conditions = [{k:fields[k]} for k in fields]
    conditions = [
        {'x-amz-meta-uuid':user_id},
        {'x-amz-meta-name':name},
        {'x-amz-meta-timestamp':timestamp}    
    ]
    
    resp = {}
    print(key)
    try:
        s3 = boto3.client('s3', region_name='eu-west-1')
        resp = s3.generate_presigned_post(
            Bucket='intruder.analysis',
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=120
        )
        resp = success("Link successfully Generated", resp)
        print(resp)
    except ClientError as e:
        print(e)
        resp = error(f'{e}')

    return {
        'statusCode': 200,
        'headers': {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        },
        'body': json.dumps(resp)
    }
