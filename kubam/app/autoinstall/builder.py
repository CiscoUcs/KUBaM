from jinja2 import Environment, FileSystemLoader
from subprocess import call
from os import path, chdir, pardir
from kickstart import Kickstart
from vmware import VMware
from windows import Windows
from db import YamlDB
from config import Const


class Builder(object):
    """
    This class does the following:
    1.  Read in a configuration file.
    2.  Create a kickstart file based on a template
    3.  Create an image from that kickstart file to be used to boot a UCS.
    """
    @staticmethod
    def find_template(node):
        # First search in Kubam directory for file, if not there, get it from default Kubam
        template = node['os'] + ".tmpl"
        if "template" in node:
            if path.isfile(node['template']):
                print path.dirname(path.abspath(node['template']))
                return 0, None, path.basename(node['template']), path.dirname(path.abspath(node['template']))
            else:
                return 1, "template: {0} not found".format(node['template']), None, None
        if path.isfile(Const.KUBAM_DIR + template):
            return 0, None, template, Const.KUBAM_DIR
        if path.isfile(Const.TEMPLATE_DIR + template):
            return 0, None, template, Const.TEMPLATE_DIR
        return 1, "template not found", None, None

    @staticmethod
    def get_cidr(netmask):
        return sum([bin(int(x)).count('1') for x in netmask.split('.')])

    @staticmethod
    def build_template(node, config):
        """
        Given a node and the kubam configuration populate a template file with the appropriate values.
        If the machine is Windows we add the network.txt file and fill in these values as well. 
        Returns: error code (0 good, 1 bad), msg (only if an error), template, network.txt if windows.
        """
        err, msg, template_file, template_dir = Builder.find_template(node)
        if err > 0:
            return err, msg, None, None
        ## get network configuration from network group
        if not "network_group" in node:
            return 1, "node does not have a network_group", None, None
        netinfo = [x for x in config["network_groups"] if node["network_group"] == x["name"]]
        if len(netinfo) < 1:
            return 1, "network group {0} not found".format(node["network_group"]), None, None
        netinfo = netinfo[0] # get the first element of the list. 
        vlan = ""
        proxyAddr = ""
        if "vlan" in netinfo:
            vlan = netinfo["vlan"]
        if "proxy" in netinfo:
            proxyAddr = netinfo["proxy"]
        
        j2_env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True)
        f = j2_env.get_template(template_file).render(
            masterIP=config['kubam_ip'],
            ip=node['ip'],
            # grab the first k8s master or return blank if there is none.
            k8s_master=next((x for x in config['hosts'] if x['role'] == "k8s master"), ""),
            name=node['name'],
            proxy=proxyAddr,
            role=node['role'],
            hosts=config['hosts'],
            netmask=netinfo['netmask'],
            mask_bits=Builder.get_cidr(netinfo['netmask']),
            nameserver=netinfo['nameserver'],
            ntp=netinfo['ntpserver'],
            gateway=netinfo['gateway'],
            vlan=vlan,
            keys=config['public_keys']
        )
        j = ""
        if node["os"] in ["win2016", "win2012r2"]:
            net_dir = Const.TEMPLATE_DIR
            ## hack for test cases since we don't have a /kubam directory per say. Keep the templates in the test file.
            if template_file == "t134.tmpl":
               net_dir = "./test" 
            j2_env = Environment(loader=FileSystemLoader(net_dir), trim_blocks=True)
            j = j2_env.get_template("network.txt").render(
                masterIP=config['kubam_ip'],
                ip=node['ip'],
                netmask=netinfo['netmask'],
                gateway=netinfo['gateway'],
                os=node['os'] 
            )
        return err, msg, f, j

    @staticmethod
    def build_boot_image(node, template, net_template):
        if node['os'] in ["centos7.3", "centos7.4", "redhat7.2", "rhvh4.1", "redhat7.5", "centos7.5"]:
            return Kickstart.build_boot_image(node, template)
        if node['os'] in ["esxi6.0", "esxi6.5"]:
            return VMware.build_boot_image(node, template)
        if node['os'] in ["win2012r2", "win2016"]:
            return Windows.build_boot_image(node, template, net_template)
        return 1,  "no os is built! for os %s and node {0}".format(node['os'], node['name'])

    # Make the Ansible post install directory so its accessible for post installation tasks.
    @staticmethod
    def make_post():
        if path.isdir(Const.KUBAM_DIR + "post/ansible"):
            return 0, "ansible scripts already exist. Do not modify."
        o = call(["mkdir" , "-p", Const.KUBAM_DIR + "post"])
        if not o == 0:
            return 1, "error making {0} directory".format(Const.KUBAM_DIR + "post")
        o = call(["cp", "-a", Const.KUBAM_SHARE_DIR + "/ansible", Const.KUBAM_DIR + "post/"])
        if not o == 0:
            return 1, "error copying ansible components to {0} directory".format(Const.KUBAM_DIR + "post")

        chdir(Const.KUBAM_DIR + "post")
        o = call(["tar", "czf", Const.KUBAM_DIR + "post/ansible.tgz", "ansible"])
        if not o == 0:
            return 1, "error creating tar archive of ansible scripts."
        return 0, ""

    @staticmethod
    def make_images(hosts):
        """
        given an array of host dictionaries, build an image for each one.
        """
        # make the post directory
        err, msg = Builder.make_post()
        if err > 0:
            return err, msg

        db = YamlDB()
        err, msg, config = db.parse_config(Const.KUBAM_CFG, True) 
        if err > 0:
            return err, msg

        for host in hosts:
            err, msg, template, net_template  = Builder.build_template(host, config)
            if err > 0:
                print err, msg
                break
            err, msg = Builder.build_boot_image(host, template, net_template)
            if err == 1:
                print err, msg
                break

        return err, msg
