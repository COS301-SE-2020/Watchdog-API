import requests
import json
import unittest
from warrant.aws_srp import AWSSRP
from functools import wraps

client_id="5bl2caob065vqodmm3sobp3k7d"
client_secret = None
user_pool_id = "eu-west-1_mQ0D78123"
pool_region = 'eu-west-1'
username = 'Foo'
password = 'Test@123'



# data = requests.get(url=baseUrl.format('user'), headers=headers).text
# data = json.loads(data)
# print(data)


class TestGets(unittest.TestCase):
    pass

class TestPosts(unittest.TestCase):
    pass

class TestDeletes(unittest.TestCase):
    pass

if __name__ == '__main__':
    global api
    aws = AWSSRP(username=username, password=password, pool_id=user_pool_id,
                 client_id=client_id, pool_region=pool_region)

    tokens = aws.authenticate_user()
    token = tokens["AuthenticationResult"]["IdToken"]

    baseUrl = 'https://aprebrte8g.execute-api.af-south-1.amazonaws.com/testing/{}'
    headers = {
        "Authorization": f'{token}'
    }

    def gatewayRequest(route, params=None):
        if params is None:
            return json.loads(requests.get(url=baseUrl.format(route), headers=headers).text)
        else:
            return  json.loads(requests.get(url=baseUrl.format(route), headers=headers, params=params).text)
        api = {}

    with open('api_description.json', 'rb') as fl:
        api = fl.read()

    api = str(api, 'utf-8')
    api = json.loads(api)

    def add_method(cls, name):
        def decorator(func):
            @wraps(func) 
            def wrapper(self, *args, **kwargs): 
                print("NAME: "+name + "API: "+ api[name])
                return func(name, *args, **kwargs)
            setattr(cls, name, wrapper)
            # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
            return func # returning func means func can still be used normally
        return decorator

    base = api["host"] + api["basePath"]

    for i, route in enumerate(api["paths"]):
        feature = route.replace('/', '')
        api[f'test_{feature}'] = route
        print(f'ROUTE: {route} => test_{feature}')
        @add_method(TestGets, f'test_{feature}')
        def test(name):
            print("FUNCT NAME: "+name)
            data = gatewayRequest(api[name])
            print(f'TESTING /GET {base}{api[name]}\n')
            if "get" in api['paths'][api[name]].keys() and "parameters" not in api['paths'][api[name]]["get"]:
                # print(data)
                assert 'OK' in data['status']
            else:
                assert 'message' in data

        @add_method(TestPosts, f'test_{feature}')
        def test(name):
            print("FUNCT NAME: "+name)
            data = gatewayRequest(api[name])
            print(f'TESTING /POST {base}{api[name]}\n')
            if "get" in api['paths'][api[name]].keys() and "parameters" not in api['paths'][api[name]]["get"]:
                # print(data)
                assert 'OK' in data['status']
            else:
                assert 'message' in data

        @add_method(TestDeletes, f'test_{feature}')
        def test(name):
            print("FUNCT NAME: "+name)
            data = gatewayRequest(api[name])
            print(f'TESTING /DELETE {base}{api[name]}\n')
            if "get" in api['paths'][api[name]].keys() and "parameters" not in api['paths'][api[name]]["get"]:
                # print(data)
                assert 'OK' in data['status']
            else:
                assert 'message' in data

    unittest.main()
