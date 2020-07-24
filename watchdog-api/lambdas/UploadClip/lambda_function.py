import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
	
	

def get_location_from_tag(tag):
    if tag == 'detected':
        return os.environ['FRAME_BUCKET'], os.environ['DETECTED_DIRECTORY'], os.environ['FRAME_BUCKET_REGION']
    # elif tag == 'whitelist':
    #     return os.environ['FRAME_BUCKET'], os.environ['WHITELIST_DIRECTORY'], os.environ['FRAME_BUCKET_REGION']
    elif tag == 'periodic' or tag == 'movement' or tag == 'intruder':
        return os.environ['VIDEO_BUCKET'], '', os.environ['VIDEO_BUCKET_REGION']
    else:
        return None, None, None
    
def get_presigned_link(bucket, directory, region, event):
    tag = event['queryStringParameters']['tag']
    file_name = event['queryStringParameters']['file_name']
    uuid = event['queryStringParameters']['user_id']
    camera_id = event['queryStringParameters']['camera_id']
    timestamp = event['queryStringParameters']['timestamp']
    token = event['queryStringParameters']['token']
    
    s3 = boto3.client('s3', region_name=region)
    key = directory+file_name
    fields = {
        'x-amz-meta-uuid':uuid,
        'x-amz-meta-key':key,
        'x-amz-meta-tag':tag,
        'x-amz-meta-camera_id':camera_id,
        'x-amz-meta-timestamp':timestamp,
        'x-amz-meta-token':token
        # 'acl':'public-read'
        # ,'Cache-Control': 'nocache',
        # 'Content-tag': 'image/jpeg'
    }
    conditions = [
        {'x-amz-meta-uuid':uuid},
        {'x-amz-meta-key':key},
        {'x-amz-meta-tag':tag},
        {'x-amz-meta-camera_id':camera_id},
        {'x-amz-meta-timestamp':timestamp},
        {'x-amz-meta-token':token}
        # {'acl':'public-read'}
        # ,'Cache-Control': 'nocache',
        # 'Content-tag': 'image/jpeg'
    ]
    print("(2. Meta Data for object): x-amz-meta-uuid:"+uuid+" x-amz-meta-key:"+key+" x-amz-meta-tag:"+tag+" x-amz-meta-camera_id:"+camera_id+" x-amz-meta-timestamp:"+timestamp)
    try:
        response = s3.generate_presigned_post(
            Bucket=bucket, 
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=120  # expires in two minutes from generation
        )
    except ClientError as e:
        logging.error(e)
        exit()
        
    return response
    
            
def lambda_handler(event, context):
    response = None
    # Get request Parameters
    bucket, directory, region = get_location_from_tag(event['queryStringParameters']['tag'])
    print(f"(1. Tag information):  bucket:{bucket} directory:{directory}   region:{region}")
    if bucket is not None:
        response = get_presigned_link(bucket, directory, region, event)
        print("3. url link:"+str(response['url'])+"  fields:"+str(response['fields']))
    
    # Package Response
    respObj = {
        "statusCode": 200,
        "headers": {
            "Content-tag": "application/json"
        },
        "body": json.dumps(response)
    }
    return respObj