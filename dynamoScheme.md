# Table 1: User Data

{
	"user_id": "unique string",
	"name": "string",
	"email": "string",
	"phone": "string",
	"preferences": {
		"bucket_size_limit": int
	},
	"control_panel": {
		"site_id": {
			"physical_address": "string",
			"broadcast_ip": ""
			"cameras": {
				"camera_id": {
					"home_location": "string",
					"ip_address": {
						"protocal": "",
						"address": "",
						"port": "",
						"path": ""
					},
					"alert_log": {
						"alert_hash" : {
							"time": "",
							"message": "",
							"path": ""
							"level": ""
						}
					}
				}
			}
		}
	},
}

# Table 2: Artifacts

{
	"path": "unique",
	"metadata":{}
}
