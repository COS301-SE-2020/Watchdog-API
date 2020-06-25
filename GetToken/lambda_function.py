import json

print("getToken function")


def gettoken_handler(event, context):
    username = event["queryStringParams"]["username"]
    password = event["queryStringParams"]["password"]
    print("the user name provided was " + username)
    resp = {
        "token": "slemtgf87weeuoasjhfuiew",
        "message": "Token has been generated!"
    }
    respObj = {
        "statuscode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(resp)
    }

    return respObj
