#!/usr/bin/env python
# this script does the following: 
# 1.  Read in a configuration file. 
# 2.  Create a kickstart file based on a template
# 3.  Create an image from that kickstart file to be used to boot a UCS.
from socket import inet_aton, error as Serror
from jinja2 import Environment, FileSystemLoader
from subprocess import call
from os import path
from sshpubkeys import SSHKey, InvalidKeyException

# constants.  
supported_oses = ["centos7.3", "esxi6.0", "esxi6.5", "rh7.3"]

# makes sure that the list of ISO images actually exists. 
def validate_iso_images(iso_images):
    for i in iso_images:
        if i == None:
            return 1, "empty value not accepted."
        elif not "file" in i and not "os" in i:
            return 1, "iso must have an 'os' value and a 'file' value"
        elif not i["os"] in supported_oses:
            return 1, "%s is not a supported OS." % i["os"]
        elif not path.isfile(i["file"]):
            return 1, "%s file is not found." % i["file"]
    return 0, ""
        
        

# validate list of public keys
def validate_pks(key_list):
    err = 0
    msg = ""
    
    for k in key_list:
        if k == None:
            return 1, "No Key was passed in."
        ssh = SSHKey(k, strict_mode=True)
        try: 
            ssh.parse()
        except InvalidKeyException as err:
            err +=1
            msg = msg + "\nInvalid SSH Public Key:" % k
    return err, msg
        

# takes in an OS and verifies it's something we support
def validate_os(op_sys):
    rc = 0
    msg = ""
    if not op_sys in supported_oses:
        rc = 1
        msg = "%s is not a supported OS.  Supported OSes are: %s" % (op_sys, " ".join(supported_oses))
    return rc, msg
    
    
# takes in a hash of configuration data and validates to make sure
# it has the stuff we need in it. 
def validate_ip(ip):
    err = 0
    msg = ""
    try:
        inet_aton(ip)
    except Serror: 
        msg = "IP %s is not a valid IP address." % ip
        err +=1
    return err, msg

def validate_hosts(hosts):
    err = 0
    msg = ""
    for n in hosts:
        if "ip" in n:
            er1, msg1 = validate_ip(n["ip"])
            err += er1
            msg = msg + "\n" + msg1
        else:
            msg = msg + "\n" + "Node %s doesn't have IP address defined." % n["name"]
            err += 1
        if not "name" in n:
            msg = msg + "\n" +  "Missing Node Name in config file."
            err +=1
        if "os" in n:
            er1, msg1 = validate_os(n["os"])
            err += er1
            msg = msg + "\n" + msg1
        else:
            msg = msg + "\n" + "Node %s doesn't have an OS defined." % n["name"]
            err += 1

    return err, msg

def validate_network(network):
    err = 0
    msg = ""
    for item in ["netmask", "gateway", "nameserver", "ntpserver"]:
        if item in network: 
            if item != "ntpserver":
                er1, msg1 = validate_ip(network[item])
                err += er1
                msg = msg + "\n" + msg1
        else:
            msg = msg + "Network doesn't have %s defined." % item
            err +=1
    return err, msg

def validate_config(config, strict):
    err = 0
    msg = ""
    if "kubam_ip" in config:
        er1, msg1 = validate_ip(config["kubam_ip"])
        err += er1
        msg = msg + "\n" + msg1
    elif strict:
        msg = msg + "\n" + "kubam_ip not found in config file."
        err += 1

    if "hosts" in config: 
        er1, msg1 = validate_hosts(config["hosts"])     
        err += er1
        msg = msg + "\n" + msg1
    
    elif strict:
        msg = msg + "\n" + "No hosts found in config file."
        err += 1

    if "network" in config: 
        er1, msg1 = validate_network(config["network"])
        err += er1
        msg = msg + "\n" + msg1
    elif strict:
        msg = msg + "\n" + "network not found in config file." 
        err += 1

    if err > 0:
        msg = "Invalid config file. See documentation at http://kubam.io" + msg
        config = {}
    return err, msg, config


    
    

def write_config(config, out_file):
    import yaml
    err = 0
    msg = ""
    try: 
        with open(out_file, "w") as f:
            try: 
                msg = yaml.safe_dump(config, f, encoding='utf-8', default_flow_style=False)
            except yaml.YAMLError as err:
                msg = "Error writing %s config file: %s" % (out_file, err)
                err = 1
    except IOError as err:
        err = 1
        msg = err.strerror + " " + out_file

    return err, msg

    
