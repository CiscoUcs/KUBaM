#!/usr/bin/env python
# this script does the following: 
# 1.  Read in a configuration file. 
# 2.  Create a kickstart file based on a template
# 3.  Create an image from that kickstart file to be used to boot a UCS.
import os
from socket import inet_aton, error as Serror
from jinja2 import Environment, FileSystemLoader
from subprocess import call

# constants.  
KUBAM_DIR="/kubam/"
KUBAM_SHARE_DIR="/usr/share/kubam/"
BASE_IMG=KUBAM_SHARE_DIR+"/stage1/ks.img"
TEMPLATE_DIR=KUBAM_SHARE_DIR+"/templates/"
TEMPLATE_FILE="centos7-ks.tmpl"

# takes in a hash of configuration data and validates to make sure
# it has the stuff we need in it. 
def validate_ip(ip):
    err = 0
    try:
        inet_aton(ip)
    except Serror: 
        print "IP %s is not a valid IP address." % ip
        err +=1
    return err
def validate_nodes_config(nodes):
    err = 0
    for n in nodes:
        if "ip" in n:
            err += validate_ip(n["ip"])
        else:
            print "Node doesn't have IP address defined."
            err += 1
        if not "name" in n:
            print "missing Node Name in config file."
            err +=1
    return err

def validate_network(network):
    err = 0
    for item in ["netmask", "gateway", "nameserver"]:
        if item in network:
            err += validate_ip(network[item])
        else:
            print "Network doesn't have %s defined." % item
            err +=1
    return err

def validate_config(config):
    errors = 0
    if "masterIP" in config:
        errors += validate_ip(config["masterIP"])
    else:
        print "masterIP not found in config file."
        errors += 1

    if "nodes" in config: 
        errors += validate_nodes_config(config["nodes"])     
    else:
        print "nodes not found in config file."
        errors += 1
    if "network" in config: 
        errors += validate_network(config["network"])
    else:
        print "network not found in config file." 
        errors += 1
    if errors > 0:
        print "Invalid config file. See documentation at http://kubam.io"
        config = ""
    return config

# get the config file and parse it out so we know what we have. 
def parse_config(file_name):
    import yaml
    config = ""
    try: 
        with open(file_name, "r") as stream: 
            try: 
                config = yaml.load(stream)
            except yaml.YAMLError as exc:
                print "Error parsing %s config file: " % file_name
                print(exc)
                return ""
        stream.close()
    except IOError as err:
        print file_name, err.strerror
    return validate_config(config)

def build_template(node, j2_env, config):
    f = j2_env.get_template(TEMPLATE_FILE).render(
        masterIP=config["masterIP"],
        ip=node["ip"],
        name=node["name"],
        netmask=config["network"]["netmask"],
        nameserver=config["network"]["nameserver"],
        gateway=config["network"]["gateway"],
        keys=config["public_keys"] 
    )
    return f
    
# build the kickstart images
def build_boot_image(node, template):
    new_image_name = KUBAM_DIR + node["name"] + ".img"
    new_image_dir = KUBAM_DIR + node["name"] 
    # cp the file to the directory. 
    o = call(["cp" , "-f", 
                BASE_IMG,
                new_image_name])
    if not o == 0: 
        return 1 
    # create mount point. 
    o = call(["mkdir" , "-p", new_image_dir])
    if not o == 0: 
        return 1 
    # use fuse to mount the image. 
    # e.g: fuseext2 kube01.img kube01 -o rw+,nonempty
    o = call(["fuseext2", "-o", "rw+,nonempty",
                new_image_name, new_image_dir,])
    if not o == 0:
        return 1
    
    # write the file over the existing file if it exists. 
    # hack to over write file 
    fw = new_image_dir + "/ks1.cfg"
    fw_real = new_image_dir + "/ks.cfg"
    try: 
        with open(fw, 'w') as f:
            f.write(template)
    except IOError as err:
        print file_name, err.strerror
        return 1

    # mv this file to ks.cfg
    o = call(["mv", fw, fw_real])            
    if not o == 0:
        return 1

    # unmount the filesystem. 
    o = call(["umount", new_image_dir])            
    if not o == 0:
        return 1
    # remove mount directory
    o = call(["rm", "-rf", new_image_dir])
    if not o == 0:
        return 1
    return 0
    

config = parse_config(KUBAM_DIR + "stage1.yaml")
if config == "":
    exit(1)

j2_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                     trim_blocks=True)
for node in config["nodes"]:
    template = build_template(node, j2_env, config)
    rc = build_boot_image(node, template)
    if rc == 1:
        break
