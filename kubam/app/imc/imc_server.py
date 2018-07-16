from imcsdk.imcexception import ImcOperationError
from imcsdk.apis.server import vmedia
from db import YamlDB
from config import Const
from helper import KubamError

class IMCServer(object):

    @staticmethod
    def mount_media(handle, kubam_server, host_name, os):
        """
        Mount vMedia on IMC server. 
        """
        media = os + "-boot.iso"
        if os in ["esxi6.0", "esxi6.5"]:
            media = host_name + ".iso"
        try:
            vmedia.vmedia_mount_create(
                handle,
                volume_name="c",
                map="www",
                mount_options="",
                remote_share="http://{0}/kubam".format(kubam_server),
                remote_file=media,
                username="",
                password="")
        #https://github.com/CiscoUcs/imcsdk/blob/master/imcsdk/imcexception.py
        except ImcOperationError as e:
            raise KubamError(e.message)
        
        
