import boto3
import json
import base64
import os
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.client import Config


s3 = boto3.client('s3', config=Config(signature_version='s3v4'))
rekognition = boto3.client('rekognition', region_name=os.environ['REKOGNITION_REGION'])


def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}    
    

def get_training_locations(user_id):
    client = boto3.client('dynamodb', region_name='af-south-1')
            
    response = client.query(
        TableName='UserData',
        ProjectionExpression='preferences.notifications, preferences.security_level',
        KeyConditionExpression=f'user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': {"S": user_id}
        }
    )
    
    data = from_dynamodb_to_json(response['Items'][0])
    preferences = data['preferences']['notifications']
    security_level = int(data['preferences']['security_level'])
    
    response = client.query(
        TableName='Artefacts',
        ProjectionExpression='profiles',
        KeyConditionExpression=f'user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': {"S": user_id}
        }
    )
    
    data = from_dynamodb_to_json(response['Items'][0])
    training_set = data['profiles']

    print("(3. Get user details): preferences:"+str(preferences)+" training set images:"+str(training_set) +" security_level:"+str(security_level))
    return preferences, training_set, security_level


def is_owner(sources, target, bucket):
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
                print("(5.a compare faces (training set & detected image)): Owner Identified:{source image:"+source+", target image:"+target+"}")
                return True, index, source
    print("(5.a compare faces (training set & detected image)): Owner NOT Identified: target image:"+target)
    return False, -1, None


def send_sms(number, link, message=None):
    sns = boto3.client("sns", region_name="eu-west-1")
    if message is None:
        message = "Please be aware that you may be experiencing a potential breach! View the detected image at the following link: "+link
    else:
        message = message + " View the detected image at the following link: "+link
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
        </p>
        <p>
            Detected Image:
        </p>
        <p>
            
            <img src="{link}" alt="Image Expired">
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
                'Data': "",
            },
        },
        Source="lynk.solutions.tuks@gmail.com",
    )


def generate_presigned_link(key):
    response = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': 'intruder.analysis',
            'Key': key
        },
        ExpiresIn=3600
    )
    
    return response   


def send_notification(preferences, target, send_to_security=True, custom_message=None):
    print("(5.b Send notificaiton to Owner & Security Company)")
    link = generate_presigned_link(target)
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
        if len(preferences['security_company'])>0:
            security_message = "One of your clients may have a potential breach! Please contact "+preferences['phone']+" immediately!"
            print(f"(5.b.2. Notify security): SMS:{security_message}; TO:{preferences['security_company']}")
            send_sms(preferences['security_company'], link)


def get_meta_data_from_event(event):
    bucket = os.environ['BUCKET']
    record = event['Records'][0]['s3']
    key = record['object']['key']
    metadata = s3.head_object(Bucket=bucket, Key=key)
    metadata = metadata['ResponseMetadata']['HTTPHeaders']
    return metadata['x-amz-meta-uuid'], key, metadata['x-amz-meta-camera_id'], metadata['x-amz-meta-timestamp'], metadata['x-amz-meta-token']


def remove_s3_object(key):
    response = s3.delete_object(
        Bucket = os.environ['BUCKET'],
        Key=key
    )
    print(f"(3. Delete detected false-positive): Key:{key}")


def add_detected_image_to_artefacts(key, uuid, camera_id, timestamp, io):
    client = boto3.resource('dynamodb', region_name='af-south-1')
    table = client.Table('Artefacts')
    
    if io:
        field = 'whitelist'
    else:
        field = 'blacklist'

    response = table.update_item(
        Key={
            'user_id': uuid,
        },
        UpdateExpression=f"SET {field} = list_append({field}, :i)",
        ExpressionAttributeValues={
            ":i": [
                {
                    'key': key,
                    'timestamp':timestamp,
                    'metadata': {
                        'camera_id':camera_id
                    }
                    # 'aid': hash(f'{key}-{uuid}'),
                }
            ]
        },
        ReturnValues="UPDATED_NEW"
    )
    print(f"(7. Add detected image key to artifacts): Key:{key};    is owner:{io};    field:{field}    camera id:{camera_id}")
    return response

def append_log(message, user_id, token, key, camera_id):
    timestamp = str(datetime.now().timestamp())
    data = {
        'tag': 'detected',
        "message":message,
        "timestamp": timestamp,
    }

    client = boto3.resource('dynamodb',region_name='af-south-1')
    table = client.Table('UserData')
    
    response = table.update_item(
        Key= {"user_id": user_id},
        UpdateExpression='SET logs = list_append(logs, :obj)',
        ExpressionAttributeValues={
            ":obj": [data]
        },
        ReturnValues="UPDATED_NEW"
    )
    
    print(f"(6. Append Log): Log message:{message};  timestamp:{timestamp}")


def get_detected_frames(user_id):
    time_gap = datetime.now() - timedelta(minutes=10)
    time_gap = str(time_gap.timestamp())
    
    client = boto3.client('dynamodb', region_name='af-south-1')
    
    response = client.query(
        TableName='Artefacts',
        ProjectionExpression='blacklist, whitelist',
        KeyConditionExpression=f'user_id = :user_id',
        ExpressionAttributeValues={
            ':user_id': {"S": user_id}
        }
    )
    detected_frames = from_dynamodb_to_json(response['Items'][0])
    detected_frames = detected_frames['whitelist']+detected_frames['blacklist']
    print("TEMP: response from getting whitelist and blacklist frames to check for uniqueness: "+str(detected_frames))
    
    frames_to_check = []
    for i in detected_frames:
        if i['timestamp'] > time_gap:
            frames_to_check.append(i)
    print(f"(2.2.1 Detected Frames in the past 10 min):  frames:{frames_to_check}")
    
    return frames_to_check
        

def is_detected_unique(user_id, target):
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
                print(f"(2.2.1 Detected image Uniqueness): Detected image is not unique: detected image:{target};   source image:{i['key']}")
                return False
    print(f"(2.2.1 Detected image Uniqueness): Detected image is unique: detected image:{target};")
    return True