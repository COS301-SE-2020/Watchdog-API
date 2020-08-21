import json
import boto3
import decimal
from pprint import pprint
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError
import sys
import traceback

s3_client = boto3.client('s3')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}

def get_data(parameters, user_id):
    client = boto3.client('dynamodb', region_name='af-south-1')
    response = client.query(
            ExpressionAttributeValues={
                ":v1": {'S': user_id}
            },
            KeyConditionExpression="user_id = :v1",
            **parameters
        )
    if len(response['Items']) == 0:
        return {}
    return from_dynamodb_to_json(response['Items'][0])
        
def generate_presigned_link(link):
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': 'watchdog.uservideocontent',
                                                            'Key': link.split('/')[-1]},
                                                    ExpiresIn=3600)
    except ClientError as e:
        logging.error(e)
        return None

    return response
    # return link
    
def lambda_handler(event, context):
    route = event['resource']
    params = event['queryStringParameters']
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"] 
    
    resp = {}
    
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
        
        
    try:
        if '/ui/recordings' == route:
            requests = [
                {
                    "TableName": "Artefacts",
                    "ProjectionExpression": "videos"
                },
                {
                    "TableName": "UserData",
                    "ProjectionExpression": "control_panel"
                }
            ]
            responses = [get_data(r, user_id) for r in requests]
            
            # if responses[0]:
            
            #for i, identity in enumerate(responses[1]['identities']['whitelist']):
                #identity["index"] = i
                #responses[1]['identities']['whitelist'] = identity
            
            # Putting room into camera object
            # {site: {location: {camera: {}}}}
            # {site: {"cameras": {camera: {room: ""}}}}
            # reformed_data = {}
            cameras = {}
            for site in responses[1]['control_panel']:
                cameras[site] = {"cameras": {}}
                for location in responses[1]['control_panel'][site]:
                    if location != 'metadata':
                        cameras["cameras"] = {**cameras, **responses[1]['control_panel'][site][location]}
                        for camera in cameras["cameras"]:
                            cameras["cameras"][camera]["location"] = location
                        # for cameras in responses[1]['control_panel'][site][location]:
                            # camera = {}
                           #print(json.dumps(camera))
                        #   camera['room'] = responses[1]['control_panel'][site][location]
                            # TODO: Let Abu know to change room to location
                            # camera['location'] = location
                            # cameras['camera'] = camera
                  
            # responses = get_data(requests[0], user_id)
            data = {"videos": responses[0]["videos"]}
            
            for i, video in enumerate(data["videos"]):
                video["path_in_s3"] = generate_presigned_link(video["path_in_s3"])
            
            pprint(cameras)
            pprint(data)
            
            for i, video in enumerate(responses[0]["videos"]):
                print(video)
                try:
                    data["videos"][i]["metadata"]["location"] = cameras[video['metadata']['camera_id']]['location']
                except Exception as e:
                    print(e)
            resp = success(f'Operation Successfull for "{route}"', extra=data)
        else:
            resp = {"status": "UNIMPLEMENTED", "message": f'The route "{route}" is not implemented yet. Tell Armin to get off his arse and implement it'} 
    except Exception as e:
        traceback.print_exc()
        resp = error(f'An unexpected error has occured: {e}', extra={"data": event})


    return {
        "statusCode":200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body":json.dumps(resp, cls=DecimalEncoder)
    }
