import boto3
import json
import base64
import os
from boto3.dynamodb.conditions import Key
import requests

print("DetectIntruder function using detected image being uploaded into S3")

def is_human(photo, bucket, rekognition):
    # df = base64.b64decode(ef)
    response =  rekognition.detect_labels(
        Image={
            # "Bytes":df
            'S3Object':{
                'Bucket':os.environ['BUCKET'],
                'Name':photo
            }
        },
        MaxLabels=10,
        MinConfidence=75
    )
    #check to see if human is identified and has confidence > 75
    for label in response['Labels']:
        if label['Name'] == "Person" and label['Confidence'] > 90:
            print("(2. Identify if detected image is human): Label:"+label['Name']+"; Confidence:"+str(label['Confidence'])+"  --->  is human = True")
            return True
    print("(2. Identify if detected image is human):  --->  is human = False")
    return False
    
def get_training_locations(uuid):
    # MOCK setup
    response = {
      "status": "OK",
      "data": [
        {
          "training": [
            "IMG_0269.jpeg",
            "stacey.png"
          ],
          "sns": {
            "security_company": "+27763165023",
            "type": "SMS",
            "value": "+27715100762"
          }
        }
      ]
    }
    # Integration
    # url = f"{os.environ['USER_DATA_URL']}"
    # print("getting preferences using "+url)
    # response = requests.get(
    #     os.environ['USER_DATA_URL'],
    #     params={
    #         'user_id':uuid
    #     }
    # )
    
    preferences = response['data'][0]['sns']
    training_set = response['data'][0]['training']
    print("(3. Get user details): preferences:"+str(preferences)+" training set images:"+str(training_set))
    return preferences, training_set


def is_owner(sources, target, bucket, rekognition):
    response = False
    if len(sources) > 0:
        for source in sources:
            source = os.environ['TRAINING_DIRECTORY']+source
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
                print("(4. compare faces (training set & detected image)): Owner Identified:{source image:"+source+", target image:"+target+"}")
                # may need to check if length of unmatched > 0 then the owner 
                # could be getting hold hostage!
                # could have levels of threats:
                # if owner is in image with an unregistered person:
                    # HIGH - still notify owner
                    # LOW - do not notify owner
                return True
    print("(4. compare faces (training set & detected image)): Owner NOT Identified: target image:"+target)
    return False
    
def send_sms(number, message=None):
    sns = boto3.client("sns", region_name="eu-west-1")
    if message is None:
        message = "Please be aware that you may be experiencing a potential breach!"
    sns.publish(PhoneNumber=number, Message=message)
    
def send_notification(preferences):
    # preferences: {'security_company': '+27810139351', 'type': 'SMS', 'value': '+27810139351'}
    print("(5. Send notificaiton to Owner & Security Company)")
    type = preferences['type']
    if type == 'SMS':
        message = "Please be aware that you may be experiencing a potential breach!"
        print(f"(5.1. Notify Owner) SMS:{message}; TO:{preferences['value']}")
        send_sms(preferences['value'], message)
    elif type == 'EMAIL':
        pass
    elif type == 'PUSH':
        pass
    security_message = "One of your clients may have a potential breach! Please contact "+preferences['value']+" immediately!"
    print(f"(5.2. Notify security): SMS:{security_message}; TO:{preferences['security_company']}")
    send_sms(preferences['security_company'], message)
    

def lambda_handler(event, context):
    # define parameter variables
    target = os.environ['DETECTED_DIRECTORY']+event['queryStringParameters']['image']
    bucket = os.environ['BUCKET']
    uuid = event['queryStringParameters']["user_id"]
    print(f"(1. Parameters): Detected Image: {target}; User ID: {uuid}")
    
    # define rekognition resource
    rekognition = boto3.client('rekognition', region_name=os.environ['REKOGNITION_REGION'])
    
    is_intruder = False
    if is_human(target, bucket, rekognition):
        # face has been detected in detected image - now compare it to other images from user uploads
        preferences, training_set = get_training_locations(uuid)
        if not is_owner(training_set, target, bucket, rekognition):
            send_notification(preferences)
            is_intruder = True
            
        if is_intruder:
            response = "Intruder Detected!"
        else:
            response = "Owner has been identified :)"
    response = "The image that was detected is not a human!"
    
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
