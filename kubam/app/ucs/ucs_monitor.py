class UCSMonitor(object):

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
