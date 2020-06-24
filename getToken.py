import json

print("getToken function")


def gettoken_handler(event, context):
    username = event["queryStringParams"]["username"]
    password = event["queryStringParams"]["password"]
    print("the user name provided was " + username)
    resp = {}
    resp["token"] = "slemtgf87weeuoasjhfuiew"
    resp["message"] = "Token has been generated!"

    respObj = {}
    respObj["statuscode"] = 200
    respObj["headers"] = {}
    respObj["headers"]["Content-Type"] = "application/json"
    respObj["body"] = json.dumps(resp)

    return respObj