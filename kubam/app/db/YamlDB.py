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
from cryptography.fernet import Fernet
import uuid

# constants.  

# makes sure that the list of ISO images actually exists. 
def validate_iso_images(iso_images):
    for i in iso_images:
        if i == None:
            return 1, "empty value not accepted."
        elif not "file" in i and not "os" in i:
            return 1, "iso must have an 'os' value and a 'file' value"
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
# TODO: Get this information from the catalog.  Maybe move builder external
def validate_os(op_sys):
    rc = 0
    msg = ""
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
        msg = err.strerror + " " + out_file
        err = 1

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


def new_uuid():
    # create a random uuid string.
    return str(uuid.uuid4())

def delete_server_group(file_name, guid):
    """
    Deletes a server group from the list of servers.  Just pass in the ID.
    """
    #TODO: Make sure no host depends upon a physical group.
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "server_groups" in config:
        return 1, "no servers created yet"
    # get the group
    found = False
    for group in config["server_groups"]:
        if group["id"] == guid:
            found = True 
            config["server_groups"].remove(group)
            break
    # now that it is removed, write the config file back out. 
    err, msg = write_config(config, file_name)
    return err, msg

def check_valid_server_group(gh):
    if not "type" in gh:
        return 1, "Please specify the type of server group: 'imc' or 'ucsm'"
    else: 
        if gh["type"] not in ["imc", "ucsm"]:
            return 1, "server group type should be 'imc' or 'ucsm'"
            
    if not "name" in gh:
        return 1, "Please specify the name of the server group.  This should be unique."
    if not "credentials" in gh: 
        return 1, "Please specify the login credentials of the server group: 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"
    
    creds = gh['credentials']
    if not isinstance(creds, dict):
        return 1, "Credentials should be a dictionary of ip, password, and user."
    if not 'ip' in creds:
        return 1, "Please specify the login credentials of the server group: 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"
    if not 'password' in creds:
        return 1, "Please specify the login credentials of the server group: 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"
    if not 'user' in creds: 
        return 1, "Please specify the login credentials of the server group: 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"
    return 0, ""

def update_server_group(file_name, gh):
    # check if valid config. 
    err, msg = check_valid_server_group(gh)
    if err == 1:
        return err, msg
    # make sure there is an id
    if not "id" in gh:
        return 1, "server group id not given"
    
    # get all server groups
    err, msg, groups = list_server_group(file_name)
    if err == 1:
        return err, msg
    # check that it exists. 
    found = False
    for g in groups:
        if g['id'] == gh['id']:
            found = True
            groups.remove(g)
            groups.append(gh)
            err, msg, config = open_config(file_name)
            config['server_groups'] = groups
            err, msg = write_config(config, file_name)
            if err == 1:
                return err, msg
    if not found:
        return 1, "nothing to update, no server group %s is found" % gh['name']

    return 0, "%s has been updated" % gh['name']
    
    
def new_server_group(file_name, gh):
    """
    Credentials passed would be:
    {"name", "ucs01", "type" : "ucsm", "credentials" : {"user": "admin", "password" : "secret-password", "server" : "172.28.225.163" }}
    """    
    if not isinstance(gh, dict):
        return 1, "No server group information was passed into the request."
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    err, msg = check_valid_server_group(gh)
    if err == 1:
        return err, msg
    # create a new uuid
    gh["id"] = new_uuid()
    # encrypt the password: 
    err, msg, key = get_decoder_key(file_name)
    if err == 1:
        return err, msg
    f = Fernet(key)
    gh['credentials']['password'] = f.encrypt(bytes(gh['credentials']['password']))
   
    # nothing in here yet, first entry.
    if not "server_groups" in config:
        config["server_groups"] = []
    else:
        # check if name already exists
        for group in config["server_groups"]:
            if group["name"] == gh["name"]:
                return 1, "server group '%s' already exists.  Can not add another." % gh["name"]

    config["server_groups"].append(gh)
    err, msg = write_config(config, file_name)
    return err, msg

def list_server_group(file_name):
    """
    get all the server group details for each server group.
    """
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    # err code 2 means no entries 
    if err == 2:
        return 0, "", {}
    if not "server_groups" in config:
        return 0, "", {}
    return 0, "", config["server_groups"]



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

