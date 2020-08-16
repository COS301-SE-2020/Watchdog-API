import os
import json
import boto3
from base64 import b64decode
import decimal
import datetime
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
    user_id = event['requestContext']['authorizer']['claims'][
        'sub']  # Get the user_id (which is the Cognito 'sub') from the Authorizer (which comes from Cognito when you use the WatchdogAuthorizer)

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
            data = loadBase64Json(event["body"])

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
            location = params["location"]
            camera_id = params["camera_id"]
            print("uploading camera " + camera_id + " from site " + site_id)
            data = loadBase64Json(event["body"])
            default_params = {
                "Key": {"user_id": user_id},
                "ReturnValues": "UPDATED_NEW",

            }

            check_site = {
                **default_params,
                "UpdateExpression": f'SET control_panel.#site = if_not_exists(control_panel.#site, :obj)',
                "ExpressionAttributeValues": {
                    ":obj": {
                        "metadata": {}
                    }
                },
                "ExpressionAttributeNames": {
                    '#site': site_id
                }

            }
            check_location = {
                **default_params,
                "UpdateExpression": f'SET control_panel.#site.#location = if_not_exists(control_panel.#site.#location, :obj)',
                "ExpressionAttributeValues": {
                    ":obj": {}
                },
                "ExpressionAttributeNames": {
                    '#site': site_id,
                    '#location': location
                }
            }
            add_camera = {
                **default_params,
                "UpdateExpression": f'SET control_panel.#site.#location.#camera = :obj',
                "ExpressionAttributeValues": {
                    ":obj": data
                },
                "ExpressionAttributeNames": {
                    '#site': site_id,
                    '#location': location,
                    '#camera': camera_id
                },
                "ExpressionAttributeNames": {
                    '#site': site_id,
                    '#location': location,
                    '#camera': camera_id
                }
            }

            resp = [
                add_data(check_site),
                add_data(check_location),
                add_data(add_camera)
            ]

            resp = success(msg=f'Dynamo UpdateItem Completed for "{route}. 3 operations completed successfully."',
                           extra={"data": resp})
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
                    "UpdateExpression": f'SET preferences.notifications.security_company = :security_company, SET preferences.notification.type = :type',
                    "ExpressionAttributeValues": {
                        ":security_company": data.security_company,
                        ":type": data.type
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
        elif '/logs' in route:
            data = loadBase64Json(event["body"])
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
        elif '/identities/tagdetectedimage' in route:
            key = params['key']
            name = params['name']

            client = boto3.client('dynamodb', region_name='af-south-1')

            response = client.query(
                TableName='Artefacts',
                KeyConditionExpression=f'user_id = :user_id',
                ProjectionExpression='frames',
                ExpressionAttributeValues={
                    ':user_id': {"S": user_id}
                }
            )
            print("(1. get the detected frames for the user): response:" + str(response))

            data = from_dynamodb_to_json(response['Items'][0])

            print(f"(1.1. Deserialised Data: {data}")

            # no frames in the database
            if len(data['frames']) != 0:

                # get the index of the element to be deleted in the artefacts table based on the user_id and the key element
                path_in_s3 = os.environ['OBJECT_URL'] + key
                index = -1
                for count, x in enumerate(data['frames']):
                    if data['frames'][count]['path_in_s3'] == path_in_s3:
                        index = count
                        break

                if index != -1:
                    print(
                        f"(2. index of detected frame and metadata): index:{index}  camera_id: {data['frames'][index]['metadata']['camera_id']}  aid:{data['frames'][index]['aid']}")

                    parameters = {
                        "Key": {
                            'user_id': user_id,
                        },
                        "UpdateExpression": "SET identities.whitelist = list_append(identities.whitelist, :i)",
                        "ExpressionAttributeValues": {
                            ":i": [
                                {
                                    "key": key,
                                    "path_in_s3": path_in_s3,
                                    "name": name,
                                    "timestamp": str(datetime.datetime.now().timestamp()),
                                    "metadata": {
                                        "camera_id": data['frames'][index]['metadata']['camera_id'],
                                        "aid": data['frames'][index]['aid']
                                    }
                                }
                            ]
                        },
                        "ReturnValues": "UPDATED_NEW"
                    }
                    resp = success(message="Image Successfully added to Whitelist", extra=add_data(parameters))

                    print(f"(3. Updated inserted whitelist image response): response:{str(resp)}")

                    client = boto3.resource('dynamodb', region_name='af-south-1')
                    table = client.Table('Artefacts')

                    res = table.update_item(
                        Key={
                            "user_id": user_id
                        },
                        UpdateExpression=f'REMOVE frames[{index}]',
                        ConditionExpression=f'frames[{index}].path_in_s3=:path_in_s3',
                        ReturnValues="UPDATED_NEW",
                        ExpressionAttributeValues={
                            ':path_in_s3': path_in_s3
                        }
                    )
                    print(
                        f"(4. Updated removed artefacts table record with removed detected frame): response:{str(res)}")
                else:
                    resp = error(
                        msg=f'Detected image is not found within the given detected images.',
                        extra={
                            "event": event
                        }
                    )
            else:
                resp = error(
                    msg=f'There are currently no images in the detected list.',
                    extra={
                        "event": event
                    }
                )
        else:
            resp = error(msg=f'Method not implemented yet. Tell Armin to get off his arse and do this: {route}', extra={
                "event": event,
                "post-body": loadBase64Json(event['body']),
            })
    except Exception as e:
        print(str(e))
        resp = error(f'Could not complete operation due to this error: "{str(e)}"')

    return {
        'statusCode': 200,
        'headers': {"Access-Control-Allow-Origin": "*"},
        'body': json.dumps(resp, cls=DecimalEncoder),
    }