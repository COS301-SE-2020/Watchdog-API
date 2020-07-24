import json
import boto3
import decimal
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

s3_client = boto3.client('s3', region_name='eu-west-1')

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}

def fetch_from_dynamo(user_id, projectionExpression=None, tableName='UserData'):
    # Get the service resource.
    client = boto3.client('dynamodb', region_name='af-south-1')
    
    if projectionExpression is None:
        response = client.query(
            TableName=tableName,
            ExpressionAttributeValues={
                ':v1': {'S': user_id},
            },
            KeyConditionExpression=f'user_id = :v1',
        )
    else:
        response = client.query(
            TableName='UserData',
            ExpressionAttributeValues={
                ':v1': {'S': user_id},
            },
            KeyConditionExpression=f'user_id = :v1',
            ProjectionExpression=projectionExpression
        )

    if len(response['Items']) == 0:
        return {}
    return from_dynamodb_to_json(response['Items'][0])
    
    
def generate_presigned_link(key):
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': 'intruder.analysis',
                'Key': key
            },
            ExpiresIn=3600
        )
    except ClientError as e:
        logging.error(e)
        return None

    return response

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
        if '/user' in route:
            data = fetch_from_dynamo(user_id)
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
        elif '/detectintruder' in route:
            prjEx = 'identities.whitelist, preferences.notifications, preferences.security_level'
            data = fetch_from_dynamo(user_id, projectionExpression=prjEx)
            
            # Manip data to add presigned link:
            for x, identity in enumerate(data['identities']['whitelist']):
                link = data['identities']['whitelist'][x]['key']
                data['identities']['whitelist'][x]['path_in_s3'] = generate_presigned_link(link)
                
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
        elif '/controlpanel' in route:
            data = fetch_from_dynamo(user_id, projectionExpression='control_panel')
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
        elif '/cameras' in route: 
            projectionExpression = 'control_panel'
            site_id = params['site_id']
            
            if 'camera_id' in params.keys():
                camera_id=params['camera_id']
                projectionExpression = f'control_panel.{site_id}.cameras.{camera_id}'
            else:
                projectionExpression = f'control_panel.{site_id}.cameras'
                
            data = fetch_from_dynamo(user_id, projectionExpression=f'control_panel.{site_id}')
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
            
        elif '/identities' in route: 
            data = fetch_from_dynamo(user_id, projectionExpression='identities')
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
        elif '/preferences' in route: 
            data = {}
            if "/securitylevel" in route:
                data = fetch_from_dynamo(user_id, projectionExpression='preferences.security_level')
            else:
                data = fetch_from_dynamo(user_id, projectionExpression='preferences')
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
        elif '/sites' in route:
            prjEx = f'control_panel'
            
            if 'site_id' in params.keys():
                site_id = params['site_id']
                prjEx = f'control_panel.{site_id}'
            
            data = fetch_from_dynamo(user_id, projectionExpression=prjEx)
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
        elif '/storage/video' == route:
            data = fetch_from_dynamo(user_id, tableName='Artefacts')
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
        elif '/logs' in route:
            data = fetch_from_dynamo(user_id, projectionExpression='logs')
            resp = success(f'Dynamo GetItem Completed for {route}', extra=data)
            
    except Exception as e:
        resp = error(f'Could not complete Dynamo Operation due to Error: {e}')
        
    return {"statusCode":200, "headers": {"Access-Control-Allow-Origin": "*"}, "body":json.dumps(resp, cls=DecimalEncoder)}