# get the UCS org
def get_org(file_name):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    elif err == 2:
        return 0, "", ""
    if not "ucsm" in config:
        return 0, "", ""
    if not "org" in config["ucsm"]:
        return 0, "", ""
    else:
        return 0, "", config["ucsm"]["org"]

# Set UCS org
def update_org(file_name, org):
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "ucsm" in config:
        config["ucsm"] = {}
    # if org is empty update org. 
    if not org:
        config["ucsm"].pop("org", None)
    else: 
        config["ucsm"]["org"] = org
    err, msg = write_config(config, file_name)
    return err, msg

# put in the IP address of master node. 
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


def create_key(file_name):
    """
    create the key in a file name, write it out and return the key
    """
    key = Fernet.generate_key()
    try: 
        with open(file_name, "w") as f:
            f.write(key)
    except IOError as err:
        return 1, err.strerror + " " + file_name, ""
    f.close()
    return 0, "", key
    
def get_key(file_name):
    """
    return the decoder key
    """
    key = ""
    with open(file_name, "r") as f:
        key = f.read()
    return key 


def get_decoder_key(file_name):
    """
    Create encryption key file in the same directory as the kubam.yaml if it doesn't exist.
    but we store it in the .kubam file
    The file passed in should be the kubam.yaml file so we can tell where it is. 
    """
    dir_name = path.dirname(file_name)
    secret_file = path.join(dir_name, ".kubam")
    err = 0
    msg = ""
    if path.isfile(secret_file):
        key = get_key(secret_file)
    else:
        # create the key
        err, msg, key = create_key(secret_file)
    return err, msg, key


def list_aci(file_name):
    """
    get all the aci details for each aci group
    """
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    # err code 2 means no entries 
    if err == 2:
        return 0, "", {}
    if not "aci" in config:
        return 0, "", {}
    return 0, "", config["aci"]

def check_valid_aci(gh):
    if not "name" in gh:
        return 1, "Please specify the name of the server group.  This should be unique."
    if not "credentials" in gh: 
        return 1, "Please specify the login credentials of the server group: 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"
    
    creds = gh['credentials']
    if not isinstance(creds, dict):
        return 1, "Credentials should be a dictionary of ip, password, and user."
    if not 'ip' in creds:
        return 1, "Please specify the login credentials of ACI : 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"
    if not 'password' in creds:
        return 1, "Please specify the login credentials of ACI: 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"
    if not 'user' in creds: 
        return 1, "Please specify the login credentials of ACI: 'credentials': { 'ip': '123.345.234.1', 'password': 'password', 'user': 'admin' }"

    if not 'tenant_name' in gh:
        return 1, "Please specify the tenant name for the ACI group"
    if not 'vrf_name' in gh:
        return 1, "Please specify the VRF name for the ACI group"
    if not 'bridge_domain' in gh:
        return 1, "Please specify the bridge Domain name for the ACI group"
    return 0, ""

def new_aci(file_name, gh):
    """
    Create a new ACI group
    { "name": "ACI group name",
      "credentials": {
        "ip": <ip>
        "password": <secret-password>
        "user": <admin>
       },
    "tenant_name": <tenant name> 
    "tenant_descr": <tenant description>
    "vrf_name": <vrf name>
    "vrf_description": <vrf descr>
    "bridge_domain": <name of bridge domain>
    }
    """    
    if not isinstance(gh, dict):
        return 1, "No information was passed into the request."
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    err, msg = check_valid_aci(gh)
    if err == 1:
        return err, msg
    # create a new uuid
    gh["id"] = new_uuid()
    # encrypt the password: 
    err, msg, key = get_decoder_key(file_name)
    if err == 1:
        return err, msg
    f = Fernet(key)
    gh['credentials']['password'] = f.encrypt(bytes(gh['credentials']['password']))
   
    # nothing in here yet, first entry.
    if not "aci" in config:
        config["aci"] = []
    else:
        # check if name already exists
        for group in config["aci"]:
            if group["name"] == gh["name"]:
                return 1, "ACI group '%s' already exists.  Can not add another." % gh["name"]

    config["aci"].append(gh)
    err, msg = write_config(config, file_name)
    return err, msg

