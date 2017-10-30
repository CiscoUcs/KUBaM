# Kickstart Primer

Kickstart is an automated way to install CentOS and RedHat.  Kickstart may be older than you!  We've been using it since 2001 but its probably been around much longer than that!

To test with we don't want to wait for servers to boot up and POST so using Virtual Box is a great way to speed up testing. 



## Virtual Box settings

Create a new VM and use the NAT network.  Then change the boot settings so that it provisions from the network after the hard drive.  

Really, just following [these instructions](https://github.com/defunctzombie/virtualbox-pxe-boot) are really all you need.  Notice that Virtual Box can provide it's own DHCP/TFTP service in the NAT so there is no need for you to have to install another server to do this.  

Using those instructions we can modify the files in the 
```~/Library/VirtualBox/TFTP```

If we have a VM named ks-test then we do a ```ln -s pxelinux.0 ks-test.pxe```

To change what ks file it uses (as well as OS) you can update the ```pxelinux.cfg/default``` file.  