import os
import json
import boto3
from base64 import b64decode
import decimal
import datetime
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.client import Config


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def loadBase64Json(obj):
    return json.loads(str(b64decode(obj), "utf-8").strip())


def add_data(parameters):
    client = boto3.resource("dynamodb")
    table = client.Table("UserData")

    return table.update_item(**parameters)


def get_blacklist_images(user_id):
    client = boto3.client("dynamodb", region_name="af-south-1")

    response = client.query(
        TableName="Artefacts",
        KeyConditionExpression=f"user_id = :user_id",
        ProjectionExpression="blacklist",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )
    print("(1. get the detected frames for the user): response:" + str(response))

    data = from_dynamodb_to_json(response["Items"][0])

    print(f"(1.1. Deserialised Data: {data}")
    return data


def get_email_address_from_user(user_id):
    client = boto3.client("dynamodb", region_name="af-south-1")

    response = client.query(
        TableName="UserData",
        KeyConditionExpression=f"user_id = :user_id",
        ProjectionExpression="preferences.notifications.email",
        ExpressionAttributeValues={":user_id": {"S": user_id}},
    )

    email = from_dynamodb_to_json(response["Items"][0])
    email = email["preferences"]["notifications"]["email"]
    print(f"(1. get email address of user): response:{email}")
    return email


def is_email_verified(user_id):
    email = get_email_address_from_user(user_id)

    ses = boto3.client("ses", region_name="eu-west-1")

    verified_emails = ses.list_identities(IdentityType="EmailAddress")
    verified_emails = verified_emails["Identities"]
    print(f"(1. get verified email addresses in SES): response:{verified_emails}")

    for verified_email in verified_emails:
        if verified_email == email:
            return True
    return False


def verify_email(user_id):
    email = get_email_address_from_user(user_id)
    ses = boto3.client("ses", region_name="eu-west-1")
    response = ses.verify_email_address(EmailAddress=email)
    print("(verify email address link sent): to:" + email)
    return response


def get_index_of_blacklist_image(key, data):
    index = -1
    # no frames in the database
    if len(data["blacklist"]) != 0:
        # get the index of the element to be deleted in the artefacts table based on the user_id and the key element
        for count, x in enumerate(data["blacklist"]):
            if data["blacklist"][count]["key"] == key:
                index = count
                break
    return index


def add_image_to_profiles(key, name):
    """
    Copy object from detected directory to whitelist directory.
    This will trigger the addToWhitelist function which will add it to the
    whitelist and aggregate other images that are the same person to the whitelist
    """
    s3 = boto3.client(
        "s3", config=Config(signature_version="s3v4"), region_name="eu-west-1"
    )

    k = s3.head_object(Bucket=os.environ["IMAGE_BUCKET"], Key=key)
    m = k["Metadata"]
    m["name"] = name
    s3.copy_object(
        Bucket=os.environ["IMAGE_BUCKET"],
        Key="whitelist/" + key.split("/")[1],
        CopySource={"Bucket": os.environ["IMAGE_BUCKET"], "Key": key},
        Metadata=m,
        MetadataDirective="REPLACE",
    )
    print(f"copy image {key} to whitelist/{key.split('/')[1]}")
    s3.delete_object(Bucket=os.environ["IMAGE_BUCKET"], Key=key)
    print(f"delete original image from s3 {key}")
    return {
        "data": "Moved image to whitelist directory and triggered function to add it to profiles"
    }


def remove_blacklist_record(index, user_id, key):
    client = boto3.resource("dynamodb", region_name="af-south-1")
    table = client.Table("Artefacts")

    res = table.update_item(
        Key={"user_id": user_id},
        UpdateExpression=f"REMOVE blacklist[{index}]",
        ConditionExpression=f"blacklist[{index}].#key = :image_key",
        ReturnValues="UPDATED_NEW",
        ExpressionAttributeValues={":image_key": key},
        ExpressionAttributeNames={"#key": "key"},
    )


