import boto3
import json
import base64
import os
from boto3.dynamodb.conditions import Key
import requests
from datetime import datetime, timedelta
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer


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
            print("(2.1 Identify if detected image is human): Label:" + label['Name'] + "; Confidence:" + str(
                label['Confidence']) + "  --->  is human = True")
            return True
    print("(2.1 Identify if detected image is human):  --->  is human = False")
    return False


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}


def get_training_locations(user_id):
    client = boto3.client('dynamodb', region_name='af-south-1')

    response = client.query(
        TableName='UserData',
        ProjectionExpression='identities.whitelist, preferences.notifications, preferences.security_level',
        KeyConditionExpression=f'user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': {"S": user_id}
        }
    )

    data = from_dynamodb_to_json(response['Items'][0])

    training_set = data['identities']['whitelist']
    preferences = data['preferences']['notifications']
    security_level = int(data['preferences']['security_level'])
    print("(3. Get user details): preferences:" + str(preferences) + " training set images:" + str(
        training_set) + " security_level:" + str(security_level))
    return preferences, training_set, security_level


def is_owner(sources, target, bucket, rekognition):
    response = False
    if len(sources) > 0:
        index = -1
        for source in sources:
            index = index + 1
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
                print(
                    "(5.a compare faces (training set & detected image)): Owner Identified:{source image:" + source + ", target image:" + target + "}")
                return True, index, source
    print("(5.a compare faces (training set & detected image)): Owner NOT Identified: target image:" + target)
    return False, -1, None


def send_sms(number, link, message=None):
    sns = boto3.client("sns", region_name="eu-west-1")
    if message is None:
        message = "Please be aware that you may be experiencing a potential breach! View the detected image at the following link: " + link
    else:
        message = message + " View the detected image at the following link: " + link
    # if phone[0] is not plus
    # add +27 and remove the first digit
    sns.publish(
        PhoneNumber=number,
        Message=message,
        MessageAttributes={
            'AWS.SNS.SMS.SenderID': {
                'DataType': 'String',
                'StringValue': 'Watchdog'
            },
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            }
        }
    )


def send_email(recipient, link, message=None):
    if message is None:
        data = "Intruder Detected on property!"
        message = "Please note that detection of a possible intruder has been captured on your camera feed."
    else:
        data = "Someone in your watchlist has been detected"

    BODY_HTML = f"""<html>
    <head></head>
    <body>
        <h1>Intruder Detected</h1>
        <p>
            {message}
            Click the following link to view the <a href={link}>detected image</a>
        </p>
    </body>
    </html>
    """
    client = boto3.client('ses', region_name='eu-west-1')
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
                'Data': "",
            },
        },
        Source="lynk.solutions.tuks@gmail.com",
    )


def generate_presigned_link(key, s3):
    response = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': 'intruder.analysis',
            'Key': key
        },
        ExpiresIn=3600
    )

    return response


def send_notification(preferences, target, s3, send_to_security=True, custom_message=None):
    print("(5.b Send notificaiton to Owner & Security Company)")
    link = generate_presigned_link(target, s3)
    type = preferences['type']
    if type == 'sms':
        message = "Intruder detected"
        send_sms(preferences['phone'], link, custom_message)
        print(f"(5.b.1. Notify Owner) SMS:{message}; TO:{preferences['phone']}")
    elif type == 'email':
        send_email(preferences['email'], link, custom_message)
        print(f"(5.b.1. Notify Owner) Email recipient:{preferences['email']}")
    elif type == 'push':
        pass
    if send_to_security:
        if len(preferences['security_company']) > 0:
            security_message = "One of your clients may have a potential breach! Please contact " + preferences[
                'phone'] + " immediately!"
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
                    'path_in_s3': path_in_s3,
                    'key': key
                }
            ]
        },
        ReturnValues="UPDATED_NEW"
    )
    print(f"(7. Add detected image key to artifacts): Key:{key};    path in s3:{path_in_s3};    camera id:{camera_id}")
    return response


def append_log(message, user_id, token, key, camera_id):
    timestamp = str(datetime.now().timestamp())
    map = {
        'tag': 'detected',
        "message": message,
        "timestamp": timestamp,
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
    

def get_detected_frames(user_id):
    client = boto3.client('dynamodb', region_name='af-south-1')
    response = client.query(
        TableName='Artefacts',
        ProjectionExpression='frames',
        KeyConditionExpression=f'user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': {"S": user_id}
        }
    )

    detected_frames = from_dynamodb_to_json(response['Items'][0])
    time_gap = datetime.now() - timedelta(minutes=10)
    time_gap = str(time_gap.timestamp())
    frames_to_check = []
    detected_frames = detected_frames['frames']
    for i in detected_frames:
        if i['metadata']['timestamp'] > time_gap:
            frames_to_check.append(i)
    print(f"(2.2.1 Detected Frames in the past 10 min):  frames:{frames_to_check}")
    return frames_to_check


def is_detected_unique(user_id, target, rekognition):
    print(f"(2.2 Get detected frames to see uniqueness): user_id:{user_id}; detected image:{target}")
    detected_frames = get_detected_frames(user_id)
    if len(detected_frames) > 0:
        for i in detected_frames:
            response = rekognition.compare_faces(
                SourceImage={
                    'S3Object': {
                        'Bucket': os.environ['BUCKET'],
                        'Name': target
                    }
                },
                TargetImage={
                    'S3Object': {
                        'Bucket': os.environ['BUCKET'],
                        'Name': i['key']
                    }
                }
                # QualityFilter='NONE'|'AUTO'|'LOW'|'MEDIUM'|'HIGH'
            )
            if len(response['FaceMatches']) > 0:
                print(
                    f"(2.2.1 Detected image Uniqueness): Detected image is not unique: detected image:{target};   source image:{i['key']}")
                return False
    print(f"(2.2.1 Detected image Uniqueness): Detected image is unique: detected image:{target};")
    return True


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
    if is_human(target, bucket, rekognition) and is_detected_unique(uuid, target, rekognition):
        # face has been detected in detected image - now compare it to other images from user uploads
        preferences, training_set, security_level = get_training_locations(uuid)
        if security_level == 0:  # Disarmed ( no notifications are sent)
            print("(4. security level): level:0;   description:Disarmed;   action:no notifications are sent")
            log_message = "Watchdog has identified movement"
        elif security_level == 1:  # Recognised Only (so intruder notifications are sent)
            print(
                "(4. security level): level:1;   description:Recognised Only;   action:notifications are sent if the detected image is an owner")
            io, index, source = is_owner(training_set, target, bucket, rekognition)
            if not io:
                send_notification(preferences, target, s3)
                log_message = "Watchdog has identified a possible intruder, and has sent out a notificaiton!"
            else:
                owner = True
                log_message = "Watchdog has identified the owner in your feed!"
                if training_set[index]['monitor']['watch']:
                    send_notification(preferences, target, s3, False, training_set[index]['monitor']['custom_message'])
                    owner = False
        else:  # Armed (notifications are sent for any face detected)
            print("(4. security level): level:2;   description:Armed;   action:notifications are sent")
            send_notification(preferences, target, s3)
            log_message = "Watchdog has identified a face in your feed. if this is your face, consider changing your security to level 1, security has been notified"

        append_log(log_message, uuid, token, target, camera_id)
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
