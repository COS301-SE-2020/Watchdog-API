import boto3
import json
import base64
import os
from boto3.dynamodb.conditions import Key
import requests
import datetime


def is_human(photo, bucket, rekognition):
    # df = base64.b64decode(ef)
    response = rekognition.detect_labels(
        Image={
            # "Bytes":df
            'S3Object': {
                'Bucket': os.environ['BUCKET'],
                'Name': photo
            }
        },
        MaxLabels=10,
        MinConfidence=75
    )
    # check to see if human is identified and has confidence > 75
    for label in response['Labels']:
        if label['Name'] == "Person" and label['Confidence'] > 90:
            print("(2. Identify if detected image is human): Label:" + label['Name'] + "; Confidence:" + str(
                label['Confidence']) + "  --->  is human = True")
            return True
    print("(2. Identify if detected image is human):  --->  is human = False")
    return False


def get_training_locations(uuid, token):
    # Integration
    response = requests.get(
        os.environ['USER_DATA_URL'],
        params={
            'user_id': uuid
        },
        headers={'Authorization': token}
    )
    response = json.loads(response.text)
    training_set = response['data']['identities']['whitelist']
    preferences = response['data']['preferences']['notifications']
    security_level = int(response['data']['preferences']['security_level'])
    print("(3. Get user details): preferences:" + str(preferences) + " training set images:" + str(
        training_set) + " security_level:" + str(security_level))
    return preferences, training_set, security_level


def is_owner(sources, target, bucket, rekognition):
    response = False
    if len(sources) > 0:
        for source in sources:
            source = source['key']
            response = rekognition.compare_faces(
                SourceImage={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': source
                    }
                },
                TargetImage={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': target
                    }
                }
                # QualityFilter='NONE'|'AUTO'|'LOW'|'MEDIUM'|'HIGH'
            )
            if len(response['FaceMatches']) > 0:
                print("(5.a compare faces (training set & detected image)): Owner Identified:{source image:" + source + ", target image:" + target + "}")
                return True
    print("(5.a compare faces (training set & detected image)): Owner NOT Identified: target image:" + target)
    return False


def send_sms(number, link, message=None):
    sns = boto3.client("sns", region_name="eu-west-1")
    if message is None:
        message = "Please be aware that you may be experiencing a potential breach! View the detected image at the following link: " + link
    sns.publish(PhoneNumber=number, Message=message)
    print("sms sent to " + number)


def send_email(recipient, link):
    BODY_HTML = f"""<html>
    <head></head>
    <body>
        <h1>Intruder Detected</h1>
        <p>
            Please note that detection of a possible intruder has been captured 
            on your camera. View the   
            <a href={link}>detected image</a>
        </p>
    </body>
    </html>
    """
    client = boto3.client('ses',region_name='eu-west-1')
    response = client.send_email(
        Destination={
            'ToAddresses': [
                recipient,
            ],
        },
        Message={
            'Body': {
                'Html': {
                    'Charset': "UTF-8",
                    'Data': BODY_HTML,
                },
            },
            'Subject': {
                'Charset': "UTF-8",
                'Data': "Intruder Detected on property!",
            },
        },
        Source="lynk.solutions.tuks@gmail.com",
    )


def generate_presigned_link(key, s3):
    print("key: " + key)
    response = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': 'intruder.analysis',
            'Key': key
        },
        ExpiresIn=3600
    )

    print("(link for image in notificaiton): link: " + response)
    return response


def send_notification(preferences, target, s3):
    print("(5.b Send notificaiton to Owner & Security Company)")
    link = generate_presigned_link(target, s3)
    type = preferences['type']
    if type == 'sms':
        message = "Intruder detected"
        send_sms(preferences['value'], link)
        print(f"(5.b.1. Notify Owner) SMS:{message}; TO:{preferences['value']}")
    elif type == 'email':
        send_email(preferences['value'], link)
        print(f"(5.b.1. Notify Owner) Email recipient:{preferences['value']}")
    elif type == 'push':
        pass
    if len(preferences['security_company']) > 0:
        security_message = "One of your clients may have a potential breach! Please contact " + preferences[
            'value'] + " immediately!"
        print(f"(5.b.2. Notify security): SMS:{security_message}; TO:{preferences['security_company']}")
        send_sms(preferences['security_company'], link)


