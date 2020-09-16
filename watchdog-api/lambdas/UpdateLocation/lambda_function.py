import json
import boto3
import os
from boto3.dynamodb.types import TypeDeserializer


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def get_current_locations(user_id, site_id):
    # Get the service resource using boto3 and dynamodb implementations.
    client = boto3.client('dynamodb', region_name='af-south-1')

    response = client.query(
        TableName='UserData',
        ExpressionAttributeValues={
            ':v1': {'S': user_id},
        },
        KeyConditionExpression=f'user_id = :v1',
        ProjectionExpression=f'control_panel.{site_id}'
    )
    print(str(response))
    resp = {}
    if len(response['Items']) > 0:
        resp = from_dynamodb_to_json(response['Items'][0])
    return resp


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
    # collecting the user id from the auth
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    route = event['resource']
    params = event['queryStringParameters']
    # updating an existing camera object (specifically its location)
    client = boto3.resource('dynamodb', region_name='af-south-1')
    table = client.Table('UserData')

    if '/cameras' in route:
        old_loc_name = params['old_location']
        new_loc_name = params['new_location']
        site_id = params['site_id']
        print(f"(1. parameters): site id: {site_id}; old location: {old_loc_name}; new location: {new_loc_name};")
        site_obj = get_current_locations(user_id, site_id)
        print(f"(2. site details): locations: {str(site_obj)}")

        site_obj = site_obj['control_panel']
        if new_loc_name not in site_obj[site_id] and old_loc_name in site_obj[site_id]:
            site_obj[site_id][new_loc_name] = site_obj[site_id][old_loc_name]
            del site_obj[site_id][old_loc_name]

            try:
                parameters = {
                    "Key": {"user_id": user_id},
                    "ReturnValues": "UPDATED_NEW",
                    "UpdateExpression": f'SET control_panel.#site = :obj',
                    "ExpressionAttributeValues": {
                        ":obj": site_obj[site_id]
                    },
                    "ExpressionAttributeNames": {
                        '#site': site_id
                    }
                }
                print(f"(3. Parameters for Update Function): parameters:{parameters}")
                response = table.update_item(**parameters)
                print(f"(4. Updated Site): {str(site_obj)}")
                response = success(msg=f'Dynamo UpdateItem Completed for "{route}"', extra=response)
                print(f"(5. Response): {str(response)}")
                statusCode = 200
            except Exception as e:
                response = error(f'Could not complete Dynamo Operation due to Error: {e}')
                print(str(response))
        else:
            statusCode = 202
            response = error(msg="new location already exists for given site, or the old one does not exist")

    return {
        'statusCode': statusCode,
        'headers': {"Access-Control-Allow-Origin": "*"},
        'body': json.dumps(response)
    }
