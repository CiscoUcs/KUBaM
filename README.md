# KUBAM!

![Build Status](http://1db27123.ngrok.io/api/badges/CiscoUcs/KUBaM/status.svg?branch=v2.0)

Deploy Solutions on Cisco UCS with a Simple Open Source Light-Weight Bare Metal Installer

No PXE, DHCP, TFTP, or complicated network setup required. You don't even have to map MAC addresses. KUBAM turns your bare metal into liquid that can be molded and modified to satisfy all your deepest darkest datacenter requirements.

## Introduction
We started with a [blog on PXEless automated installs](https://communities.cisco.com/community/technology/datacenter/compute-and-storage/ucs_management/blog/2017/04/25/pxe-less-automated-installation-of-centosredhat-on-ucs). From there we evolved to an open source tool that could make this process easier.


Ready to begin?  Then [get started with the official documentation](https://ciscoucs.github.io/kubam/)



### Drone CI/CD

adding secrets is done with 

```
drone secret add -repository CiscoUcs/KUBaM -image vallard/drone-spark -name SPARK_TOKEN -value YmI...
drone secret add -repository CiscoUcs/KUBaM -image 
drone secret add -repository CiscoUcs/KUBaM -image plugins/docker -name docker_username -value kubam
drone secret add -repository CiscoUcs/KUBaM -image plugins/docker -name docker_password -value mysecret

drone secret add -repository CiscoUcs/KUBaM -image appleboy/drone-ssh -name ssh_password -value secret
```