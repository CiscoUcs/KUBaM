# KUBaM API Server

The API server aims to consolidate the work on stage1 and stage2 into an automated API. 

## To start the API server:

```
git clone https://github.com/CiscoUcs/KUBaM.git
cd api-server
python api.py
```
This will launch the application on port 5000.  

## API

You can test the API with the following: 

### Status Page

```
curl -X GET localhost:5000
```
Should get you: 

```
{
  "status": "ok"
}
```
### Session

#### Viewing current session:

```
curl -i localhost:5000/api/v1/session
```
Returns: 

```
{
  "credentials": {
    "password": "REDACTED",
    "server": "",
    "user": ""
  }
}
```

To login: 

```
curl -X POST -H "Content-Type: application/json"  -d '{"credentials" : {"user": "admin", "password" : "nbv12345", "server" : "172.28.225.163" }}' localhost:5000/api/v1/session
```
Returns either: 

```
{
  "error": "Error logging into UCS."
}
```

Or: 

```
{
  "login": "success"
}
```

#### Deleting a Session


```
curl -X DELETE localhost:5000/api/v1/session
```

### Networks

To get the UCS Networks so they can be used in creating all networks. 

```
curl -X GET -H "Content-Type: application/json"  localhost:5000/api/v1/networks
```

You should be logged in before using this method. Returns the names of the VLANs:

```
200
{
  "vlans": [
    "default",
    "hx-inband-mgmt",
    "hx-vmotion",
    "hx-data",
    "Docker-Data",
    "Docker-storage",
    "hx-storage-data",
    "vm-network"
  ]
}
```

Or 

```
401
{
  "error": "not logged in to UCS"
}
```