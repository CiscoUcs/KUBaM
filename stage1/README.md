# KUBaM stage 1

Stage 1 is the first part of installing Kubernetes on UCS.  In this stage we build the web server that will be used to automate the installation. 

To automate the installation of UCS nodes we require an automated web server.  The web server is built with a container image.  Because we aren't allowed to distribute a Linux Image, we ask that the user point us to media as part of the installation process.  

## Docker Files

The Dockerfile here is for building the container which will house the webserver.  The initial script follows the documentation outlined at the [KUBaM stage1 manual documentation](https://ciscoucs.github.io/kubam/stage1/manual)

To build the docker image run: 

```
docker build -t kubam/stage1-server . 
```
Then to run the docker image we use: 

```
docker run -d -p 80:80 \
-v <my directory with CentOS iso file>:/kubam/ \
--name kubam1 kubam/stage1-server
```
Note that before running the image, you should ensure that you have an ISO linux of CentOS 7 Minimal in your directory.  You can get that image [here](http://isoredirect.centos.org/centos/7/isos/x86_64/CentOS-7-x86_64-Minimal-1611.iso)

Running ```docker logs stage1-server``` will allow you to see what is happening as the server builds. 
