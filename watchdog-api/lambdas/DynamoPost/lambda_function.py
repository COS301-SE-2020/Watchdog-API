import json
import boto3
from base64 import b64decode
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

def loadBase64Json(obj):
    return json.loads(str(b64decode(obj), 'utf-8').strip())
    
def add_data(parameters):
    client = boto3.resource('dynamodb')
    table = client.Table('UserData')
    
    # Create operation
    # print(parameters)
    # return parameters
    return table.update_item(**parameters)
    # return {}
    

def lambda_handler(event, context):
    
    route = event['resource']
    params = event['queryStringParameters']
    user_id = event['requestContext']['authorizer']['claims']['sub'] # Get the user_id (which is the Cognito 'sub') from the Authorizer (which comes from Cognito when you use the WatchdogAuthorizer)
    
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
        if '/sites' in route:
            site_id = params["site_id"]
            data=loadBase64Json(event["body"])
            
            if 'cameras' not in data.keys():
                data['cameras'] = {}
            if 'metadata' not in data.keys():
                data['metadata'] = {}
                
            parameters = {
                "Key": {"user_id": user_id},
                "UpdateExpression": f'SET control_panel.{site_id} = :obj',
                "ExpressionAttributeValues": {
                    ":obj": data
                },
                "ReturnValues": "UPDATED_NEW"
            }
            resp = add_data(parameters)
            resp = success(msg=f'Dynamo UpdateItem Completed for "{route}"', extra=resp)
        elif '/cameras' in route:
            site_id = params["site_id"]
            camera_id = params["camera_id"]
            print("uploading camera "+camera_id+" from site "+site_id)
            data = loadBase64Json(event["body"])
            parameters = {
                "Key": {"user_id": user_id},
                "UpdateExpression": f'SET control_panel.{site_id}.cameras.{camera_id} = :obj',
                "ExpressionAttributeValues": {
                    ":obj": data
                },
                "ReturnValues": "UPDATED_NEW"
            }
            resp = add_data(parameters)
            resp = success(msg=f'Dynamo UpdateItem Completed for "{route}"', extra=resp)
        elif '/preferences' in route:
            data = loadBase64Json(event["body"])
            if '/securitylevel' in route:
                parameters = {
                    "Key": {"user_id": user_id},
                    "UpdateExpression": f'SET preferences.security_level = :obj',
                    "ExpressionAttributeValues": {
                        ":obj": str(data['security_level'])
                    },
                    "ReturnValues": "UPDATED_NEW"
                }
                resp = add_data(parameters)
            elif '/notifications' in route:
                parameters = {
                    "Key": {"user_id": user_id},
                    "UpdateExpression": f'SET preferences.notifications = :obj',
                    "ExpressionAttributeValues": {
                        ":obj": data
                    },
                    "ReturnValues": "UPDATED_NEW"
                }
                print(data)
                resp = add_data(parameters)
            else:
                parameters = {
                    "Key": {"user_id": user_id},
                    "UpdateExpression": f'SET preferences = :obj',
                    "ExpressionAttributeValues": {
                        ":obj": data
                    },
                    "ReturnValues": "UPDATED_NEW"
                }
                resp = add_data(parameters)
            resp = success(msg=f'Dynamo UpdateItem Completed for "{route}"', extra=resp)
        elif '/logs':
            data=loadBase64Json(event["body"])
            print(data)
            parameters = {
                "Key": {"user_id": user_id},
                "UpdateExpression": f'SET logs = list_append(logs, :obj)',
                "ExpressionAttributeValues": {
                    ":obj": [data]
                },
                "ReturnValues": "UPDATED_NEW"
            }
            resp = add_data(parameters)
        else:
            resp = error(msg=f'Method not implemented yet. Tell Rishi to get off his arse and do this: {route}', extra={
                "event": event,
                "post-body": loadBase64Json(event['body']),
            })
    except Exception as e:
        resp = error(f'Could not complete operation due to this error: "{str(e)}"')
    
    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*"},
        'body': json.dumps(resp),
    }