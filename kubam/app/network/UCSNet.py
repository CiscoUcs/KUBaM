from ucsmsdk.ucsexception import UcsException

def listVLANs(handle):
    filter_string = '(dn, "fabric/lan/net-[A-Za-z0-9]+", type="re")'
    vlans = handle.query_classid("fabricVlan", filter_string)
    return vlans
        
def createKubeMacs(handle, org):
    from ucsmsdk.mometa.macpool.MacpoolPool import MacpoolPool
    from ucsmsdk.mometa.macpool.MacpoolBlock import MacpoolBlock
    mo = MacpoolPool(parent_mo_or_dn=org, policy_owner="local", descr="KUBAM MAC Pool A", assignment_order="default", name="kubamA")
    mo_1 = MacpoolBlock(parent_mo_or_dn=mo, to="00:25:B5:88:8A:FF", r_from="00:25:B5:88:8A:00")
    handle.add_mo(mo)

    mo = MacpoolPool(parent_mo_or_dn=org, policy_owner="local", descr="KUBAM MAC Pool B", assignment_order="default", name="kubamB")
    mo_1 = MacpoolBlock(parent_mo_or_dn=mo, to="00:25:B5:88:8B:FF", r_from="00:25:B5:88:8B:00")
    handle.add_mo(mo)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\tKUBAM MAC Pools already exist"
        else:
            return 1, err.error_descr
    return 0, ""

def deleteKubeMacs(handle, org):
    print "Deleting KUBAM MAC Pools"
    moa = handle.query_dn(org + "/mac-pool-kubamA")
    mob = handle.query_dn(org + "/mac-pool-kubamB")
    try:
        handle.remove_mo(moa)
        handle.remove_mo(mob)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

#handle.commit()    
def createVNICTemplates(handle, vlan, org):
    print "Creating KUBAM VNIC Templates"
    from ucsmsdk.mometa.vnic.VnicLanConnTempl import VnicLanConnTempl
    from ucsmsdk.mometa.vnic.VnicEtherIf import VnicEtherIf
    mo = VnicLanConnTempl(parent_mo_or_dn=org, templ_type="updating-template", name="kubamA", descr="", stats_policy_name="default", switch_id="A", pin_to_group_name="", mtu="1500", policy_owner="local", qos_policy_name="", ident_pool_name="kubamA", nw_ctrl_policy_name="")
    mo_1 = VnicEtherIf(parent_mo_or_dn=mo, default_net="yes", name=vlan)
    handle.add_mo(mo)

    mob = VnicLanConnTempl(parent_mo_or_dn=org, templ_type="updating-template", name="kubamB", descr="", stats_policy_name="default", switch_id="B", pin_to_group_name="", mtu="1500", policy_owner="local", qos_policy_name="", ident_pool_name="kubamB", nw_ctrl_policy_name="")
    mo_2 = VnicEtherIf(parent_mo_or_dn=mob, default_net="yes", name=vlan)
    handle.add_mo(mob)

    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\tVNIC Templates already exist"
        else:
            return 1, err.error_descr
    return 0, ""

def deleteVNICTemplates(handle, org):
    print "Deleting VNIC Templates"
    moa = handle.query_dn(org + "/lan-conn-templ-kubamA")
    mob = handle.query_dn(org + "/lan-conn-templ-kubamB")
    try:
        handle.remove_mo(moa)
        handle.remove_mo(mob)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def createLanConnPolicy(handle, org):
    print "Creating KUBAM LAN connectivity policy"
    from ucsmsdk.mometa.vnic.VnicLanConnPolicy import VnicLanConnPolicy
    from ucsmsdk.mometa.vnic.VnicEther import VnicEther
    mo = VnicLanConnPolicy(parent_mo_or_dn=org, policy_owner="local", name="kubam", descr="KUBAM LAN Connectivity Policy")
    mo_1 = VnicEther(parent_mo_or_dn=mo, addr="derived", nw_ctrl_policy_name="", admin_vcon="any", stats_policy_name="default", switch_id="A", pin_to_group_name="", mtu="1500", qos_policy_name="", adaptor_profile_name="Linux", ident_pool_name="", order="1", nw_templ_name="kubamA", name="eth0")
    mo_2 = VnicEther(parent_mo_or_dn=mo, addr="derived", nw_ctrl_policy_name="", admin_vcon="any", stats_policy_name="default", switch_id="A", pin_to_group_name="", mtu="1500", qos_policy_name="", adaptor_profile_name="Linux", ident_pool_name="", order="2", nw_templ_name="kubamB", name="eth1")
    try: 
        handle.add_mo(mo)
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\tLAN connectivity policy 'kubam' already exists"
        else:
            return 1, err.error_descr
    return 0, ""

def deleteLanConnPolicy(handle, org):
    print "Deleting KUBAM LAN Connectivity policy"
    mo = handle.query_dn(org + "/lan-conn-pol-kubam")
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"
    except UcsException as err:
        return 1, err.error_descr
    return 0, ""

def createKubeNetworking(handle, org, vlan_name):
    err = 0
    msg = ""
    err, msg = createKubeMacs(handle, org)
    if err != 0:
        return err, msg

    err, msg = createVNICTemplates(handle, vlan_name, org)
    if err != 0:
        return err, msg
    
    err, msg = createLanConnPolicy(handle, org)
    return err, msg

def deleteKubeNetworking(handle, org):
    err, msg = deleteLanConnPolicy(handle, org)
    if err != 0:
        return err, msg
    err, msg = deleteVNICTemplates(handle, org)
    if err != 0:
        return err, msg
    err, msg = deleteKubeMacs(handle, org) 
    if err != 0:
        return err, msg
    return err, msg
