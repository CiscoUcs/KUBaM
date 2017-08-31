# KUBaM API Server

The API server aims to consolidate the work on stage1 and stage2 into an automated API. 

## Running in a Container

```
mkdir ~/kubam
cd ~/kubam
wget <latest ISO image>
docker run -p 80:80 -d -v `pwd`:/kubam \
	--device /dev/fuse \
	--cap-add SYS_ADMIN \
	--name kubam \
	kubam/kubam
```
Notice that the docker command will mount the current directory where the ISO is.  This makes it so we can run and start the ISO file. 

If you want to change the code while developing run it as follows: 


```
export KUBAM_DIR=~/Downloads/kubam
export APP_DIR=~/Code/KUBaM/api-server/app
docker run -p 80:80 -d -v $KUBAM_DIR:/kubam \
   -v $APP_DIR:/app \
	--device /dev/fuse \
	--cap-add SYS_ADMIN \
	--name kubam \
	kubam/kubam
```

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
    {
      "name": "default",
      "vlan-id": "3095"
    },
    {
      "name": "hx-inband-mgmt",
      "vlan-id": "1"
    },
    ...
}
```

Or 

```
401
{
  "error": "not logged in to UCS"
}
```

### UCS Servers

```
curl -i -X GET -H "Content-Type: application/json"  localhost:5000/api/v1/servers
```

Output:

Gives you the list of servers in the system: 

```
{
  "servers": [
    {
      "chassis_id": "1",
      "model": "UCSB-B200-M4",
      "slot": "slot-1",
      "type": "blade"
    },
    {
      "chassis_id": "1",
      "model": "UCSB-B200-M3",
      "slot": "slot-3",
      "type": "blade"
    },
    ...
	]
}
```

### ISO images

#### List the Current ISO images

```
curl -H "Content-Type: application/json" \
 -X GET
http://localhost/api/v1/isos
```

#### Extract ISO image for use

```
curl -H "Content-Type: application/json" \
 -X POST \
 -d '{"iso" : "Vmware-ESXi-6.0.0-5050593-Custom-Cisco-6.0.3.2.iso" }' \
http://localhost/api/v1/isos/boot
```

### Boot Images

KUBAM creates boot images for the servers to boot from.  Depending on the operating, this boot image may be a ```.img``` or a ```.iso``` file. 

```
curl -H "Content-Type: application/json" \
-X POST \
http://localhost/api/v1/servers/images
```
This will create the images. This operation may take a long time depending on the operating system as it goes through and builds images.  Still a work in progress. 

This operation requires the ```kubam.yaml``` file to be in place.  


## Running Test Cases

See this [post for help](https://stackoverflow.com/questions/1896918/running-unittest-with-typical-test-directory-structure)

```
cd app
python -m unittest discover
```