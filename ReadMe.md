#  API DOCUMENTATION 
### COMPOSITION OF AN API ROUTE 
The API Gateway service facilitates all requests by the client of multiple routes and sources.
To use and display the interactions present (request and response) in the system, provide the necessary query string specified in the Method Request tab, using the standard formating of ? to start the query and the ampersand symbol (&) to separate different query parameters.
The Integration Request type specifies the nature of how the transaction will be handled and by which service (such as lambda proxy or mock functionality). 
 After the endpoint is used to facilitate the request, the response begins to form.
The Integration Response tab controls the HTTP response headers, the mapping of the responses (the JSON body and its content) as well as the output passthrough.
The Method Response tab lists all the known responses that the route can generate (such as 200 for OK or 500 for Internal Server Error) and will provide the appropriate response based on the results of the request's processing. 
### HOW TO USE (TEST PHASE) 
To use a route in API Gateway, make sure to follow these procedures:
For GET and DELETE requests, make sure to provide the necessary parameters in the query string in order to get the desired response and/or actions to execute.
For POST and UPDATE requests, make sure to provide the correctly formatted request body in JSON (also ensuring that all required fields are filled and have valid data) in order to have a successful execution.
### DEPLOYING THE API
The API Gateway, once deployed, will use request URLs which can be accessed and requested in the browser to call that route and its functions and provide a response to the client. These URLs can either be used in a browser address bar (with the appropriate query strings for GET and DELETE requests), used in Postman (a third party application) for POST and UPDATE requests and their request bodies or as a cURL. 
### OTHER INFORMATION 
There are authorisation mechanisms on each route (enforced by AWS Cognito and authorised user pools) that will check on each API call that the address making the API call is of a valid and verified user.
There are resource policies written in the API Gateway configuration detailing the permissions that developers of the Watchdog system had and accesses to data and services, as well as the permissions that entail the API Gateway itself. 
