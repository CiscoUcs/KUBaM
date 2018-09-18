# Docker Directory

This directory is for building the docker images required for drone CI/CD testing pipeline. 

## Test Directory

```
cd test
docker build -t kubam/python-test . 
docker push kubam/python-test
```


This builds the test image for the CI/CD process.

The correct image should then be pulled on the build server for testing. 

## Base Directory

We've split out the heavy lifting of kubam and the dependencies.  The base file makes the creation of the new KUBAM image go faster as these 
requirements in this directory do not change often. 
