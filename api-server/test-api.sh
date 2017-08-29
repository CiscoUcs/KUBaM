#!/bin/bash

# get welcome page.
curl -X GET http://localhost

# get current session
curl -X GET http://localhost/api/v1/session

#logout
curl -X DELETE http://localhost/api/v1/session

# login
curl -X POST -H "Content-Type: application/json"  -d '{"credentials" : {"user": "admin", "password" : "nbv12345", "server" : "172.28.225.163" }}' http://localhost/api/v1/session

# Get UCS Networks
curl -X GET -H "Content-Type: application/json"  http://localhost/api/v1/networks

# Get UCS servers
curl -X GET -H "Content-Type: application/json"  http://localhost/api/v1/servers

# Get ISO images
curl -X GET -H "Content-Type: application/json"  http://localhost/api/v1/isos

# Test ISO extract
curl -H "Content-Type: application/json" -X POST -d '{"iso" : "Vmware-ESXi-6.5.0-4564106-Custom-Cisco-6.5.0.2.iso", "os": "esxi6.5" }' http://localhost/api/v1/isos/extract

# Test Make BOOt ISO
curl -H "Content-Type: application/json" -XPOST -d '{"iso" : "CentOS-7-x86_64-Minimal-1611.iso" }' http://localhost/api/v1/isos/boot
