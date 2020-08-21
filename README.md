# Watchdog - API

This repository contains all the code used in the API

### Watchdog Repositories
|[Home Control Panel](https://github.com/COS301-SE-2020/Watchdog)|API|[Web Application](https://github.com/COS301-SE-2020/Watchdog-FrontEnd/tree/master/watchdog-frontend)|[Mobile Application](https://github.com/COS301-SE-2020/Watchdog-FrontEnd/tree/master/WatchdogApp)|[Stream Server](hhttps://github.com/COS301-SE-2020/Watchdog-Stream-Server)|
|---|---|---|---|---|

### Project Description:

For the South African household who need an efficient way to ensure their safety and security the Watchdog system is a home security system that utilizes machine 
learning to identify an intruder and alert users and security companies on the potential breach. Unlike traditional surveillance systems that keep a backlog of 
redundant video storage our product utilizes machine learning and a modern cloud architecture to deliver a real-time security system.


### Demo Videos
- [LynkSolutions-Demo1](https://drive.google.com/file/d/1mdyx54MLTo0vTAEx2nm5wwFgWU_ULEks/view?usp=sharing)
- [LynkSolutions-Demo2](https://drive.google.com/file/d/1JfVWYLl65t5PzllO-vNKPR-YlOt7DRnX/view?usp=sharing)
- [LynkSolutions-Demo3](https://drive.google.com/file/d/1bSRqRJBJ-5sPx4G1vCkq2Al8BcTPFYOs/view?usp=sharing)


### Documentation
- [SRS Document - version 3](https://drive.google.com/file/d/1dWVx8BrT0Nt8GKdyHLqmjKYzg1aGlRWS/view?usp=sharing)
- [Technical Installation Manual](https://drive.google.com/file/d/1ouZquOIizf8omvOCnzMCG-wwS2qJyhzi/view?usp=sharing)
- [Watchdog User Manual](https://drive.google.com/file/d/1gu36_44IbnKeGjC61VaDXLu3mLKEqTvr/view?usp=sharing)
- [Coding Standards Document](https://drive.google.com/file/d/1X4IsmHWHwBjvmg1aaUua1HiC6rs6w5pO/view?usp=sharing)
- [Project Management Tool (Clubhouse)](https://app.clubhouse.io/lynksolutions/stories) (If you require access please email a team member and we will add you to our workspace, since clubhouse does not allow external viewing)


### Deployed Website Link:
- [Watchdog System](https://master.dtul6cza66juk.amplifyapp.com/)

<details><summary><h3>About the API</h3></summary>

### Composing an API Route


The API Gateway service facilitates all requests by the client of multiple routes and sources.
To use and display the interactions present (request and response) in the system, provide the necessary query string specified in the Method Request tab, using the standard formating of ? to start the query and the ampersand symbol (&) to separate different query parameters.
The Integration Request type specifies the nature of how the transaction will be handled and by which service (such as lambda proxy or mock functionality). 
 After the endpoint is used to facilitate the request, the response begins to form.
The Integration Response tab controls the HTTP response headers, the mapping of the responses (the JSON body and its content) as well as the output passthrough.
The Method Response tab lists all the known responses that the route can generate (such as 200 for OK or 500 for Internal Server Error) and will provide the appropriate response based on the results of the request's processing. 


Additionally, There are authorisation mechanisms on each route (enforced by AWS Cognito and authorised user pools) that will check on each API call that the address making the API call is of a valid and verified user.
There are resource policies written in the API Gateway configuration detailing the permissions that developers of the Watchdog system had and accesses to data and services, as well as the permissions that entail the API Gateway itself. 

##### Usage in Python

```python
import os
import json
import requests
import pprint
from warrant.aws_srp import AWSSRP
```

##### Step 1: Get Token if you haven't previously

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

aws = AWSSRP(username='Foo', password='Test@123', pool_id=user_pool_id,
             client_id=client_id, pool_region='eu-west-1')
tokens = aws.authenticate_user()
```

##### Step 2: Call to API Gateway to aquire prefilled link for S3

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
resp = requests.post(get_location_url, params={"upload_key": upload_key, "folder": folder}, headers={'Authorization': f'{tokens["AuthenticationResult"]["IdToken"]}'})
print(f'{resp} : {resp.reason}')
```


```python
response_dict = json.loads(resp.text)
```

##### Step 3: Upoad Artifact to S3 bucket

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

Please see [The notebook above](/PostRequestExample.ipynd) 

### Why OpenAPI? 

OpenAPI grants us the opportunity to have a standard interface with no language constraints and no prerequisites to neither user or server to have access to or have accessed the source code or documentation in order to understand the operations and services provided by the RESTful API. It empowers all users regardless of their knowledge in APIs and their implementations to be able to make informed requests and interact further with the remote service. 

Additionally, OpenAPI also has the ability to display the API by means of documentation tools that use its definition. It also allows functionalities to generate servers using code generation tools and facilitate testing using an appropriate testing kit. 

</details>

### How it Works

The API Gateway, once deployed, will use request URLs which can be accessed and requested in the browser to call that route and its functions and provide a response to the client. These URLs can either be used in a browser address bar (with the appropriate query strings for GET and DELETE requests), used in Postman (a third party application) for POST and UPDATE requests and their request bodies or as a cURL.

### Build Instructions:

**Prerequisites**:
- AWS Cli
- AWS SAM Cli
- Bash
- Jupyter Notebook
- A Watchdog Security System Account

1. Clone this repo
2. Change into the 'watchdog-api' directory ```cd watchdog-api```
3. Execute ```sam local start-api```
4. Use the provided Jupyter Notebook to access the API

### Members

|Member|Student #|Page|LinkedIn|
|------|---------|----|--------|
|Luqmaan Badat|17088519|<https://github.com/luqmaanbadat>|<https://www.linkedin.com/in/luqmaan-badat/>|
|Aboobakr Kharbai|u18037306|<https://abubakrk.github.io>|<https://www.linkedin.com/in/aboobacker-kharbai-7a94961a9/>|
|Jordan Manas|u17080534|<https://u17080534.github.io>|<https://www.linkedin.com/in/jordan-manas-b822651aa/>|
|Ushir Raval|u16013604|<https://urishiraval.github.io>| <https://www.linkedin.com/in/unraval/>|
|Jonathan Sundy|u18079581|<https://jsundy.github.io>|<https://www.linkedin.com/in/jonathen-sundy-79b33b168/>|
|Armin van Wyk|u18008632|<https://github.com/BigMacDaddy007>|<https://www.linkedin.com/in/armin-van-wyk-b714931a9/>|

<details>
<summary>
<h1>Profiles</h1>
</summary>

##### Luqmaan Badat

I am a final year computer science student. I am adaptable, reliable and keen to learn new programming technologies. My interests are software engineering, artificial intelligence and web development. My skills range include web development, full stack development, Java development and using full stack development technologies like docker and circleci. I’ve been exposed to and worked on cloud-based solutions in the medical field. 

##### Aboobakr Kharbai

My exposure ranges between desktop applications and web-based technologies. I am very reliable as well as trustworthy. I have a broad range of experience in backend development which includes database management systems, as well as experience in java development. I am one who is always steadfast in deadlines set out and will do anything in my capacity to ensure the work done is before the deadline and also of an industry standard.

##### Jordan Manas

An avid student of the numerous fields found within Computer Science, with a concentration in the field of Artificial Intelligence. Also being well-versed in Web Development, I recognize that I am capable of fulfilling important roles in the given project. I have experience in developing projects that use almost all of the proposed technologies and am very confident that our final product will be one of quality.

##### Ushir Raval

My exposure varies greatly from desktop applications to web based technologies, all in mostly a corporate “fintech” focused development environment. My skillset ranges from python development to web-based desktop applications using full stack technologies and my personal motto is “measure twice, cut once”. I prize scalable, robust and portable code above all else and intend to primarily contribute to the integration of various technologies such as the front-end to back-end communication etcetera.

##### Jonathan Sundy

I have been exposed to an event-driven system that adopted modern cloud architecture that was hosted on Heroku and used a subset of AWS. I will use this knowledge gained to pioneer the system to be loosely coupled that promotes independent events triggering different parts of the system. Hence, I am certain that I will be of great value to the development of the serverless architecture. I am not too coherent with AWS but am motivated and inspired to expand my knowledge!

##### Armin van Wyk

I have been involved in a multitude of projects inside and outside of the EBIT faculty. I have particular interest in front-end multimedia design to back-end REST API and hosting tasks. I have familiarity in databases both with and without SQ. I can use these skills in the request handling and data handling of our projects and ensure validated, clean and lightweight data.

</details>

