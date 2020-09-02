import json
import os
import boto3


def get_meta_data_from_event(event):
    s3 = boto3.client('s3', region_name='eu-west-1')
    bucket = os.environ['BUCKET']
    record = event['Records'][0]['s3']
    key = record['object']['key']
    metadata = s3.head_object(Bucket=bucket, Key=key)
    metadata = metadata['ResponseMetadata']['HTTPHeaders']
    return metadata['x-amz-meta-uuid'], key, metadata['x-amz-meta-name'], metadata['x-amz-meta-timestamp']


def add_whitelist_image_to_user_data(event):
    user_id, key, name, timestamp = get_meta_data_from_event(event)
    # add the whitelist image to the user data table given uuid and image name
    client = boto3.resource('dynamodb', region_name='af-south-1')
    table = client.Table('Artefacts')
    path_in_s3 = os.environ['OBJECT_URL'] + key
    print(f"(1. Preferences): user_id:{user_id};   whitelist image key:{key}    Path in s3:{path_in_s3}")

    response = table.update_item(
        Key={
            'user_id': user_id,
        },
        UpdateExpression="SET profiles = list_append(profiles, :i)",
        ExpressionAttributeValues={
            ":i": [
                {
                    "key": key,
                    "timestamp": timestamp,
                    "name": name,
                    "monitor": {
                        "watch": 0,
                        "custom_message": ""
                    }
                }
            ]
        },
        ReturnValues="UPDATED_NEW"
    )
    print("(2. Add whitelist image reference to database): Response:" + str(response))
    return response


def lambda_handler(event, context):
    response = add_whitelist_image_to_user_data(event)

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully added image!, repsonse:' + str(response))
    }
