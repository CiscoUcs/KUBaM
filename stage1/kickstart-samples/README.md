# UCS Kickstart Files

There examples in this directory structure are kickstart files for RedHat and CentOS that we have tested for our UCS environments for KUBAM setups. 

The ```ks.cfg``` file in this directory is a simple configuration.  Notice that in UCS on RH7/CentOS7 the VICS show up as enpXs0.  Different configurations may validate which interface they show up under. 

### Amsterdam
The Amsterdam directory shows an example of Boot From SAN that also uses bonding drivers.  These files contain a ```%pre``` section that looks for the disk that the installation will go under.  

It runs the command:

```
disk=`ls /dev/disk/by-id/dm-name-3600* | head -1 | cut -d'-' -f4`
```
To find the right installation disk.  Since the NetApp array in our example maps to 3600* we used that as a way to find the correct disk.

```kube03``` server is different as that server has unconfigured local disks.  As such the ```ignoredisk --only-use``` field is different than the others.  We will most likely change that to make the servers consistent but we left this as an example to show what you might do if you had other disks.  From the [RH documentation](https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/Installation_Guide/sect-kickstart-syntax.html#sect-kickstart-commands) ```ignoredisk``` is required when attempting to deploy on a SAN-cluster. 