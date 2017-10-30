from ucsmsdk.ucsexception import UcsException

# org should not have org-<name> prepended."
def query_org(handle, org):
    print "Checking if org %s exists" % org
    obj = handle.query_dn("org-root/org-" + org)
    if not obj:
        print "Org %s does not exist" % org
        return False
    else:
        print "Org %s exists." % org
        return True

# create org should not have org- prepended to it. 
def create_org(handle, org):
    print "Creating Organization: %s" % org
    from ucsmsdk.mometa.org.OrgOrg import OrgOrg
    mo = OrgOrg(parent_mo_or_dn="org-root", name=org, descr="KUBAM org")
    handle.add_mo(mo, modify_present=True)
    try: 
        handle.commit()
    except UcsException as err:
        if err.error_code == "103":
            print "\tOrganization already exists."
        else:
            return 1, err.error_descr
    return 0, ""

# org should be passed with the org-<name> prepended to it.  
def delete_org(handle, org):
    print "Deleting Org %s" % org
    mo = handle.query_dn(org)
    try:
        handle.remove_mo(mo)
        handle.commit()
    except AttributeError:
        print "\talready deleted"

