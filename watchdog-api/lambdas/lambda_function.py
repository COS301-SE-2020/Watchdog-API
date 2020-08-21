import json
import boto3
import os

def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}

def fetch_from_dynamo(user_id, projectionExpression=None, tableName='UserData'):
    # Get the service resource using boto3 and dynamodb implementations.
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


def lambda_handler(event, context):
    # collecting the user id from the auth 
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    route = event['resource']
    params = event['queryStringParameters']
    # updating an existing camera object (specifically its location)
      client = boto3.resource('dynamodb', region_name='af-south-1')
      table = client.Table('UserData')
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
        # The try block where different routes facilitate different get requests and different info fetched from dynamodb tables
        if '/cameras' in route:
            old_loc_name = params['old_location']
            new_loc_name = params['new_location']
            site_id = params['site_id']
            site_obj = json.dumps(fetch_from_dynamo(user_id,projectionExpression=f'control_panel.{site_id}'))
            data=loadBase64Json(event["body"])
            
            if 'metadata' not in data.keys():
                data['metadata'] = {}
            if new_loc_name is not in site_obj:
                parameters = {
                "Key": {"user_id": user_id},
                "UpdateExpression": f'SET control_panel.{site_id}.{old_loc_name} = :obj',
                "ExpressionAttributeValues": {
                    ":obj": new_loc_name
                },
                "ReturnValues": "UPDATED_NEW"
                }
                table.update_item(parameters)
                resp = success(msg=f'Dynamo UpdateItem Completed for "{route}"', extra=resp)
            
               
            else:
                resp = errpr(msg="that location already exists on the specified site")
            
     except Exception as e:
        resp = error(f'Could not complete Dynamo Operation due to Error: {e}')
      
    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*"},
        'body': json.dumps(resp)
    }