def get_meta_data_from_event(event, s3):
    bucket = os.environ['BUCKET']
    record = event['Records'][0]['s3']
    key = record['object']['key']
    metadata = s3.head_object(Bucket=bucket, Key=key)
    metadata = metadata['ResponseMetadata']['HTTPHeaders']
    return metadata['x-amz-meta-uuid'], key, metadata['x-amz-meta-camera_id'], metadata['x-amz-meta-timestamp'], \
           metadata['x-amz-meta-token']


def remove_s3_object(key, s3):
    response = s3.delete_object(
        Bucket=os.environ['BUCKET'],
        Key=key
    )
    print(f"(3. Delete detected false-positive): Key:{key}")


def add_detected_image_to_artefacts(key, uuid, camera_id, timestamp):
    client = boto3.resource('dynamodb', region_name='af-south-1')
    table = client.Table('Artefacts')
    path_in_s3 = os.environ['OBJECT_URL'] + key

    print(f"(7. Add detected image key to artifacts): Key:{key};    path in s3:{path_in_s3};    camera id:{camera_id}")
    response = table.update_item(
        Key={
            'user_id': uuid,
        },
        UpdateExpression="SET frames = list_append(frames, :i)",
        ExpressionAttributeValues={
            ":i": [
                {
                    'aid': hash(f'{key}-{uuid}'),
                    'metadata': {
                        'camera_id': camera_id,
                        'timestamp': timestamp
                    },
                    'path_in_s3': path_in_s3
                }
            ]
        },
        ReturnValues="UPDATED_NEW"
    )
    return response


def append_log(message, user_id, token):
    timestamp = str(datetime.datetime.now().timestamp())
    map = {
        "message": message,
        "timestamp": timestamp
    }
    response = requests.post(
        os.environ['LOGS_URL'],
        params={
            'user_id': user_id,
        },
        data=json.dumps(map),
        headers={'Authorization': token}
    )
    print(f"(6. Append Log): Log message:{message};  timestamp:{timestamp}")
    

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    # get parameters from s3 object
    uuid, target, camera_id, timestamp, token = get_meta_data_from_event(event, s3)
    print(
        f"(1. Parameters): Detected Image: {target}; User ID: {uuid}; camera id:{camera_id}   timestamp:{timestamp}   token:{token}")
    bucket = os.environ['BUCKET']
    
    # define rekognition resource
    rekognition = boto3.client('rekognition', region_name=os.environ['REKOGNITION_REGION'])
    owner = False
    # response = "The image that was detected is not a human!"
    if is_human(target, bucket, rekognition):
        # face has been detected in detected image - now compare it to other images from user uploads
        preferences, training_set, security_level = get_training_locations(uuid, token)

        if security_level == 0:  # Disarmed ( no notifications are sent)
            print("(4. security level): level:0;   description:Disarmed;   action:no notifications are sent")
            log_message = "Watchdog has identified movement"
        elif security_level == 1:  # Recognised Only (so intruder notifications are sent)
            print(
                "(4. security level): level:1;   description:Recognised Only;   action:notifications are sent if the detected image is an owner")
            if not is_owner(training_set, target, bucket, rekognition):
                send_notification(preferences, target, s3)
                log_message = "Watchdog has identified a possible intruder, and has sent out a notificaiton!"
            else:
                owner = True
                log_message = "Watchdog has identified the owner in your feed!"
        else:  # Armed (notifications are sent for any face detected)
            print("(4. security level): level:2;   description:Armed;   action:notifications are sent")
            send_notification(preferences, target, s3)
            log_message = "Watchdog has identified a face in your feed. if this is your face, consider changing your security to level 1, security has been notified"

        append_log(log_message, uuid, token)

        response = "Intruder Detected!"
    else:
        owner = True

    if owner:
        # remove object from s3 - either an owner or image is false-positive
        remove_s3_object(target, s3)
        response = "Owner has been identified :)"
    else:
        # add to Dynamo DB - artifacts
        add_detected_image_to_artefacts(target, uuid, camera_id, timestamp)

    resp = {
        "response": response
    }
    respObj = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": resp
    }

    return respObj
