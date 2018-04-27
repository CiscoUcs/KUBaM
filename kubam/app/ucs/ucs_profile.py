from ucs_net import UCSNet
from ucs_server import UCSServer
from ucs_util import UCSUtil
from db import YamlDB
from config import Const


class UCSProfile(object):
    # Make the UCS configuration using the Kubam information
    @staticmethod
    def make_ucs():
        err, msg, handle = UCSUtil.ucs_login()
        if err != 0:
            return err, UCSUtil.not_logged_in(msg)
        err, msg, full_org = UCSUtil.get_full_org(handle)
        if err != 0:
            return err, msg

        db = YamlDB()
        err, msg, net_settings = db.get_ucs_network(Const.KUBAM_CFG)
        selected_vlan = ""
        if "vlan" in net_settings:
            selected_vlan = net_settings["vlan"]
        if selected_vlan == "":
            UCSUtil.ucs_logout(handle)
            return 1, "No VLAN selected in UCS configuration."

        ucs_net = UCSNet()
        err, msg = ucs_net.create_kube_networking(handle, full_org, selected_vlan)
        if err != 0:
            UCSUtil.ucs_logout(handle)
            return err, msg

        # Get the selected servers and hosts
        err, msg, hosts = db.get_hosts(Const.KUBAM_CFG)
        err, msg, servers = db.get_ucs_servers(Const.KUBAM_CFG)
        err, msg, kubam_ip = db.get_kubam_ip(Const.KUBAM_CFG)

        ucs_server = UCSServer()
        err, msg = ucs_server.create_server_resources(handle, full_org, hosts, servers, kubam_ip)
        if err != 0:
            UCSUtil.ucs_logout(handle)
            return err, msg

        UCSUtil.ucs_logout(handle)
        return err, msg

    # Destroy the UCS configuration
    @staticmethod
    def destroy_ucs():
        ucs_util = UCSUtil()
        err, msg, handle = ucs_util.ucs_login()
        if err != 0:
            return err, ucs_util.not_logged_in(msg)
        db = YamlDB()
        err, msg, hosts = db.get_hosts(Const.KUBAM_CFG)
        if err != 0:
            return 1, msg
        if len(hosts) == 0:
            return 0, "no servers deployed"
        err, msg, full_org = ucs_util.get_full_org(handle)
        if err != 0:
            return err, msg

        ucs_server = UCSServer()
        err, msg = ucs_server.delete_server_resources(handle, full_org, hosts)
        if err != 0:
            return 1, msg
        ucs_net = UCSNet()
        err, msg = ucs_net.delete_kube_networking(handle, full_org)
        if err != 0:
            return 1, msg
        return 0, "ok"
