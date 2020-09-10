import boto3
import json
from copy import deepcopy
import os
from random import randint
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta, date
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.client import Config


s3 = boto3.client('s3', config=Config(signature_version='s3v4'), region_name='eu-west-1')
dynamo_client = boto3.client('dynamodb', region_name='af-south-1')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def get_profile_data(user_id):
    '''
        get profiles and whitelist data from database
    '''
    response = dynamo_client.query(
        TableName='Artefacts',
        ProjectionExpression='profiles, whitelist',
        KeyConditionExpression=f'user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': {"S": user_id}
        }
    )
    
    data = from_dynamodb_to_json(response['Items'][0])
    profiles = data['profiles']
    whitelist = data['whitelist']

    return profiles, whitelist


def get_graph_template_data(end_date, time_scale):
    '''
        get data skeleton list for graph plugin
            1. get the time intervals
            2. get data skeleton given intervals
    '''
    
    intervals = -1
    HOURS = 0
    DAYS = 0
    WEEKS = 0

    if time_scale == "DAILY":
        intervals = 24   # 24 hours per day
        HOURS = 1
    elif time_scale == "WEEKLY":
        intervals = 7   # 7 days per week
        DAYS = 1
    elif time_scale == "MONTHLY":
        intervals = 4   # 4 weeks per month
        WEEKS = 1
    
    end_date = date.fromtimestamp(float(end_date))
    end_date = datetime(end_date.year, end_date.month, end_date.day)
    x_axis = []
    data = []
    inter = []
    time_gap = timedelta(hours=HOURS, days=DAYS, weeks=WEEKS)
    for i in range(intervals-1, -1, -1):
        x_step = end_date - (i*time_gap)
        inter.append(str(x_step.timestamp()))
        data.append(
            {
                "images":[],
                "x": x_step.strftime("%d %B %Y"),
                "y":0
            }
        )
    
    return data, inter

def binsearch(t, key, low = 0, high = 0):
	high = len(t) - 1
	while low < high:
		mid = (low + high)//2
		if float(t[mid]) < float(key):
			low = mid + 1
		else:
			high = mid
	if float(t[low]) > float(key) and low > 0:
	    low = low-1
	return low if key >= t[0] else -1


def generate_presigned_link(key):
    #generating a presigned link for S3 bucket 
    try:
        response = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': os.environ['BUCKET'],
                'Key': key
            },
            ExpiresIn=3600
        )
    except ClientError as e:
        logging.error(e)
        return None

    return response


def get_location_from_camera_id(user_id, camera_id):
    response = dynamo_client.query(
        TableName='UserData',
        ProjectionExpression='control_panel',
        KeyConditionExpression=f'user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': {"S": user_id}
        }
    )
    data = from_dynamodb_to_json(response['Items'][0])
    data = data['control_panel']
    location = None
    for site in data:
        for loc in data[site]:
            for cam in data[site][loc]:
                if cam == camera_id:
                    location = loc
                    break
    return location


def populate_graph_data(graph_data, whitelist, intervals, user_id):
    '''
        populate graph skeleton with data from whitelist
        1. check each whitelist and see if it is in correct range
        2. if so, insert image object into correct profileat specific interval
    '''
    for detected_owner in whitelist:
        index = binsearch(intervals, detected_owner['timestamp'])
        print("index of detected owner "+str(index))
        if index != -1:
            for profile in graph_data:
                if profile['aid'] == detected_owner['aid']:
                    profile['data'][index]['images'].append(
                        {
                            "link": generate_presigned_link(detected_owner['key']),
                            "timestamp": detected_owner['timestamp'],
                            "location": get_location_from_camera_id(user_id, detected_owner['metadata']['camera_id']),
                            "camera_id": detected_owner['metadata']['camera_id']
                        }
                    )
                    profile['data'][index]['y'] = profile['data'][index]['y']+1
                    break
    return graph_data


def error(msg):
    return {
        "status": "ERROR",
        "message": f'Encountered an Unexpected Error: {msg}'
    }
    
# Bundle the response with an OK
def success(msg, extra={}):
    return {
        "status": "OK",
        "message": f'Operation Completed with Message: {msg}',
        "data": extra
    }


def lambda_handler(event, context):
    route = event['resource']
    params = event['queryStringParameters']
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    
    end_date = params['end_date']
    time_scale = params['time_scale']
    try:
        # profile analytics
        # 1. preprocess data - load profiles with data structure of graph
        profiles, whitelist = get_profile_data(user_id)
        print(f"(1.1 get profile data): profiles:{profiles}    whitelist:{whitelist}")
        # 2. load data - go through whitelist images and add the images to specified list
        graph_skeleton, intervals = get_graph_template_data(end_date, time_scale)
        print(f"(2.1 ): graph data skeleton:{graph_skeleton}  intervals: {intervals}")
        graph_data = []
        for profile in profiles:
            graph_data.append(
                {
                    "id":profile["name"],
                    "aid":profile["aid"],
                    "color":f"hsl({randint(0,10)*36},50%,50%)",
                    "data":deepcopy(graph_skeleton)
                }
            )

        print(f"(2. graph skeleton data with profiles): data:{graph_data}")
        graph_data = populate_graph_data(graph_data, whitelist, intervals, user_id)
        print(f"(3. graph populated data): graph data:{graph_data}")
        resp = success(f"Successfully retrieved graph data for interval {time_scale}", graph_data)
    except Exception as e:
        resp = error(f'Could not complete Dynamo Operation due to Error: {e}')
        
    return {"statusCode":200, "headers": {"Access-Control-Allow-Origin": "*"}, "body":json.dumps(resp)}
