import json
import boto3
import os


def get_meta_data_from_event(event):
    #fetching the metadata from the S3 bucket using the boto client
    s3 = boto3.client('s3')
    bucket = os.environ['BUCKET']
    
    record = event['Records'][0]['s3']
    key = record['object']['key']
    
    metadata = s3.head_object(Bucket=bucket, Key=key)
    metadata = metadata['ResponseMetadata']['HTTPHeaders']
    return metadata['x-amz-meta-uuid'], key, metadata['x-amz-meta-tag'], metadata['x-amz-meta-camera_id'], metadata['x-amz-meta-timestamp']

def add_video_to_user_data(event):
    user_id, video_name, tag, camera_id, timestamp = get_meta_data_from_event(event)
    print(f"(1. Get metadata from s3 object): user_id:{user_id};    video key:{video_name};    tag:{tag};    camera_id{camera_id};      timestamp{timestamp}")
    
    # append the video to the artefacts given the user_id
    client = boto3.resource('dynamodb', region_name='af-south-1')
    table = client.Table('Artefacts')
    path_in_s3 = os.environ['OBJECT_URL']+video_name
    print("path in s3: "+path_in_s3)
    response = table.update_item(
        Key={
            'user_id': user_id,
        },
        UpdateExpression="SET videos = list_append(videos, :i)",
        ExpressionAttributeValues={
            ":i": [
                {
                    'aid': hash(f'{video_name}-{user_id}'), #TODO: This hash is debatable...we can decide if it's okay or not 'rr'
                    'metadata': {
                        'camera_id':camera_id,
                        'timestamp':timestamp
                    },
                    'path_in_s3': path_in_s3,
                    "tag": tag
                }
            ]
        },
        ReturnValues="UPDATED_NEW"
    )
    return response


def lambda_handler(event, context):
    #invoke the function to add the given video the Artefacts table and correspond with UserData in
    add_video_to_user_data(event)
    print("(2. Add video record for user given the metadata)")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully Uploaded Video to Artefacts Table')
    }
