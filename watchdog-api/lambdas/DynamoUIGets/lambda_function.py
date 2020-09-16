import json
import boto3
import decimal
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError
import sys
import traceback
from botocore.client import Config

s3 = boto3.client(
    "s3", config=Config(signature_version="s3v4"), region_name="af-south-1"
)
client = boto3.client("dynamodb", region_name="af-south-1")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def get_data(parameters, user_id):
    response = client.query(
        ExpressionAttributeValues={":v1": {"S": user_id}},
        KeyConditionExpression="user_id = :v1",
        **parameters,
    )
    if len(response["Items"]) == 0:
        return {}
    return from_dynamodb_to_json(response["Items"][0])


def generate_presigned_link(link):
    try:
        response = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": "watchdog.uservideocontent", "Key": link.split("/")[-1]},
            ExpiresIn=3600,
        )
    except ClientError as e:
        logging.error(e)
        print("ERROR GETTING PRESIGNED LINKED: " + str(link))
        return None

    return response


def lambda_handler(event, context):
    route = event["resource"]
    params = event["queryStringParameters"]
    user_id = event["requestContext"]["authorizer"]["claims"]["sub"]

    resp = {}

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

    try:
        if "/ui/recordings" == route:
            requests = [
                {"TableName": "Artefacts", "ProjectionExpression": "videos"},
                {"TableName": "UserData", "ProjectionExpression": "control_panel"},
            ]
            responses = [get_data(r, user_id) for r in requests]

            cameras = {}
            locations = {}
            for site in responses[1]["control_panel"]:
                cameras[site] = {"cameras": {}}
                for location in responses[1]["control_panel"][site]:
                    if location != "metadata":
                        cameras["cameras"] = {
                            **cameras,
                            **responses[1]["control_panel"][site][location],
                        }
                        for camera in cameras["cameras"]:
                            cameras["cameras"][camera]["location"] = location
                            locations[camera] = location

            data = {"videos": responses[0]["videos"], "locations": locations}

            print("DATA before adding presigned links: " + str(data))
            total = 0
            for i, video in enumerate(data["videos"]):
                video["path_in_s3"] = generate_presigned_link(video["path_in_s3"])
                if video["metadata"]["camera_id"] in locations:
                    video["location"] = locations[video["metadata"]["camera_id"]]
                else:
                    video["location"] = "Not Found"
                total = i

            resp = success(f'Operation Successfull for "{route}"', extra=data)
        else:
            resp = {
                "status": "UNIMPLEMENTED",
                "message": f'The route "{route}" is not implemented yet. Tell Armin to get off his arse and implement it',
            }
    except Exception as e:
        traceback.print_exc()
        resp = error(f"An unexpected error has occured: {e}", extra={"data": event})
        print("ERROR: " + str(resp))

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(resp, cls=DecimalEncoder),
    }
