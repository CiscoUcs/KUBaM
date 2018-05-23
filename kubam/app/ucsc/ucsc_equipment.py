from ucscsdk.ucscexception import UcscException

class UCSCEquipment(object):
    
    @staticmethod
    def list_servers(handle):
        from ucscsdk.mometa.compute.ComputeBlade import ComputeBlade
        from ucscsdk.mometa.compute.ComputeRackUnit import ComputeRackUnit
        blades = handle.query_classid(class_id="ComputeBlade")
        servers = handle.query_classid(class_id="ComputeRackUnit")
        m = blades + servers
        all_servers = []
        for i, s in enumerate(m):
            if type(s) is ComputeBlade:
                all_servers.append({
                    'type': "blade",
                    'label': s.usr_lbl,
                    'chassis_id': s.chassis_id,
                    'slot': s.rn.replace("blade-", ""),
                    'model': s.model,
                    'association': s.association,
                    'service_profile': s.assigned_to_dn
                })
            if type(s) is ComputeRackUnit:
                all_servers.append({
                    'type': "rack",
                    'label': s.usr_lbl,
                    'rack_id': s.rn.replace("rack-unit-", ""),
                    'model': s.model, 'association': s.association,
                    'service_profile': s.assigned_to_dn
                })
        return all_servers
