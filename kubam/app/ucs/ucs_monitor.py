class UCSMonitor(object):

    # Get the server name from the URL parameters
    @staticmethod
    def get_server_name(args):
        server_type = args.get('type')
        chassis_id = args.get('chassis_id')
        slot = args.get('slot')
        rack_id = args.get('rack_id')
        server_name = None
        if server_type == "blade":
            server_name = "sys/chassis-{0}/blade-{1}".format(chassis_id, slot)
        elif server_type == "rack":
            server_name = "sys/rack-unit-{0}".format(rack_id)

        return server_name

    @staticmethod
    def get_status(handle, server_name):
        fsm = handle.query_dn(server_name + "/fsm")
        if not fsm:
            return None
        response = dict()
        response["fsm_status"] = fsm.fsm_status
        response["sacl"] = fsm.sacl
        response["current_fsm"] = fsm.current_fsm
        response["progress"] = fsm.progress
        response["completion_time"] = fsm.completion_time
        return response

    @staticmethod
    def get_fsm(handle, server_name):
        fsm = handle.query_dn(server_name + "/fsm")
        if not fsm:
            return None
        stages = handle.query_children(in_mo=fsm)
        # Sorting the list of stages by the order
        stages.sort(key=lambda x: int(x.order))
        tmp = list()
        for s in stages:
            tmp.append({"descr": s.descr, "name": s.name, "order": s.order, "stage_status": s.stage_status,
                        "retry": s.retry, "last_update_time": s.last_update_time})
        response = dict()
        response["stages"] = tmp
        return response
