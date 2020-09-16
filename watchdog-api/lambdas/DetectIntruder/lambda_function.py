from helper_functions import *


def lambda_handler(event, context):
    # get parameters from s3 object
    uuid, target, camera_id, timestamp, token = get_meta_data_from_event(event)
    print(
        f"(1. Parameters): Detected Image: {target}; User ID: {uuid}; camera id:{camera_id}   timestamp:{timestamp}   token:{token}")
    bucket = os.environ['BUCKET']

    # define rekognition resource
    owner = False
    response = "Person was identified within the last 10 minutes and will not be processed again"
    if face_detected(target) and is_detected_unique(uuid, target):
        # face has been detected in detected image - now compare it to other images from user uploads
        preferences, training_set, security_level = get_training_locations(uuid)

        io, index, source = is_owner(training_set, target, bucket)

        if security_level == 0:  # Disarmed ( no notifications are sent)
            print("(4. security level): level:0;   description:Disarmed;   action:no notifications are sent")
            log_message = "Watchdog has identified movement"
        elif security_level == 1:  # Recognised Only (so intruder notifications are sent)
            print(
                "(4. security level): level:1;   description:Recognised Only;   action:notifications are sent if the detected image is an owner")
            if not io:
                send_notification(preferences, target)
                log_message = "Watchdog has identified a possible intruder, and has sent out a notificaiton!"
            else:
                log_message = "Watchdog has identified the owner in your feed!"
                if training_set[index]['monitor']['watch']:
                    send_notification(preferences, target, False, training_set[index])
        else:  # Armed (notifications are sent for any face detected)
            print("(4. security level): level:2;   description:Armed;   action:notifications are sent")
            send_notification(preferences, target)
            log_message = "Watchdog has identified a face in your feed. if this is your face, consider changing your security to level 1, security has been notified"

        append_log(log_message, uuid, token, target, camera_id)
        response = "Intruder Detected!"

        # add to Dynamo DB - artifacts
        add_detected_image_to_artefacts(target, uuid, camera_id, timestamp, io, source)
    else:
        # person is detected within 10 minutes, therefore, do not save image
        remove_s3_object(target)

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
