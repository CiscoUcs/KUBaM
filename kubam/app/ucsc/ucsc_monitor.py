class UCSCMonitor(object):

    @staticmethod
    def get_status(handle, servers):
        from ucscsdk.mometa.fsm.FsmStatus import FsmStatus
        all_r = dict()
        for s in servers:
            #s['dn'] = s['dn'].replace("blade", "server")
            fsm = handle.query_dn(s['dn'] + "/fsm/")
            if not fsm:
                all_r[s['dn']] = s['dn'] + "/fsm"
                continue
            response = dict()
            response["fsm_status"] = fsm.fsm_status
            response["sacl"] = fsm.sacl
            response["current_fsm"] = fsm.current_fsm
            response["progress"] = fsm.progress
            response["completion_time"] = fsm.completion_time
            all_r[s['dn']] = response
        return all_r

    @staticmethod
    def get_fsm(handle, server):
        from ucscsdk.mometa.fsm.FsmStatus import FsmStatus
        fsm = handle.query_dn("compute/sys-{0}/status-sys_chassis-{1}_blade-{2}".format(server['domain_id'], server['chassis_id'], server['slot']))
        if not fsm:
            return {"stages": "no information"}
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
