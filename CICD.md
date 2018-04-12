### Drone CI/CD

adding secrets is done with 

```
drone secret add -repository CiscoUcs/KUBaM -image vallard/drone-spark -name SPARK_TOKEN -value YmI...
drone secret add -repository CiscoUcs/KUBaM -image 
drone secret add -repository CiscoUcs/KUBaM -image plugins/docker -name docker_username -value kubam
drone secret add -repository CiscoUcs/KUBaM -image plugins/docker -name docker_password -value mysecret

drone secret add -repository CiscoUcs/KUBaM -image appleboy/drone-ssh -name ssh_password -value secretpasswrd
```
