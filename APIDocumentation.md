# Watchdog API Documentation

The following documentation details the routes, methods and transactions (in both request and response) facilitated by the Watchdog API with a provided guide on how to build a valid request to each possible route to receive a valid response. 
It is worth noting that all OPTIONS methods exist purely to accommodate the integrative preflights of AWS and cannot be interacted with by the user, hence they won't be discussed in this documentation.

## /analytics/dashboard Route

### GET method

Description:
The method which returns the dashboard of the user's analytics.

Parameters:
An end_date parameter is required to determine the time period from which the dashboard analytics is to be collected.

## /analytics/profiles Route

### GET method

Description: 
The method which returns the structured data of the profiles of the user's analytics.

Parameters:
There are two optional parameters of end_date and interval, which both dictate the period the data should be collected in and the intervals of the graph it is plotted against.

## /cameras Route

### DELETE method

Description:
The method to remove a camera registered on the Home Control Panel.

Parameters:
Location, site_id and camera_id parameters are required to uniquely identify the camera device to remove.

### GET method

Description:
The method to fetch all cameras and their subsequent details from the DynamoDB records (this includes their location, site_id, camera_id, metadata, etc.).

Parameters:
There are optional parameters of camera_id and site_id which can narrow down the data retrieved in the API response. 

### POST method

Description:
The method to register a new camera to the Home Control Panel and provide its necessary information.

Parameters:
Location, site_id and camera_id parameters need to be provided in the request body in order for the camera to be uniquely identified in other requests.

### PUT method

Description: 
The method to update the details of a specified camera.

Parameters: 
The parameters provided are those to be updated to the camera's DynamoDB record.

## /controlpanel Route

### DELETE method

Description:
The method to remove a registered Home Control Panel.

Parameters:
The site_id parameter is required to uniquely identify the Home Control Panel to remove.

### GET method

Description:
The method to fetch all Home Control Panels registered to the user and their subsequent information (site_id, metadata, etc.).

Parameters:
There are optional parameters of site_id which can narrow down the data retrieved in the API response. 

### POST method

Description:
The method to register a new Home Control Panel to the user and their account and provide its necessary information.

Parameters:
A site_id parameter needs to be provided in the request body in order for the Home Control Panel to be uniquely identified in other requests.

## /detectintruder Route

### GET method

Description:
The method to fetch all whitelisted identities, security preferences, notification preferences and other metadata. 

Parameters:
None. 

### POST method

Description:
This method has been deprecated.

Parameters:
N/A.

## /identities Route

### DELETE method

Description:
The method to remove an identity from the user's identities records.

Parameters:
index and type are required parameters, which identify a unique id of the profile data and whether the individual is whitelisted or blacklisted respectively.

### GET method

Description:
The method to fetch all identities, both of whitelisted and blacklisted nature, accompanied with their relevant profile data in the API response.

Parameters:
There are optional parameters of identityname which can narrow down the data retrieved in the API response. 

### POST method

Description:
This method is now deprecated.

Parameters:
N/A.

## /identities/tagdetectedimage Route

### GET method

Description:
The method to fetch the tagged detected images relevant to an identity. 

Parameters:
None. 

### POST method

Description:
The method to upload a tagged detected image relevant to an identity. The uploaded data will also be evaluated against the blacklisted images and their indexes. If an index is found, the blacklist record is removed and an image is added to a whitelisted profile. 

Parameters:
The key and name of the detected image are required, which will uniquely identify the image as well as its nature.

## /identities/upload Route

### POST method

Description:
The method to upload frames from an event and correlate this with the appropriate user data.

Parameters:
Filename and name are required parameters that provides the unique name of the file for the frame to be stored in and the unique name of the frame itself in the request body.

## /identities/watchlist Route

### POST method

Description:
The method to add a watchlist that will keep watch over certain selected profiles.

Parameters:
Required parameters of key (a unique identifier) and watch (an object to watch selected profiles). There is also an optional parameter of message which can give a custom string attached to the watchlist. 

## /logs Route

### GET method

Description:
The method to fetch all logs and their related metadata from the user's system.

Parameters:
None. 

### POST method

Description:
The method to append data (in base64 format) to the logs in the user's system.

Parameters:
No requirements in the request body.

## /preferences Route

### DELETE method

Description:
The method to remove the configured preferences of the user (such as security or notifications) and reset them to default.

Parameters:
None.

### GET method

Description:
The method to retrieved all configured preferences of the user.

Parameters:
None. 

### POST method

Description:
The method to configure and tweak desirable preferences and store these in the user's profile.

Parameters:
None.

## /preferences/notifications Route

### POST method

Description:
The method to select the preferences for the user's notifications (such as its frequency, the nature of the notifications and how it is received, etc.).

Parameters:
None.

## /preferences/notifications/verify Route

### POST method

Description:
The method to register a verification model (and authorisation methods) regarding the notifications of the user .

Parameters:
None.

## /preferences/securitylevel Route

### GET method

Description:
The method to retrieve the security level of the system based on the user's configured preferences.

Parameters:
None. 

### POST method

Description:
The method to configure a desired security level by means of the preferences interface of the user.

Parameters:
None.

## /sites Route

### DELETE method

Description:
The method to remove a site which the user has provided at a specified location.

Parameters:
Location and site_id are required parameters to uniquely identify the site to delete from the system.

### GET method

Description:
The method to fetch sites registered by the user on the system.

Parameters:
There are optional parameters of site_id which can narrow down the data retrieved in the API response. 

### POST method

Description:
The method to register a new site to which a user can employ Watchdog's security system.

Parameters:
A site_id parameter needs to be provided in the request body in order for the site to be uniquely identified in other requests.

## /storage/upload Route

### POST method

Description:
The method to upload a clip to the specified storage location from a specific camera and its feed.

Parameters:
camera_id, user_id, tag and filename are all required parameters which will be stored in the clip's data object. The camera_id identifies the camera from which it is uploaded, the user_id to identify the user to which the system is registered, the tag to identify the clip uploaded and the filename where it will be stored.

## /storage/video Route

### GET method

Description:
The method to fetch the videos from the artefacts table.

Parameters:
None.

## /ui/recordings Route


### GET method

Description:
The method to fetch all recordings from a specific location and project them to the user interface.

Parameters:
None.

## /user Route

### DELETE method

Description:
The method to terminate a user's account.

Parameters:
User_id will be required to identify the correct user to delete.

### GET method

Description:
The method to fetch a user and its subsequent profile data from the system.

Parameters:
None. 

### POST method

Description:
The method to register a new user for a Watchdog account.

Parameters:
This will be specified in the sign up page and are all required.
 
