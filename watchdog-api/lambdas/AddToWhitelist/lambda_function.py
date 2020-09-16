import json
import os
import boto3
from botocore.client import Config
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

# Define resources
s3 = boto3.client(
    "s3", config=Config(signature_version="s3v4"), region_name="eu-west-1"
)
rekognition = boto3.client("rekognition", region_name="eu-west-1")


def from_dynamodb_to_json(item):
    """
    Deserialise data from dynamo request
    """
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def get_meta_data_from_event(event):
    """
    get metadata from image that triggered the function
    """
    bucket = os.environ["BUCKET"]
    record = event["Records"][0]["s3"]
    key = record["object"]["key"]
    metadata = s3.head_object(Bucket=bucket, Key=key)
    metadata = metadata["ResponseMetadata"]["HTTPHeaders"]
    return (
        key,
        metadata["x-amz-meta-uuid"],
        metadata["x-amz-meta-name"],
        metadata["x-amz-meta-timestamp"],
    )


def get_identities(user_id):
    """
    get current profiles to check if the given name is unique
    get blacklist images to add similar images of the owner to the whitelist
    """
    dynamo_client = boto3.client("dynamodb", region_name="af-south-1")
    response = dynamo_client.query(
        TableName="Artefacts",
        ProjectionExpression="profiles, blacklist",
        KeyConditionExpression=f"user_id = :user_id",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )
    data = from_dynamodb_to_json(response["Items"][0])
    return data["profiles"], data["blacklist"]


def add_to_profile(user_id, key, timestamp, name):
    """
    add image key to profiles
    """
    dynamo_resource = boto3.resource("dynamodb", region_name="af-south-1")
    table = dynamo_resource.Table("Artefacts")
    artefact_id = str(hash(f"{key}-{user_id}"))
    response = table.update_item(
        Key={
            "user_id": user_id,
        },
        UpdateExpression="SET profiles = list_append(profiles, :i)",
        ExpressionAttributeValues={
            ":i": [
                {
                    "key": key,
                    "aid": artefact_id,
                    "timestamp": timestamp,
                    "name": name,
                    "monitor": {"watch": 0, "custom_message": ""},
                }
            ]
        },
        ReturnValues="UPDATED_NEW",
    )
    print("(3. Add to profiles): Response:" + str(response))
    return artefact_id


def is_name_unique(name, profiles):
    for profile in profiles:
        if profile["name"] == name:
            return False
    return True


def add_similar_images_to_whitelist(user_id, key, aid, blacklist):
    """
    check blacklist to see if image is similar,
    if so, add them to the whitelist with the aid of the image being added
    """
    dynamo_resource = boto3.resource("dynamodb", region_name="af-south-1")
    count = 0
    for i in range(len(blacklist) - 1, -1, -1):
        response = rekognition.compare_faces(
            SourceImage={"S3Object": {"Bucket": os.environ["BUCKET"], "Name": key}},
            TargetImage={
                "S3Object": {
                    "Bucket": os.environ["BUCKET"],
                    "Name": blacklist[i]["key"],
                }
            },
        )
        if len(response["FaceMatches"]) > 0:
            table = dynamo_resource.Table("Artefacts")
            try:
                response = table.update_item(
                    Key={"user_id": user_id},
                    UpdateExpression=f"REMOVE blacklist[{i}]",
                    ConditionExpression=f"blacklist[{i}].#key = :name",
                    ExpressionAttributeNames={"#key": "key"},
                    ExpressionAttributeValues={":name": blacklist[i]["key"]},
                    ReturnValues="UPDATED_NEW",
                )
            except dynamo_resource.meta.client.exceptions.ConditionalCheckFailedException as e:
                print(e)
                return False
            response = table.update_item(
                Key={
                    "user_id": user_id,
                },
                UpdateExpression="SET whitelist = list_append(whitelist, :i)",
                ExpressionAttributeValues={
                    ":i": [
                        {
                            "key": blacklist[i]["key"],
                            "aid": aid,
                            "metadata": blacklist[i]["metadata"],
                            "timestamp": blacklist[i]["timestamp"],
                        }
                    ]
                },
                ReturnValues="UPDATED_NEW",
            )
            count += 1
            print(
                f"(4.1 Profile image found & removed in blacklist and moved to whitelist): profile key:{key} blacklist key:{blacklist[i]['key']}"
            )
    print(f"(4.2 Count of similar images): count:{count}")
    return True


def lambda_handler(event, context):
    status_code = 200
    response = "Successfully added image to profiles"
    key, user_id, name, timestamp = get_meta_data_from_event(event)
    print(
        f"(1. Metadata from bucket): image key:{key}  name of user:{name} timestamp:{timestamp} user id:{user_id}"
    )
    profiles, blacklist = get_identities(user_id)
    print(f"(2. identities): current profiles:{profiles}  blacklist:{blacklist}")
    if is_name_unique(name, profiles):
        print("(3. name uniqueness) unique: TRUE")
        aid = add_to_profile(user_id, key, timestamp, name)

        # corner case - if the detected list is updated concurrently and
        # displases the index of the key to update, then it will not update the
        # blacklist correctly
        is_valid = False
        while is_valid == False:
            profiles, blacklist = get_identities(user_id)
            is_valid = add_similar_images_to_whitelist(user_id, key, aid, blacklist)
    else:
        print("(3. name uniqueness) unique: FALSE")
        status_code = 500
        response = "The name of the profile already exists!"

    return {"status": "OK", "status_code": status_code, "body": response}
