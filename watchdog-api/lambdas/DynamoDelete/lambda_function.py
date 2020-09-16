import json
import boto3
from botocore.exceptions import ClientError

# import decimal
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer


# class DecimalEncoder(json.JSONEncoder):
#     def default(self, o):
#         if isinstance(o, decimal.Decimal):
#             return float(o)
#         return super(DecimalEncoder, self).default(o)


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


# Bundle the Response with an ERROR
def error(msg, extra={}):
    return {
        "status": "ERROR",
        "message": f"Encountered an Unexpected Error: {msg}",
        **extra,
    }


# Bundle the response with an OK
def success(msg, extra={}):
    return {
        "status": "OK",
        "message": f"Operation Completed with Message: {msg}",
        "data": {**extra},
    }


def remove_profile_at_index(index, user_id, type):
    index = int(index)
    dynamo_client = boto3.client("dynamodb", region_name="af-south-1")
    dynamo_resource = boto3.resource("dynamodb", region_name="af-south-1")
    # get profile data
    response = dynamo_client.query(
        TableName="Artefacts",
        KeyConditionExpression=f"user_id = :user_id",
        ProjectionExpression=type,
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )
    print("1. returned: " + str(response["Items"][0]))
    # response = json.loads(response)
    data = from_dynamodb_to_json(response["Items"][0])
    _key = data[type][index]["key"]
    table = dynamo_resource.Table("Artefacts")
    res = table.update_item(
        Key={"user_id": user_id},
        UpdateExpression=f"REMOVE {type}[{index}]",
        ConditionExpression=f"{type}[{index}].#key = :image_key",
        ReturnValues="UPDATED_NEW",
        ExpressionAttributeValues={":image_key": _key},
        ExpressionAttributeNames={"#key": "key"},
    )
    print("profile: " + str(data[type][index]))
    return data[type][index]


def move_whitelist_images(profile, user_id):
    """
    move and remove all images in the whitelist that have the same aid
    (same person) to the blacklist so that the user can tag them again
    if they want to.
    """
    # get whitelist images
    dynamo_client = boto3.client("dynamodb", region_name="af-south-1")
    response = dynamo_client.query(
        TableName="Artefacts",
        KeyConditionExpression=f"user_id = :user_id",
        ProjectionExpression="whitelist",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )
    data = from_dynamodb_to_json(response["Items"][0])
    data = data["whitelist"]
    # find all occurences of given aid in profile with whitelist
    count = 0
    dynamo_resource = boto3.resource("dynamodb", region_name="af-south-1")
    table = dynamo_resource.Table("Artefacts")

    for i in range(len(data) - 1, -1, -1):
        if str(profile["aid"]) == str(data[i]["aid"]):
            # try and remove the whitelist image in the database given the index
            try:
                res = table.update_item(
                    Key={"user_id": user_id},
                    UpdateExpression=f"REMOVE whitelist[{i}]",
                    ConditionExpression=f"whitelist[{i}].#key = :image_key",
                    ReturnValues="UPDATED_NEW",
                    ExpressionAttributeValues={":image_key": data[i]["key"]},
                    ExpressionAttributeNames={"#key": "key"},
                )
            except dynamo_resource.meta.client.exceptions.ConditionalCheckFailedException as e:
                print(e)
                return False
            # add the whitelist record to the blacklist
            response = table.update_item(
                Key={
                    "user_id": user_id,
                },
                UpdateExpression="SET blacklist = list_append(blacklist, :i)",
                ExpressionAttributeValues={
                    ":i": [
                        {
                            "key": data[i]["key"],
                            "timestamp": data[i]["timestamp"],
                            "metadata": data[i]["metadata"],
                        }
                    ]
                },
                ReturnValues="UPDATED_NEW",
            )
            print(f"Moved whitelist image {data[i]['key']} to the blacklist")
            count += 1
    print(f"Amount of whitelist images removed and moved to the blacklist: {count}")
    return True


def lambda_handler(event, context):
    client = boto3.resource("dynamodb", region_name="af-south-1")

    route = event["resource"]
    params = event["queryStringParameters"]
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    resp = {}

    try:
        # the identities route to remove whitelisted images and profiles from the HCP
        if "/identities" in route:
            type = params["type"]
            index = params["index"]
            if type == "profiles":
                print("remove index " + index)
                dynamo_client = boto3.client("dynamodb", region_name="af-south-1")
                # get profile data
                profile = remove_profile_at_index(index, user_id, type)
                print(f"profile {profile}")
                is_valid = False
                while is_valid == False:
                    is_valid = move_whitelist_images(profile, user_id)
                resp = success(
                    f"DELETE completed successfully on item: {index}", extra={}
                )
            elif type == "blacklist":
                blacklist = remove_profile_at_index(index, user_id, type)
        elif "/cameras" in route:
            site_id = params["site_id"]
            location = params["location"]
            camera_id = params["camera_id"]
            print(
                f"(1. Parameters): route:'/cameras'   site_id:{site_id}   location:{location}    camera_id:{camera_id}"
            )
            table = client.Table("UserData")
            resp = table.update_item(
                Key={"user_id": user_id},
                UpdateExpression=f"REMOVE control_panel.#site_id.#location.#camera_id",
                ReturnValues="UPDATED_NEW",
                ExpressionAttributeNames={
                    "#site_id": site_id,
                    "#location": location,
                    "#camera_id": camera_id,
                },
            )
            resp = success(
                f"DELETE completed successfully for camera {camera_id}", extra=resp
            )
            print(f"(2. response): response:{resp}")
        elif "/sites" in route:
            """
            Remove location in a given site
            """
            site_id = params["site_id"]
            location = params["location"]

            print(
                f"(1. Parameters): route:'/cameras'   site_id:{site_id}   location:{location}"
            )
            table = client.Table("UserData")
            resp = table.update_item(
                Key={"user_id": user_id},
                UpdateExpression=f"REMOVE control_panel.#site_id.#location",
                ReturnValues="UPDATED_NEW",
                ExpressionAttributeNames={"#site_id": site_id, "#location": location},
            )
            resp = success(
                f"DELETE completed successfully for location {location} in site {site_id}",
                extra=resp,
            )

    except ClientError as e:
        resp = error(f"An unexpected Client Error occured: {e}", {"data": e})
        print(str(resp))
    finally:
        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": str(resp),
        }
