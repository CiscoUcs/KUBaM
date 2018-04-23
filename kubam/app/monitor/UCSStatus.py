def get_status(handle, blade_name):
    fsm = handle.query_dn(blade_name + "/fsm")
    stages = handle.query_children(in_mo=fsm)
    # Sorting the list of stages by the order
    stages.sort(key=lambda x: int(x.order))
    tmp = list()
    for s in stages:
        tmp.append({"descr": s.descr, "name": s.name, "order": s.order, "stage_status": s.stage_status,
                    "retry": s.retry, "last_update_time": s.last_update_time})
    status = dict()
    status["sacl"] = fsm.sacl
    status["current_fsm"] = fsm.current_fsm
    status["progress"] = fsm.progress
    status["completion_time"] = fsm.completion_time
    status["stages"] = tmp
    return status




