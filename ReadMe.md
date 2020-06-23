# Routes needed:

- Live Streaming:
	- Request Stream
		- Auth user
		- Encrypt stream

- Installation Requests
	- Register IP Camera (IP Address) to user
	- ?? Configuration ?? (Camera Calibration?)

- CRUD
	- Read + Delete will have least parameters

# TODO:

- [] Create API Specification
- [] Integrate with Cognito
- [] Configure backed functionaily (such as Dynamo)

# Why OpenAPI? 

OpenAPI grants us the opportunity to have a standard interface with no language constraints and no prerequisites to neither user or server to have access to or have accessed the source code or documentation in order to understand the operations and services provided by the RESTful API. It empowers all users regardless of their knowledge in APIs and their implementations to be able to make informed requests and interact further with the remote service. 

Additionally, OpenAPI also has the ability to display the API by means of documentation tools that use its definition. It also allows functionalities to generate servers using code generation tools and facilitate testing using an appropriate testing kit. 
