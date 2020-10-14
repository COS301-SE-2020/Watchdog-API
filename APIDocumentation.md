# Watchdog API Documentation

The following documentation details the routes, methods and transactions (in both request and response) facilitated by the Watchdog API with a provided guide on how to build a valid request to each possible  to receive a valid response. 
It is worth noting that all OPTIONS methods exist purely to accommodate the integrative preflights of AWS and cannot be interacted with by the user, hence they won't be discussed in this documentation.

## /analytics/dashboard 

### GET 

Description:
The method which returns the dashboard of the user's analytics.

Parameters:
- end_date

## /analytics/profiles 

### GET 

Description: 
The method which returns the structured data of the profiles of the user's analytics.

Parameters:
- end_date
- interval

## /cameras 

### DELETE 

Description:
The method to remove a camera registered on the Home Control Panel.

Parameters:
- location
- site_id
- camera_id

### GET 

Description:
The method  to fetch all cameras and their subsequent details from the DynamoDB records (this includes their location, site_id, camera_id, metadata, etc.).

Parameters:
- camera_id (optional)
- site_id (optional)

### POST 

Description:
The method to register a new camera to the Home Control Panel and provide its necessary information.

Parameters:
- location
- site_id
- camera_id

### PUT 

Description: 
The method to update the details of a specified camera.

Parameters: 
- location (optional)
- metadata (optional)

## /controlpanel 

### DELETE 

Description:
The method to remove a registered Home Control Panel.

Parameters:
- site_id
### GET 

Description:
The method to fetch all Home Control Panels registered to the user and their subsequent information (site_id, metadata, etc.).

Parameters:
- site_id (optional)

### POST 

Description:
The method to register a new Home Control Panel to the user and their account and provide its necessary information.

Parameters:
- site_id

## /detectintruder 

### GET 

Description:
The method to fetch all whitelisted identities, security preferences, notification preferences and other metadata. 

Parameters:
None. 

## /identities 

### DELETE 

Description:
The method to remove an identity from the user's identities records.

Parameters:
- index
- type

### GET 

Description:
The method to fetch all identities, both of whitelisted and blacklisted nature, accompanied with their relevant profile data in the API response.

Parameters:
- identityname (optional)

## /identities/tagdetectedimage 

### GET 

Description:
The method to fetch the tagged detected images relevant to an identity. 

Parameters:
None. 

### POST 

Description:
The method to upload a tagged detected image relevant to an identity. The uploaded data will also be evaluated against the blacklisted images and their indexes. If an index is found, the blacklist record is removed and an image is added to a whitelisted profile. 

Parameters:
- key
- name

## /identities/upload 

### POST 

Description:
The method to upload frames from an event and correlate this with the appropriate user data.

Parameters:
- filename
- name

## /identities/watchlist 

### POST 

Description:
The method to add a watchlist that will keep watch over certain selected profiles.

Parameters:
- key
- watch
- message (optional)

## /logs 

### GET 

Description:
The method to fetch all logs and their related metadata from the user's system.

Parameters:
None. 

### POST 

Description:
The method to append data (in base64 format) to the logs in the user's system.

Parameters:
No requirements in the request body.

## /preferences 

### DELETE 

Description:
The method to remove the configured preferences of the user (such as security or notifications) and reset them to default.

Parameters:
None.

### GET 

Description:
The method to retrieved all configured preferences of the user.

Parameters:
None. 

### POST 

Description:
The method to configure and tweak desirable preferences and store these in the user's profile.

Parameters:
None.

## /preferences/notifications 

### POST 

Description:
The method to select the preferences for the user's notifications (such as its frequency, the nature of the notifications and how it is received, etc.).

Parameters:
None.

## /preferences/notifications/verify 

### POST 

Description:
The method to register a verification model (and authorisation methods) regarding the notifications of the user .

Parameters:
None.

## /preferences/securitylevel 

### GET 

Description:
The method to retrieve the security level of the system based on the user's configured preferences.

Parameters:
None. 

### POST 

Description:
The method to configure a desired security level by means of the preferences interface of the user.

Parameters:
None.

## /sites 

### DELETE 

Description:
The method to remove a site which the user has provided at a specified location.

Parameters:
- location
- site_id

### GET 

Description:
The method to fetch sites registered by the user on the system.

Parameters:
- site_id (optional)

### POST 

Description:
The method to register a new site to which a user can employ Watchdog's security system.

Parameters:
- site_id

## /storage/upload 

### POST 

Description:
The method to upload a clip to the specified storage location from a specific camera and its feed.

Parameters:
- camera_id
- user_id
- filename
- tag

## /storage/video 

### GET 

Description:
The method to fetch the videos from the artefacts table.

Parameters:
None.

## /ui/recordings 


### GET 

Description:
The method to fetch all recordings from a specific location and project them to the user interface.

Parameters:
None.

## /user 

### DELETE 

Description:
The method to terminate a user's account.

Parameters:
- user_id

### GET 

Description:
The method to fetch a user and its subsequent profile data from the system.

Parameters:
None. 

### POST 

Description:
The method to register a new user for a Watchdog account.

Parameters:
- user_id
 




















