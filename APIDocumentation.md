# /cameras 

#### DELETE
> This removes the selected camera from the control panel
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?camera_id=<camera_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### GET
> This fetches the camera and its information using camera_id
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?camera_id=<camera_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "camera": "camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
}
}
```
#### POST
> Registers a camera to a control panel
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
		"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### PUT
> Updates a camera of a control panel
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?camera_id=<camera_id>```
- Request Body:
```json
{
		"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
}
```
> This is a mock function.

# /controlpanel

#### DELETE
> This removes the selected control panel from the user's account
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?site_id=<site_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### GET
> This fetches the control panel and its information using site_id
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?site_id=<site_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "control_panel": {
		"site_id": {
			"physical_address": "string",
			"broadcast_ip": "",
			"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
		}
	}
}
```
#### POST
> Registers a control panel to a user
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
	"control_panel": {
		"site_id": {
			"physical_address": "string",
			"broadcast_ip": "",
			"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
		}
	}
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### PUT
> Updates a control panel of a user
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?siteid=<site_id>```
- Request Body:
```json
{
	"control_panel": {
		"site_id": {
			"physical_address": "string",
			"broadcast_ip": "",
			"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
		}
	}
}
```
> This is a mock function.

# /detectintruder

#### GET
> This fetches the trained images from the AWS services.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "data": [
        {
            "training": [
                "trained images come in here"
            ],
            "sns": {
                "security_company":     "$item.preferences.M.sns.M.security_company.S",
                "type": "$item.preferences.M.sns.M.type.S",
                "value": "$item.preferences.M.sns.M.value.S"
            }

        }
    ]
}
}
```
#### POST
> Uploads a detected image to S3
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
	"image": "<base64 encoding>",
     "user_id": "string"
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
# /identities

#### DELETE
> This removes the selected identity from the user's whitelist
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?identity_name=<identity_name>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### GET
> This fetches the identities whitelisted by the user.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "identities": [
		{
			"path_in_s3":"",
			"name": "",
			"role": ""
		}
	]
}
```
#### POST
> Registers a identity to whitelist
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
		"identities": [
		{
			"path_in_s3":"",
			"name": "",
			"role": ""
		}
]
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### PUT
> Updates the list of whitelisted identities
Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Request Body:
```json
{
      
	"identities" : 	{
			"path_in_s3":"",
			"name": "",
			"role": ""
		}

}
```
> This is a mock function.

# /preferences

#### DELETE
> This removes the preferences of the user
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### GET
> This fetches the preferences configured by the user
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "preferences": {
		"historical": {
			"clip_length": 1,
			"clip_gap": 1
		}
	}
}
```
#### POST
> Configures preferences of the user.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
     "preferences": {
		"historical": {
			"clip_length": integer,
			"clip_gap": integer
		}
	}
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### PUT
> Updates the preferences.
Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Request Body:
```json
{
      "preferences": {
		"historical": {
			"clip_length": integer,
			"clip_gap": integer
		}
	}

}
```
> This is a mock function.

# /sites


#### DELETE
> This removes the selected site from the user's account
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?site_id=<site_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### GET
> This fetches the site requested by the user.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?site_id=<site_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "site": {
		"site_id": {
			"physical_address": "string",
			"broadcast_ip": "",
			"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
		}
	}
}
```
#### POST
> Registers a site to the user. 
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
	"site": {
		"site_id": {
			"physical_address": "string",
			"broadcast_ip": "",
			"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
		}
	}

}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### PUT
> Updates the site.
Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?site_id=<site_id>```
- Request Body:
```json
{
      	"site": {
		"site_id": {
			"physical_address": "string",
			"broadcast_ip": "",
			"cameras": {
				"camera_id": {
					"name": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					}
				}
			}
		}
	}

}
```
> This is a mock function.

# /storage 

#### DELETE
> This deletes the artefact item in storage (dynamoDB)
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### GET
> This fetches the artefacts from the camera requested.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?camera_id=<camera_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "artefact" : {
    "camera_id": "unique",
  "frames": [
    {
      "aid": "",
      "metadata": {
        "ttl": "x"
      },
      "path_in_s3": ""
    }
  ],
  "videos": [
    {
      "aid": "a",
      "metadata": {
        "ttl": "x"
      },
      "path_in_s3": "b",
      "tag": "intruder"
    }
  ]
}
}
```
#### POST
> An artefact is uploaded to storage. 
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
	"artefact" : {
    "camera_id": "unique",
  "frames": [
    {
      "aid": "",
      "metadata": {
        "ttl": "x"
      },
      "path_in_s3": ""
    }
  ],
  "videos": [
    {
      "aid": "a",
      "metadata": {
        "ttl": "x"
      },
      "path_in_s3": "b",
      "tag": "intruder"
    }
  ]
}
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
# /storage/upload

#### POST
> A clip is uploaded from a camera. 
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
	"file_name": "string",
      "type": "string"
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
# /storage/video

#### GET
> This fetches the video from a camera.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?camera_id=<camera_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "data": {
        camera_id: [
            {
            	"videos": [
            		{
            			"aid": "string",
            			"path_in_s3": "string",
            			"metadata": {
                  		    "tag": "string"
                       			}
            		}
                     	]
            	
            }
        ]
    }
}
```
# /user

#### DELETE
> This removes the user's account
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### GET
> This fetches user and their account information.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK",
    "data": {
        	"user_id": "unique string",
        	"name": "string",
        	"email": "string",
        	"phone": "string",
        	"identities": [
        		{
        			"path_in_s3":"",
        			"name": "",
        			"role": ""
        		}
        	],
        	"preferences": {
        		"historical": {
        			"clip_length": 1,
        			"clip_gap": 1
        		}
        	},
        	"control_panel": {
        		"site_id": {
        			"physical_address": "string",
        			"broadcast_ip": "",
        			"cameras": {
        				"camera_id": {
        					"name": "string",
        					"ip_address": {
        						"protocal": "",
        						"address": "",
        						"port": "",
        						"path": ""
        					}
        				}
        			}
        		}
        	},
        }

}
```
#### POST
> A user registers on the Watchdog system.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```None```
- Request Body:
```json
{
	"name": "string",
	"email": "string",
	"phone": "string",
     "password" : "string"
}
```
- Response:
```json
Header1: something
Header2: something

{
    "status": "OK"
}
```
#### PUT
> Updates a user's profile.
- Headers:
```json
{
    "Authorization": "<Cognito Access-Tocken>"
}
```
- Query Parameters: ```/?user_id=<user_id>```
- Request Body:
```json
{
	"name": "string",
	"email": "string",
	"phone": "string",
	"identities": [
		{
			"path_in_s3":"",
			"name": "",
			"role": ""
		}
	],
	"preferences": {
		"historical": {
			"clip_length": integer,
			"clip_gap": integer
		}
	}
}
```
> This is a mock function.

























