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
export APP_DIR=~/Code/KUBaM/kubam/app
docker run -p 80:80 -d -v $KUBAM_DIR:/kubam \
   -v $APP_DIR:/app \
	--device /dev/fuse \
	--cap-add SYS_ADMIN \
	--name kubam \
	kubam/kubam
```

## To start the API server without a container

```
git clone https://github.com/CiscoUcs/KUBaM.git
cd api-server
python api.py
```
This will launch the application on port 5000.  


## Architecture

The API server is a service that runs in a container that simplifies communication with UCS.  It uses the [UCSMSDK](https://github.com/CiscoUcs/ucsmsdk) which is written in python.  This is, frankly, the only reason this is written in python - There is no SDK for golang at the moment. 

The API when first starting will look for a YAML file called ```kubam.yaml``` in the ```/kubam``` directory.  If it is found then it will use those values to configure everything.  It will, however not deploy anything, it will wait for you to tell it to do that. 


## KUBAM ```kubam.yaml``` file

The yaml file will have the following format: 

```yaml
---
ucsm:
- credentials:
	 	ip: 172.28.226.163
	  	user: admin
	  	password: nbv12345
	  	
  ucs_server_pool:
		blades:
		  - 1/1
		  - 2/1
		rack_servers:
		  - 6
		  - 7
		  - 8
  ucs_network:
      vlan: default
 - credentials:
     ip: adsf.asdf.asdf.fas
     user: admin
     password: 230f3kf3jfj3f3f3f3
    	  
   ucs_network:
   	  vlan: default
  
kubam_ip: 172.28.225.135

iso_images:
- file: CentOS-7-x86_64-Minimal-1611.iso
  os: centos7.3

public_keys:
- "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDeV4/Sy+B8R21pKzODfGn5W/p9MC9/4ejFUJoI3RlobYOWWxbLmnHYbKmRHn8Jgpmm4xqv61uaFpbAZvxFTyKIqLdcYmxaHem35uzCJbgB8BvT+4aGg1pZREunX6YaE8+s3hFZRu4ti7UHQYWRD1tCizYz78YHL8snp+N3UAPmP9eTTNw62PHAJERi1Hbl6sRfYijqNlluO223Thqbmhtt3S8tnjkRsFnNxsDgxrfbR3GBQ5925hPth3lGejln2P1L9EIQw9NOmtMhF9UpXPWP9r234p3crmBTsw+E6IF0+OsGKOl8Ri4Im7GpnAgbY9I5THEDn142uNOm6vJATZZ3 root@devi-builder"
	
hosts:
  - server-group: blah
- name: esxi1
  ip: 172.28.225.132
  os: centos7.3
  role: kubernetes-master
- name: esxi2
  ip: 172.28.225.133
  os: centos7.3
  role: kubernetes-slave
  
network:
  netmask: 255.255.254.0
  gateway: 172.28.224.1
```


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


#### To select the network used for kubam deployment



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
 -d '{"iso" : "Vmware-ESXi-6.0.0-5050593-Custom-Cisco-6.0.3.2.iso", "os": "esxi6.0" }' \
http://localhost/api/v1/isos/extract
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

Or you can do it for individual unit test files

```
python2 -m unittest test.sg.SGUnitTests
python2 -m unittest test.test_db.DBUnitTests
python2 -m unittest test.test_app.FlaskTestCase
```

## Misc Dev Testing techniques

### Using the REPL

```
>>> from ucscsdk.ucschandle import UcscHandle
>>> from ucscsdk.ucscexception import UcscException
>>> handle = UcscHandle("10.94.132.71", "admin", "cisco.125")
>>> handle.login()
>>> b = handle.query_classid(class_id = "ComputeBlade")
>>> from ucscsdk.mometa.compute.ComputeBlade import ComputeBlade
>>> print(b[0])
```