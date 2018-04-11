# test directory

This directory is for building the docker images required for drone CI/CD testing pipeline. 

```
docker build -t kubam/python-test . 
docker push kubam/python-test
```

This builds the test image for the CI/CD process.

The correct image should then be pulled on the build server for testing. 
