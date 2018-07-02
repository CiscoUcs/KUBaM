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
    def get_fsm(handle, server_name):
        pass