def lambda_handler(event, context):
    print(f"POST BEGIN")
    route = event["resource"]
    params = event["queryStringParameters"]
    user_id = event["requestContext"]["authorizer"]["claims"][
        "sub"
    ]  # Get the user_id (which is the Cognito 'sub') from the Authorizer (which comes from Cognito when you use the WatchdogAuthorizer)

    print(f"Prerequisite -> resource: {route}")
    print(f"Prerequisite -> user_id: {user_id}")
    print(f"Prerequisite -> params: {params}")
    resp = {}

    def error(msg, extra={}):
        return {
            "status": "ERROR",
            "message": f"Encountered an Unexpected Error: {msg}",
            **extra,
        }

    def success(msg, extra={}):
        return {
            "status": "OK",
            "message": f"Operation Completed with Message: {msg}",
            "data": {**extra},
        }

    try:
        if "/sites" in route:
            site_id = params["site_id"]
            data = loadBase64Json(event["body"])

            if "metadata" not in data.keys():
                data["metadata"] = {}

            parameters = {
                "Key": {"user_id": user_id},
                "UpdateExpression": f"SET control_panel.{site_id} = :obj",
                "ExpressionAttributeValues": {":obj": data},
                "ReturnValues": "UPDATED_NEW",
            }
            resp = add_data(parameters)
            resp = success(msg=f'Dynamo UpdateItem Completed for "{route}"', extra=resp)
        elif "/cameras" in route:
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
                "UpdateExpression": f"SET control_panel.#site = if_not_exists(control_panel.#site, :obj)",
                "ExpressionAttributeValues": {":obj": {"metadata": {}}},
                "ExpressionAttributeNames": {"#site": site_id},
            }
            check_location = {
                **default_params,
                "UpdateExpression": f"SET control_panel.#site.#location = if_not_exists(control_panel.#site.#location, :obj)",
                "ExpressionAttributeValues": {":obj": {}},
                "ExpressionAttributeNames": {"#site": site_id, "#location": location},
            }
            add_camera = {
                **default_params,
                "UpdateExpression": f"SET control_panel.#site.#location.#camera = :obj",
                "ExpressionAttributeValues": {":obj": data},
                "ExpressionAttributeNames": {
                    "#site": site_id,
                    "#location": location,
                    "#camera": camera_id,
                },
                "ExpressionAttributeNames": {
                    "#site": site_id,
                    "#location": location,
                    "#camera": camera_id,
                },
            }

            resp = [
                add_data(check_site),
                add_data(check_location),
                add_data(add_camera),
            ]

            resp = success(
                msg=f'Dynamo UpdateItem Completed for "{route}. 3 operations completed successfully."',
                extra={"data": resp},
            )
        elif "/preferences" in route:
            print("-> Compiling DATA")
            data = {}
            if "body" in event.keys():
                if event["body"] is not None:
                    data = loadBase64Json(event["body"])

            print(f"-> DATA: {data}")

            if "/preferences/securitylevel" in route:
                parameters = {
                    "Key": {"user_id": user_id},
                    "UpdateExpression": f"SET preferences.security_level = :obj",
                    "ExpressionAttributeValues": {":obj": str(data["security_level"])},
                    "ReturnValues": "UPDATED_NEW",
                }
                resp = add_data(parameters)
            elif "/preferences/notifications" in route:
                if "verify" in route:
                    response = verify_email(user_id)
                    resp = {
                        "response": response,
                        "data": {"email_verification_sent": True},
                    }
                else:
                    client = boto3.resource("dynamodb", region_name="af-south-1")
                    table = client.Table("UserData")
                    table.update_item(
                        Key={"user_id": user_id},
                        UpdateExpression="SET preferences.notifications.security_company = :security_company",
                        ExpressionAttributeValues={
                            ":security_company": params["security_company"]
                        },
                        ReturnValues="UPDATED_NEW",
                    )
                    print("updated security company number")
                    is_valid = True
                    resp = {}
                    if params["type"] == "email":
                        if not is_email_verified(user_id):
                            is_valid = False
                            print("TEMP: email NOT verified")
                            resp.update({"email_verified": False})
                        else:
                            print("TEMP: email verified")
                            resp.update({"email_verified": True})

                    if is_valid:
                        table.update_item(
                            Key={"user_id": user_id},
                            UpdateExpression="SET preferences.notifications.#type = :message_type",
                            ExpressionAttributeValues={":message_type": params["type"]},
                            ExpressionAttributeNames={"#type": "type"},
                            ReturnValues="UPDATED_NEW",
                        )
                        print(
                            "updated notification type preferences for "
                            + params["type"]
                        )
            else:
                print("(ROUTE: /preferences")
                parameters = {
                    "Key": {"user_id": user_id},
                    "UpdateExpression": f"SET preferences = :obj",
                    "ExpressionAttributeValues": {":obj": data},
                    "ReturnValues": "UPDATED_NEW",
                }
                resp = add_data(parameters)
            resp = success(msg=f'Dynamo UpdateItem Completed for "{route}"', extra=resp)
        elif "/logs" in route:
            data = loadBase64Json(event["body"])
            print(data)
            parameters = {
                "Key": {"user_id": user_id},
                "UpdateExpression": f"SET logs = list_append(logs, :obj)",
                "ExpressionAttributeValues": {":obj": [data]},
                "ReturnValues": "UPDATED_NEW",
            }
            resp = add_data(parameters)
        elif "/identities/tagdetectedimage" in route:
            key = params["key"]
            name = params["name"]

            data = get_blacklist_images(user_id)

            index = get_index_of_blacklist_image(key, data)
            print(
                f"(2. index of detected frame and metadata): index:{index}  camera_id: {data['blacklist'][index]['metadata']['camera_id']}"
            )

            if index != -1:
                remove_blacklist_record(index, user_id, key)
                print(f"(3. Remove image from artefacts table): key:" + key)
                response = add_image_to_profiles(key, name)
                print(f"(4. Add image to profiles): response:{resp}")
                resp = success(
                    msg="Image Successfully added to Whitelist", extra=response
                )
        elif "/identities/watchlist" in route:
            # get parameters
            key = params["key"]
            message = params["message"]
            watch = params["watch"]

            print(
                f"(1. parameters):  whitelist key:{key}  custom message:{message}  to watch:{watch}"
            )

            # get whitelist data
            client = boto3.client("dynamodb", region_name="af-south-1")

            response = client.query(
                TableName="Artefacts",
                KeyConditionExpression=f"user_id = :user_id",
                ProjectionExpression="profiles",
                ExpressionAttributeValues={":user_id": {"S": user_id}},
            )

            print("(2. get profile frames): response:" + str(response))

            data = from_dynamodb_to_json(response["Items"][0])

            print(f"(2.1. Deserialised Data: {data}")

            # no frames in the database
            if len(data["profiles"]) > 0:
                # get the index of the element to be update in the UserData table based on the user_id and the key element
                index = -1
                for count, x in enumerate(data["profiles"]):
                    if data["profiles"][count]["key"] == key:
                        index = count
                        break
                if index != -1:
                    print(f"(2. index of whitelist image to update): index:{index}")

                    client = boto3.resource("dynamodb")
                    table = client.Table("Artefacts")

                    response = table.update_item(
                        Key={
                            "user_id": user_id,
                        },
                        UpdateExpression=f"SET profiles[{index}].monitor = :i",
                        ExpressionAttributeValues={
                            ":i": {"custom_message": message, "watch": int(watch)}
                        },
                        ReturnValues="UPDATED_NEW",
                    )

                    resp = success(
                        msg="Whitelist image successfully added to watchlist",
                        extra=response,
                    )

                    print(
                        f"(3. Updated inserted whitelist image response): response:{str(resp)}"
                    )
                else:
                    resp = error(
                        msg=f"Whitelist image does not exist in the current whitelist list.",
                        extra={"event": event},
                    )
            else:
                resp = error(
                    msg=f"There are currently no images in the whitelist list.",
                    extra={"event": event},
                )
        else:
            resp = error(
                msg=f"Method not implemented yet. Tell Armin to get off his arse and do this: {route}",
                extra={
                    "event": event,
                    "post-body": loadBase64Json(event["body"]),
                },
            )
    except Exception as e:
        print(str(e))
        resp = error(f'Could not complete operation due to this error: "{str(e)}"')

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(resp, cls=DecimalEncoder),
    }
