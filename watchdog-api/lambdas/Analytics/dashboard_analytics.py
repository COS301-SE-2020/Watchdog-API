import boto3
import json
from copy import deepcopy
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta, date
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.client import Config

dynamo_client = boto3.client("dynamodb", region_name="af-south-1")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def get_detected_data(user_id):
    """
    get detected images(whitelist & blacklist) data from database
    """
    response = dynamo_client.query(
        TableName="Artefacts",
        ProjectionExpression="whitelist, blacklist",
        KeyConditionExpression=f"user_id = :user_id",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )

    data = from_dynamodb_to_json(response["Items"][0])
    whitelist = data["whitelist"]
    blacklist = data["blacklist"]

    return whitelist, blacklist


def get_dashboard_template_data(end_date):
    """
    get template data from
    """
    intervals = []
    labels = []
    # end_date = date.fromtimestamp(float(end_date))
    # end_date = datetime(end_date.year, end_date.month, end_date.day)
    end_date = datetime.now() + timedelta(hours=2)
    print(f"TEMP current end date: {end_date.strftime('%I%p')}")
    time_gap = timedelta(days=1)
    for i in range(6, -1, -1):
        x_step = end_date - (i * time_gap)
        intervals.append(str(x_step.timestamp()))
        labels.append(x_step.strftime("%d %B %Y"))

    datasets = [
        {"label": "Owners", "data": [], "fill": "false", "borderColor": "#03A9F4"},
        {
            "label": "Possible Intruders",
            "data": [],
            "fill": "false",
            "borderColor": "#FFC107",
        },
    ]

    return labels, datasets, intervals


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


def get_y_points_from_set(dataset, intervals):
    y_values = [0] * 7
    for identity in dataset:
        index = binsearch(intervals, identity["timestamp"])
        if index != -1:
            y_values[index] += 1
    return y_values
