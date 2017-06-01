# Ansible playbook and roles to create a simple Kubernetes cluster with kubeadm and Contiv

## Credit
This work was built upon by [@iceworld](https://github.com/iceworld/)

## Support
Right now this works with RedHat 7.3 & CentOS 7.3

Please open an issue if you have problems.

## Configuration

### Step 0: Prerequisites
This Ansible script is stage 3 in the installation method of [KUBaM](https://ciscoucs.github.io/kubam/) which installs Kubernetes on Bare Metal UCS.  

The UCS servers should be installed and you should be able to ssh into the servers without a password. 

### Step 1: Edit inventory
Once the machines are installed with CentOS 7.3 or RedHat 7.3, you can put the node names in the 
```inventory/hosts``` file.   

At present we are set up to support 1 management server and no limits on the amount of nodes. (Though we have only tested up to 3 nodes!)

Verify that you can now reach these nodes by running: 

```
    ansible -m ping cluster
```
If this doesn't work, fix things until it does. 

### Step 2: Edit Variables

In ```group_vars/all.yml``` you need to change the following: 

* ```master_ip_address*``` This should be the IP address of your master node.  This is used by the nodes to join the master cluster. 
* ```ntp_server``` This is the time server you wish to use. It's important that all nodes have the same time.
* ```*proxy``` this is the proxy variables if you are behind a firewall. If you don't require a proxy, then you can just delete these variables or set them to ```''``

### Step 3: Run the scripts


```
ansible-playboook cluster.yml
```
This will go through and install your nodes. 


## Notes

This playbook implements the steps described in [Installing Kubernetes on Linux with kubeadm](http://kubernetes.io/docs/getting-started-guides/kubeadm/)

Currently contiv only supports kubeadm 1.6.0-beta and uses Kubernetes version 1.5.4.  Once contiv supports higher release then this will be supported. 


## Acknowlegements

* The man:  [@iceworld](https://github.com/iceworld)
* Huge kudos to the authors of kubeadm and [its getting started guide](http://kubernetes.io/docs/getting-started-guides/kubeadm/)
* Joe Beda [provided the code to generate tokens, and how to feed a token into kubeadm init](https://github.com/upmc-enterprises/kubeadm-aws/issues/1)
* @marun pointed me to the documentation about how to access the master remotely via kubectl

## Contributing

Pull requests and issues are welcome.