def update_aci(file_name, gh):
    """
    Update an ACI group
    """
    # check if valid config. 
    err, msg = check_valid_aci(gh)
    if err == 1:
        return err, msg
    # make sure there is an id
    if not "id" in gh:
        return 1, "ACI group id not given"
    
    # get all server groups
    err, msg, groups = list_aci(file_name)
    if err == 1:
        return err, msg
    # check that it exists. 
    found = False
    for g in groups:
        if g['id'] == gh['id']:
            found = True
            groups.remove(g)
            groups.append(gh)
            err, msg, config = open_config(file_name)
            config['aci'] = groups
            err, msg = write_config(config, file_name)
            if err == 1:
                return err, msg
    if not found:
        return 1, "nothing to update, no server group %s is found" % gh['name']

    return 0, "%s has been updated" % gh['name']

def delete_aci(file_name, guid):
    """
    Deletes an ACI group from the Database.  Just pass in the ID.
    """
    #TODO: make sure no network group depends upon an aci group. 
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "aci" in config:
        return 1, "no servers created yet"
    # get the group
    found = False
    for group in config["aci"]:
        if group["id"] == guid:
            found = True 
            config["aci"].remove(group)
            break
    # now that it is removed, write the config file back out. 
    err, msg = write_config(config, file_name)
    return err, msg


def check_valid_network(gh):
    """
    Checks that all the right parameters are in the network hash
    """
    if not "name" in gh:
        return 1, "Please specify the name of the network group.  This should be unique."
    err, msg = validate_network(gh)
    if err > 0:
        return err, msg

    if "aci_group" in gh:
        #TODO, make sure aci group exists. 
        1
    return 0, ""

# net information
def new_network_group(file_name, gh):
    """
    Create a new net group
    { 
    "name" : <unique name>,
    "gateway": <netmask>,
    "nameserver" : <ip>,
    "ntpserver" : <ip / host>,
    "vlan" : <optional value>,
    "proxy" : <optional ip with port or url>,
    "aci_group" : <value that exists in config already for ACI>
    }
    """    
    if not isinstance(gh, dict):
        return 1, "No information was passed into the request."
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    err, msg = check_valid_network(gh)
    if err > 0:
        return 1, msg
    # create a new uuid
    gh["id"] = new_uuid()
    # encrypt the password: 

    # nothing in here yet, first entry.
    if not "network_groups" in config:
        config["network_groups"] = []
    else:
        # check if name already exists
        for group in config["network_groups"]:
            if group["name"] == gh["name"]:
                return 1, "Network group '%s' already exists.  Can not add another." % gh["name"]

    config["network_groups"].append(gh)
    err, msg = write_config(config, file_name)
    return err, msg


def list_network_group(file_name):
    """
    get all the network group details for each group.
    """
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg, ""
    # err code 2 means no entries 
    if err == 2:
        return 0, "", {}
    if not "network_groups" in config:
        return 0, "", {}
    return 0, "", config["network_groups"]

def update_network_group(file_name, gh):
    """
    Update an existing network group to something else. 
    """
    # check if valid config. 
    
    err, msg = check_valid_network(gh)
    if err > 0:
        return 1, msg
    # make sure there is an id
    if not "id" in gh:
        return 1, "network group id not given"
    
    # get all server groups
    err, msg, groups = list_network_group(file_name)
    if err == 1:
        return err, msg
    # check that it exists. 
    found = False
    for g in groups:
        if g['id'] == gh['id']:
            found = True
            groups.remove(g)
            groups.append(gh)
            err, msg, config = open_config(file_name)
            config['network_groups'] = groups
            err, msg = write_config(config, file_name)
            if err == 1:
                return err, msg
    if not found:
        return 1, "nothing to update, no network group %s is found" % gh['name']

    return 0, "%s has been updated" % gh['name']
    

def delete_network_group(file_name, guid):
    """
    Deletes a Network group from the Database.  Just pass in the ID.
    """
    #TODO: make sure no host group uses a network group
    err, msg, config = open_config(file_name)
    if err == 1:
        return err, msg
    if not "aci" in config:
        return 1, "no servers created yet"
    # get the group
    found = False
    for group in config["network_groups"]:
        if group["id"] == guid:
            found = True 
            config["network_groups"].remove(group)
            break
    # now that it is removed, write the config file back out. 
    err, msg = write_config(config, file_name)
    return err, msg