# get the config file and parse it out so we know what we have. 
# returns err, msg, config
def open_config(file_name):
    import yaml
    config = {}
    err = 0
    msg = ""
    try: 
        with open(file_name, "r") as stream: 
            try: 
                config = yaml.load(stream)
            except yaml.YAMLError as exc:
                msg = "Error parsing %s config file: " % file_name
                #print(exc)
                return 1, msg, {}
        stream.close()
    except IOError as err:
        msg =  err.strerror + " " + file_name
        if err.errno == 2:
            return 2, msg, {}
        return 1, msg, {}
    return err, msg, config

def parse_config(file_name, strict):
    err, msg, config = open_config(file_name) 
    if err != 0:
        return err, msg
    return validate_config(config, strict)

# our database operations will all be open and update the file. 
# creds_hash should be: {"ip": "172.28.225.164", "user": "admin", "password": "nbv12345"}}
def update_ucs_creds(file_name, creds_hash):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "ucsm" in config:
        config["ucsm"] = {}
    # if the creds is empty, then get rid of credentials. 
    if not creds_hash:
        config["ucsm"].pop("credentials", None)
    else: 
        config["ucsm"]["credentials"] = creds_hash 
    err, msg = write_config(config, file_name)
    return err, msg

# net_hash should be: {"vlan": "default"}
def update_ucs_network(file_name, net_hash):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "ucsm" in config:
        config["ucsm"] = {}
    config["ucsm"]["ucs_network"] = net_hash 
    err, msg = write_config(config, file_name)
    return err, msg

def get_ucs_network(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", {} 
    elif not "ucsm" in config:
        return 0, "", {} 
    elif not "ucs_network" in config["ucsm"]:
        return 0, "", {}
    else:
        return 0, "", config["ucsm"]["ucs_network"]

def update_network(file_name, net_hash):
    err, msg = validate_network(net_hash)
    if err > 0:
        return err, msg
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "network" in config:
        config["network"] = {}
    config["network"] = net_hash 
    err, msg = write_config(config, file_name)
    return err, msg

def get_network(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", {} 
    elif not "network" in config:
        return 0, "", {} 
    else:
        return 0, "", config["network"]
    
    
def update_ucs_servers(file_name, server_hash):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "ucsm" in config:
        config["ucsm"] = {}
    config["ucsm"]["ucs_server_pool"] = server_hash 
    err, msg = write_config(config, file_name)
    return err, msg


def get_ucs_servers(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", []
    elif not "ucsm" in config:
        return 0, "", []
    elif not "ucs_server_pool" in config["ucsm"]:
        return 0, "", []
    else:
        return 0, "", config["ucsm"]["ucs_server_pool"]

# get hosts out of the database
def get_hosts(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", []
    elif not "hosts" in config:
        return 0, "", []
    else:
        return 0, "", config["hosts"] 

# update the hosts
def update_hosts(file_name, ho_hash):
    err, msg = validate_hosts(ho_hash)
    if err > 0:
        return err, msg
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "hosts" in config:
        config["hosts"] = []
    config["hosts"] = ho_hash 
    err, msg = write_config(config, file_name)
    return err, msg

# get the proxy value
def get_proxy(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", ""
    elif not "proxy" in config:
        return 0, "", ""
    else:
        return 0, "", config["proxy"]

# update the proxy, should be something like http://proxy.com:80  needs port, etc. 
# TODO verify that this is correct to do some error detection. 
def update_proxy(file_name, proxy):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    config["proxy"] = proxy
    err, msg = write_config(config, file_name)
    return err, msg

def get_kubam_ip(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", ""
    elif not "kubam_ip" in config:
        return 0, "", ""
    else:
        return 0, "", config["kubam_ip"] 


def update_kubam_ip(file_name, kubam_ip):
    err, msg = validate_ip(kubam_ip)
    if err > 0:
        return err, msg
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    config["kubam_ip"] = kubam_ip
    err, msg = write_config(config, file_name)
    return err, msg

def get_public_keys(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", []
    elif not "public_keys" in config:
        return 0, "", []
    else:
        return 0, "", config["public_keys"] 


def update_public_keys(file_name, public_keys):
    err, msg = validate_pks(public_keys)
    if err > 0:
        return err, msg
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "public_keys" in config:
        config["public_keys"] = []
    config["public_keys"] = public_keys
    err, msg = write_config(config, file_name)
    return err, msg

def show_config(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", []
    else:
        return 0, "", config
    

def get_iso_map(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", []
    elif not "iso_map" in config:
        return 0, "", []
    else:
        return 0, "", config["iso_map"] 

def update_iso_map(file_name, iso_images):
    err, msg = validate_iso_images(iso_images)
    if err > 0:
        return err, msg
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "iso_map" in config:
        config["iso_map"] = []
    config["iso_map"] = iso_images
    err, msg = write_config(config, file_name)
    return err, msg
