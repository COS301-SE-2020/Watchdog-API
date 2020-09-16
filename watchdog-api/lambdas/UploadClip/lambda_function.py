import boto3
import json
import os
import logging
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import datetime, timedelta


def get_location_from_tag(tag):
    if tag == "detected":
        return (
            os.environ["FRAME_BUCKET"],
            os.environ["PREPROCESS_DIRECTORY"],
            os.environ["FRAME_BUCKET_REGION"],
        )
    elif tag == "periodic" or tag == "movement" or tag == "intruder":
        return os.environ["VIDEO_BUCKET"], "", os.environ["VIDEO_BUCKET_REGION"]
    else:
        return None, None, None


def get_presigned_link(bucket, directory, region, event):
    # generating a presigned link for the S3 bucket with appropriate AWS roles and policies
    tag = event["queryStringParameters"]["tag"]
    file_name = event["queryStringParameters"]["file_name"]
    uuid = event["queryStringParameters"]["user_id"]
    camera_id = event["queryStringParameters"]["camera_id"]
    # timestamp = event['queryStringParameters']['timestamp']
    timestamp = datetime.now() + timedelta(hours=2)
    timestamp = str(timestamp.timestamp())

    token = event["queryStringParameters"]["token"]

    s3 = boto3.client("s3", config=Config(signature_version="s3v4"), region_name=region)
    key = directory + file_name
    fields = {
        "x-amz-meta-uuid": uuid,
        "x-amz-meta-tag": tag,
        "x-amz-meta-camera_id": camera_id,
        "x-amz-meta-timestamp": timestamp,
        "x-amz-meta-token": token,
    }
    conditions = [
        {"x-amz-meta-uuid": uuid},
        {"x-amz-meta-tag": tag},
        {"x-amz-meta-camera_id": camera_id},
        {"x-amz-meta-timestamp": timestamp},
        {"x-amz-meta-token": token},
    ]
    print(
        "(2. Meta Data for object): x-amz-meta-uuid:"
        + uuid
        + " x-amz-meta-key:"
        + key
        + " x-amz-meta-tag:"
        + tag
        + " x-amz-meta-camera_id:"
        + camera_id
        + " x-amz-meta-timestamp:"
        + timestamp
    )
    try:
        response = s3.generate_presigned_post(
            Bucket=bucket,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=120,  # expires in two minutes from generation
        )
    except ClientError as e:
        logging.error(e)
        exit()

    return response


def lambda_handler(event, context):
    response = None
    # Get request Parameters
    bucket, directory, region = get_location_from_tag(
        event["queryStringParameters"]["tag"]
    )
    print(
        f"(1. Tag information):  bucket:{bucket} directory:{directory}   region:{region}"
    )
    if bucket is not None:
        response = get_presigned_link(bucket, directory, region, event)
        print(
            "3. url link:"
            + str(response["url"])
            + "  fields:"
            + str(response["fields"])
        )

    # Package Response, provided in JSON format for API Gateway
    respObj = {
        "statusCode": 200,
        "headers": {"Content-tag": "application/json"},
        "body": json.dumps(response),
    }
    return respObj
