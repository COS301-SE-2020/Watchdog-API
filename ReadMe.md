# Usage

```python
import os
import json
import requests
import pprint
from warrant.aws_srp import AWSSRP
```

### Step 1: Get Token if you haven't previously

- _client_id_ = id of the Client App (In this caase the HomeControlPanel in Cognito)
- _user_pool_id_ = Watchdog User Pool id

This gives you _tokens_ which is a dict object with the Access token, Refresh Token, and Id Token

The Access Token can always be found in: 

```python
    tokens["AuthenticationResult"]["AccessToken"]
```
And this needs to to be send as a _Authorization_ Header


```python
client_id="5bl2caob065vqodmm3sobp3k7d"
client_secret = None
user_pool_id = "eu-west-1_mQ0D78123"

aws = AWSSRP(username='test', password='Test123@', pool_id=user_pool_id,
             client_id=client_id, pool_region='eu-west-1')
tokens = aws.authenticate_user()
```

### Step 2: Call to API Gateway to aquire prefilled link for S3

- *_get_location_url_* is the route in the api
- *_upload_key_* is the name of the artifact
- *_folder_* is the folder you would like to store it in

This gives you the S3 resource location to upload to according to the parameters you provided along with all the nessesary Authorization and Access parameters you would need to upload it.

**In order to access the API Gateway you need the token in Step 1 to be Appended to the Header of the Request as the value 'Authorization'**


```python
get_location_url = "https://la7nxehzwg.execute-api.af-south-1.amazonaws.com/alphav2/live/uploadclip/"
upload_key = "test_prefilled_post.txt"
folder = "video"
```


```python
resp = requests.post(get_location_url, params={"upload_key": upload_key, "folder": folder}, headers={'Authorization': f'TOK:{tokens["AuthenticationResult"]["AccessToken"]}'})
print(f'{resp} : {resp.reason}')
```


```python
response_dict = json.loads(resp.text)
```

### Step 3: Upoad Artifact to S3 bucket

> Use the native 'post' request provider (such as axios or ajax etc)

The url and parameters from the prefilled link must be given as parameters in this request otherwise you will get a Fobidden error.

- Note: No header needed for S3 upload


```python
http_response = None
with open(upload_key, 'rb') as binary_object:
    files = {'file': (upload_key, binary_object)}
    http_response = requests.post(response_dict['url'], data=response_dict['fields'], files=files)
```


```python
print(f'{http_response}: {http_response.reason}')
```

Please see [UsageExample (Jupyter Notebook)](/UsageExample.ipynd) 

# Why OpenAPI? 

OpenAPI grants us the opportunity to have a standard interface with no language constraints and no prerequisites to neither user or server to have access to or have accessed the source code or documentation in order to understand the operations and services provided by the RESTful API. It empowers all users regardless of their knowledge in APIs and their implementations to be able to make informed requests and interact further with the remote service. 

Additionally, OpenAPI also has the ability to display the API by means of documentation tools that use its definition. It also allows functionalities to generate servers using code generation tools and facilitate testing using an appropriate testing kit. 
