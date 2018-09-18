from helper import KubamError
from ucsmsdk.ucsexception import UcsException


class UCSTemplate(object):
    @staticmethod
    def list_templates(handle):
        # from ucsmsdk.mometa.ls.LsServer import LsServer

        # Get all the updating and initial templates
        filter_str = "(type, 'initial-template', type='eq') or (type, 'updating-template', type='eq')"
        try:
            query = handle.query_classid("lsServer", filter_str=filter_str)
            templates = list()

            for q in query:
                templates.append({"name": q.dn})
            return templates

        except UcsException as e:
            raise KubamError(e)
