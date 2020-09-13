import json
import boto3
from botocore.exceptions import ClientError
import decimal
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}

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
    client = boto3.resource('dynamodb', region_name = 'af-south-1')
    
    route = event['resource']
    params = event['queryStringParameters']
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"] 
    
    resp = {}
        
    try:
        #the identities route to remove whitelisted images and profiles from the HCP 
        if '/identities' in route:
            index = params['index']
            parameters = {
                "Key": {"user_id": user_id},
                "UpdateExpression": f'REMOVE profiles[{index}]',
                "ReturnValues": "UPDATED_NEW"
            }
            table = client.Table('Artefacts')
            data = table.update_item(**parameters)
            resp = success(f'DELETE completed successfully on item: {index}', extra=data)
            
        elif '/cameras' in route:
            site_id = params['site_id']
            location = params['location']
            camera_id = params['camera_id']
            print(f"(1. Parameters): route:'/cameras'   site_id:{site_id}   location:{location}    camera_id:{camera_id}")
            table = client.Table('UserData')
            resp = table.update_item(
                Key =  {
                    "user_id": user_id
                },
                UpdateExpression = f'REMOVE control_panel.#site_id.#location.#camera_id',
                ReturnValues = "UPDATED_NEW",
                ExpressionAttributeNames = {
                    '#site_id':site_id,
                    "#location": location,
                    '#camera_id': camera_id
                }
            )
            resp = success(f'DELETE completed successfully for camera {camera_id}', extra=resp)
            print(f"(2. response): response:{resp}")
        elif '/sites' in route:
            '''
                Remove location in a given site
            '''
            site_id = params['site_id']
            location = params['location']
            
            print(f"(1. Parameters): route:'/cameras'   site_id:{site_id}   location:{location}")
            table = client.Table('UserData')
            resp = table.update_item(
                Key =  {
                    "user_id": user_id
                },
                UpdateExpression = f'REMOVE control_panel.#site_id.#location',
                ReturnValues = "UPDATED_NEW",
                ExpressionAttributeNames = {
                    '#site_id':site_id,
                    "#location": location
                }
            )
            resp = success(f'DELETE completed successfully for location {location} in site {site_id}', extra=resp)
            
    except ClientError as e:
        resp = error(f'An unexpected Client Error occured: {e}', {'data': e})
        print(str(resp))
    finally:
        return {
            'statusCode': 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            'body': str(resp)
        }
