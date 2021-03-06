import boto3
import json
from copy import deepcopy
import os
from random import randint
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta, date
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.client import Config
from random import randint

s3 = boto3.client(
    "s3", config=Config(signature_version="s3v4"), region_name="eu-west-1"
)
dynamo_client = boto3.client("dynamodb", region_name="af-south-1")


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def get_profile_data(user_id):
    """
    get profiles and whitelist data from database
    """
    response = dynamo_client.query(
        TableName="Artefacts",
        ProjectionExpression="profiles, whitelist",
        KeyConditionExpression=f"user_id = :user_id",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )

    data = from_dynamodb_to_json(response["Items"][0])
    profiles = data["profiles"]
    whitelist = data["whitelist"]

    return profiles, whitelist


def get_profile_template_data(end_date, time_scale):
    """
    get data skeleton list for graph plugin
        1. get the time intervals
        2. get data skeleton given intervals
    """

    intervals = -1
    HOURS = 0
    DAYS = 0
    WEEKS = 0
    time_format = "%d %B %Y"

    print(f"Time scale: {time_scale}")
    if time_scale == "DAILY":
        intervals = 12  # 24 hours per day
        HOURS = 2
        time_format = "%I%p"
    elif time_scale == "WEEKLY":
        intervals = 7  # 7 days per week
        DAYS = 1
    elif time_scale == "MONTHLY":
        intervals = 4  # 4 weeks per month
        WEEKS = 1

    # end_date = date.fromtimestamp(float(end_date))
    # end_date = datetime(end_date.year, end_date.month, end_date.day)
    end_date = datetime.now() + timedelta(hours=2)
    print(f"TEMP current end date: {end_date.strftime('%I%p')}")
    x_axis = []
    data = []
    inter = []
    TEMP = []
    time_gap = timedelta(hours=HOURS, days=DAYS, weeks=WEEKS)
    for i in range(intervals - 1, -1, -1):
        x_step = end_date - (i * time_gap)
        TEMP.append(x_step.strftime("%I%p"))
        inter.append(str(x_step.timestamp()))
        data.append({"images": [], "x": x_step.strftime(time_format), "y": 0})
    print(f"TEMP x-axis:{TEMP}")
    return data, inter


def binsearch(t, key, low=0, high=0):
    high = len(t) - 1
    while low < high:
        mid = (low + high) // 2
        if float(t[mid]) < float(key):
            low = mid + 1
        else:
            high = mid
    # 	if float(t[low]) > float(key) and low > 0:
    # 	    low = low-1
    return low if key >= t[0] else -1


def generate_presigned_link(key):
    # generating a presigned link for S3 bucket
    try:
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": os.environ["BUCKET"], "Key": key},
            ExpiresIn=3600,
        )
    except ClientError as e:
        logging.error(e)
        return None

    return response


def get_location_from_camera_id(user_id, camera_id):
    response = dynamo_client.query(
        TableName="UserData",
        ProjectionExpression="control_panel",
        KeyConditionExpression=f"user_id = :user_id",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )
    data = from_dynamodb_to_json(response["Items"][0])
    data = data["control_panel"]
    location = None
    for site in data:
        for loc in data[site]:
            for cam in data[site][loc]:
                if cam == camera_id:
                    location = loc
                    break
    return location


def populate_graph_data(graph_data, whitelist, intervals, user_id):
    """
    populate graph skeleton with data from whitelist
    1. check each whitelist and see if it is in correct range
    2. if so, insert image object into correct profileat specific interval
    """
    for detected_owner in whitelist:
        index = binsearch(intervals, detected_owner["timestamp"])
        if index != -1:
            for profile in graph_data:
                if profile["aid"] == detected_owner["aid"]:
                    profile["data"][index]["images"].append(
                        {
                            "link": generate_presigned_link(detected_owner["key"]),
                            "timestamp": detected_owner["timestamp"],
                            "location": get_location_from_camera_id(
                                user_id, detected_owner["metadata"]["camera_id"]
                            ),
                            "camera_id": detected_owner["metadata"]["camera_id"],
                        }
                    )
                    profile["data"][index]["y"] = profile["data"][index]["y"] + 1
                    break
    return graph_data
