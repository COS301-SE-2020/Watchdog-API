import json

print("getCameras function")


def lambda_handler(event, context):
    #user_id = event["queryStringParameters"]["user_id"]
    # token = event["queryStringParameters"]["usertoken"]

    # print("the user id provided was " + user_id)
    # print("the token provided was " + token)

    resp = {
        "status": "OK",
        "data": {
            "cameras":[
                {
            		"camera_id": "qwerrtyrtyudfhdfg",
            		"name": "Bathroom"
            	},
            	{
            		"camera_id": "zxcvzsdfgadfgasfg",
            		"name": "Main Bedroom"
            	},
            	{
            		"camera_id": "qwasdsdfgsertgsdf",
            		"name": "Kitchen"
            	}
            ]
            
        }
    }
    respObj = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp)
    }

    return respObj