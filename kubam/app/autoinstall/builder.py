from jinja2 import Environment, FileSystemLoader
from subprocess import call
from os import path, chdir
from kickstart import Kickstart
from vmware import VMware
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
                return 0, "", template, Const.KUBAM_DIR
        if path.isfile(Const.KUBAM_DIR + template):
            return 0, "", template, Const.KUBAM_DIR
        if path.isfile(Const.TEMPLATE_DIR + template):
            return 0, "", template, Const.TEMPLATE_DIR
        return 1, "template not found", "", ""

    def build_template(self, node, config):
        err, msg, template_file, template_dir = self.find_template(node)
        if err > 0:
            return err, msg, ""
        if "vlan" not in config['network']:
            config['network']['vlan'] = ""
        j2_env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True)
        if "proxy" not in config:
            config['proxy'] = ""

        f = j2_env.get_template(template_file).render(
            masterIP=config['kubam_ip'],
            ip=node['ip'],
            # grab the first k8s master or return blank if there is none.
            k8s_master=next((x for x in config['hosts'] if x['role'] == "k8s master"), ""),
            name=node['name'],
            proxy=config['proxy'],
            role=node['role'],
            hosts=config['hosts'],
            netmask=config['network']['netmask'],
            nameserver=config['network']['nameserver'],
            ntp=config['network']['ntpserver'],
            gateway=config['network']['gateway'],
            vlan=config['network']['vlan'],
            keys=config['public_keys']
        )
        return err, msg, f

    @staticmethod
    def build_boot_image(node, template):
        if node['os'] in ["centos7.3", "centos7.4", "redhat7.2"]:
            return Kickstart.build_boot_image(node, template)
        if node['os'] in ["esxi6.0", "esxi6.5"]:
            return VMware.build_boot_image(node, template)
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

    def deploy_server_images(self, config):
        err, msg, config = YamlDB.parse_config(config, True)
        if err > 0:
            return err, msg

        err, msg = self.make_post()
        if err > 0:
            return err, msg

        for host in config["hosts"]:
            err, msg, template = self.build_template(host, config)
            if err > 0:
                print err, msg
                break
            err, msg = self.build_boot_image(host, template)
            if err == 1:
                print err, msg
                break

        return err, msg
