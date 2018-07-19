#!/usr/bin/env python
# this script does the following: 
# 1.  Read in a configuration file. 
# 2.  Create a kickstart file based on a template
# 3.  Create an image from that kickstart file to be used to boot a UCS.
from socket import inet_aton, error as Serror
from jinja2 import Environment, FileSystemLoader
from subprocess import call
from os import path, chdir
import Kickstart, VMware
from db import YamlDB 

# constants.  
KUBAM_DIR="/kubam/"
KUBAM_SHARE_DIR="/usr/share/kubam/"
BASE_IMG=KUBAM_SHARE_DIR+"/stage1/ks.img"
TEMPLATE_DIR=KUBAM_SHARE_DIR+"/templates/"

# catalog has to be in sync with IsoMaker module. 
catalog = {
    "centos7.3" : ["generic", "k8s master", "k8s node"],
    "centos7.4" : ["generic", "k8s master", "k8s node"],
    "centos7.5" : ["generic", "k8s master", "k8s node"],
    "redhat7.2" : ["generic", "k8s master", "k8s node"],
    "redhat7.3" : ["generic", "k8s master", "k8s node"],
    "redhat7.4" : ["generic", "k8s master", "k8s node"],
    "redhat7.5" : ["generic", "k8s master", "k8s node"],
    "esxi6.0" : ["generic"],
    "esxi6.5" : ["generic"],
}


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
    if not "vlan" in config["network"]:
        config["network"]["vlan"] = ""
    j2_env = Environment(loader=FileSystemLoader(template_dir),
                     trim_blocks=True)
    if not "proxy" in config:
        config["proxy"] = ""

    f = j2_env.get_template(template_file).render(
        masterIP=config["kubam_ip"],
        ip=node["ip"],
        # grab the first k8s master or return blank if there is none.
        k8s_master=next( (x for x in config["hosts"] if x["role"] == "k8s master"), ""),
        name=node["name"],
        proxy=config["proxy"],
        role=node["role"],
        hosts=config["hosts"],
        netmask=config["network"]["netmask"],
        nameserver=config["network"]["nameserver"],
        ntp=config["network"]["ntpserver"],
        gateway=config["network"]["gateway"],
        vlan=config["network"]["vlan"],
        keys=config["public_keys"] 
    )
    return err, msg, f
    
def build_boot_image(node, template):
    if node["os"] in ["centos7.3", "centos7.4", "centos7.5", "redhat7.2", "redhat7.3", "redhat7.4", "redhat7.5"]:
        return Kickstart.build_boot_image(node, template)
    if node["os"] in ["esxi6.0", "esxi6.5"]:
        return VMware.build_boot_image(node, template)
    return 1,  "no os is built! for os %s and node %s" % (node["os"], node["name"])

# make_post - make the ansible post install directory so its accessible for
# post installation tasks.    
def make_post():
    if path.isdir(KUBAM_DIR + "post/ansible"):
        return 0, "ansible scripts already exist. Do not modify."
    o = call(["mkdir" , "-p", KUBAM_DIR + "post"])
    if not o == 0:
        return 1, "error making %s directory" % KUBAM_DIR + "post"
    o = call(["cp", "-a", KUBAM_SHARE_DIR + "/ansible", KUBAM_DIR + "post/"])
    if not o == 0:
        return 1, "error copying ansible components to %s directory" % KUBAM_DIR + "post"

    chdir(KUBAM_DIR + "post")
    o = call(["tar", "czf", KUBAM_DIR + "post/ansible.tgz", "ansible"])
    if not o == 0:
        return 1, "error creating tar archive of ansible scripts."
    return 0, ""

def deploy_server_images(config):
    err = 0
    msg = "ok"
    err, msg, config = YamlDB.parse_config(config, True)
    if err > 0:
        return err, msg

    err, msg = make_post()
    if err > 0:
        return err, msg

    for host in config["hosts"]:
        err, msg, template = build_template(host, config)
        if err > 0:
            print err, msg
            break
        err, msg = build_boot_image(host, template)
        if err == 1:
            print err, msg
            break

    return err, msg 
