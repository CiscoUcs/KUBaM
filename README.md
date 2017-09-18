# KUBaM!
Kubernetes on UCS Bare Metal

## Introduction
You believe the hype: Kubernetes is the future.  Containers are where its at and you're ready to tear everything down and go all in with Kube.  Great, so how do you get that kubernetes goodness working on your shiny UCS platform?  And more important: How do you automate that so it works every time?  We want infrastructure as code right?  Isn't that the future as well (even though its actually the past and present as well?)

That is where KUBaM comes in.  We want to guide you through the 4 stages of Kubernetes.

## Stage 1 - Prepare
You need an OS on your UCS system.  To prepare the OS deployment environment we propose you use [PXEless automated installs](https://communities.cisco.com/community/technology/datacenter/compute-and-storage/ucs_management/blog/2017/04/25/pxe-less-automated-installation-of-centosredhat-on-ucs). This is something UCS can do that no other server can.  Aren't you glad you've got UCS? 

## Stage 2 - UCS Bare Metal Deployment
You need to automated the UCS configuration and land the host OS.  There are several ways to do this.  Using the UCS Python SDK is the way to go at the present.  But be on the lookout for us to release Terraform and Ansible installers for this stage.  Once past this stage, you have your Operating system deployed. 

## Stage 3 - Kubernetes Installation
Once the vanilla OS is up, its time to get Kubernetes going!  How to do that?  Configuration management tools.  Currently we use Ansible for this stage. 

## Stage 4 - Day 2+ Operations
You're up and running!  At this point, just configure your ```kubectl``` command to make this work.  Get a dashbaord, setup some monitoring and it's on!

Ready to begin?  Then [get started with the official documentation](https://ciscoucs.github.io/kubam/)
