#!/usr/bin/env python
# this script does the following: 
# 1.  Read in a configuration file. 
# 2.  Create a kickstart file based on a template
# 3.  Create an image from that kickstart file to be used to boot a UCS.
from socket import inet_aton, error as Serror
from jinja2 import Environment, FileSystemLoader
from subprocess import call
from os import path
import Kickstart, VMware

# constants.  
KUBAM_DIR="/kubam/"
KUBAM_SHARE_DIR="/usr/share/kubam/"
BASE_IMG=KUBAM_SHARE_DIR+"/stage1/ks.img"
TEMPLATE_DIR=KUBAM_SHARE_DIR+"/templates/"
supported_oses = ["centos7.3", "esxi6.0", "esxi6.5"]


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

def validate_nodes(nodes):
    err = 0
    msg = ""
    for n in nodes:
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
    for item in ["netmask", "gateway", "nameserver"]:
        if item in network:
            er1, msg1 = validate_ip(network[item])
            err += er1
            msg = msg + "\n" + msg1
        else:
            msg = msg + "Network doesn't have %s defined." % item
            err +=1
    return err, msg

def validate_config(config):
    err = 0
    msg = ""
    if "masterIP" in config:
        er1, msg1 = validate_ip(config["masterIP"])
        err += er1
        msg = msg + "\n" + msg1
    else:
        msg = msg + "\n" + "masterIP not found in config file."
        err += 1

    if "nodes" in config: 
        er1, msg1 = validate_nodes(config["nodes"])     
        err += er1
        msg = msg + "\n" + msg1
    
    else:
        msg = msg + "\n" + "No nodes found in config file."
        err += 1

    if "network" in config: 
        er1, msg1 = validate_network(config["network"])
        err += er1
        msg = msg + "\n" + msg1
    else:
        msg = msg + "\n" + "network not found in config file." 
        err += 1
    if err > 0:
        msg = "Invalid config file. See documentation at http://kubam.io" + msg
        config = {}
    return err, msg, config

# get the config file and parse it out so we know what we have. 
# returns err, msg, config
def parse_config(file_name):
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
        return 1, msg, {}
    return validate_config(config)


def find_template(node):
    # first search in kubam directory for file, if not there, get it from default kubam. 
    template = node["os"] + ".tmpl"    
    if "template" in node:
        if path.isfile(node['template']):
            return 0, "", template, KUBAM_DIR
    if path.isfile(KUBAM_DIR + template):
        return 0, "", template, KUBAM_DIR
    if path.isfile(TEMPLATE_DIR + template):
        return 0, "", template, TEMPLATE_DIR
    return 1, "template not found", "", ""
    
    

def build_template(node, config):
    err, msg, template_file, template_dir = find_template(node)
    if err > 0:
        return err, msg, ""
    j2_env = Environment(loader=FileSystemLoader(template_dir),
                     trim_blocks=True)
    f = j2_env.get_template(template_file).render(
        masterIP=config["masterIP"],
        ip=node["ip"],
        name=node["name"],
        netmask=config["network"]["netmask"],
        nameserver=config["network"]["nameserver"],
        gateway=config["network"]["gateway"],
        keys=config["public_keys"] 
    )
    return err, msg, f
    
def build_boot_image(node, template):
    if node["os"] in ["centos7.3"]:
        return Kickstart.build_boot_image(node, template)
    if node["os"] in ["esxi6.0", "esxi6.5"]:
        return VMware.build_boot_image(node, template)

def deploy_server_images():
    err = 0
    msg = "ok"
    err, msg, config = parse_config(KUBAM_DIR + "kubam.yaml")
    if err > 0:
        return err, msg

    for node in config["nodes"]:
        err, msg, template = build_template(node, config)
        if err > 0:
            break
        err, msg = build_boot_image(node, template)
        if err == 1:
            break

    return err, msg 
