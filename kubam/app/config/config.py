# Class with constant variables
class Const(object):
    KUBAM_CFG = "/kubam/kubam.yaml"
    API_ROOT = "/api/v1"
    API_ROOT2 = "/api/v2"
    KUBAM_DIR = "/kubam/"
    KUBAM_SHARE_DIR = "/usr/share/kubam/"
    BASE_IMG = KUBAM_SHARE_DIR + "/stage1/ks.img"  # ext2 formatted base image. 
    WIN_IMG = KUBAM_SHARE_DIR + "/stage1/win.img"  # windows requires fat32 formatted
    TEMPLATE_DIR = KUBAM_SHARE_DIR + "/templates/"
    HTTP_OK = 200
    HTTP_CREATED = 201
    HTTP_NO_CONTENT = 204
    HTTP_BAD_REQUEST = 400
    HTTP_UNAUTHORIZED = 401
    HTTP_NOT_FOUND = 404
    HTTP_NOT_ALLOWED = 405
    HTTP_SERVER_ERROR = 500
    CATALOG = {  # Catalog of supported operating systems
        'centos7.3': ["generic", "k8s master", "k8s node"],
        'centos7.4': ["generic", "k8s master", "k8s node"],
        'centos7.5': ["generic", "k8s master", "k8s node"],
        'redhat7.2': ["generic", "k8s master", "k8s node"],
        'redhat7.3': ["generic", "k8s master", "k8s node"],
        'redhat7.4': ["generic", "k8s master", "k8s node"],
        'redhat7.5': ["generic", "k8s master", "k8s node"],
        'rhvh4.1': ["generic"],
        'esxi6.0': ["generic"],
        'esxi6.5': ["generic"],
        'esxi6.7': ["generic"],
        'ubuntu18.04': ["generic", "k8s master", "k8s node"],
        'win2012r2': ["generic"],
        'win2016': ["generic"]
    }
    OS_DICT = {  # Dictionary of supported operating systems
        "centos7.3": {
            "key_file": ".discinfo",
            "key_string": "7.3",
            "dir": "centos7.3"
        },
        "centos7.4": {
            "key_file": ".discinfo",
            "key_string": "7.4",
            "dir": "centos7.4"
        },
        "centos7.5": {
            "key_file": ".discinfo",
            "key_string": "7.5",
            "dir": "centos7.5"
        },
        "redhat7.2": {
            "key_file": ".discinfo",
            "key_string": "7.2",
            "dir": "redhat7.2"
        },
        "redhat7.3": {
            "key_file": ".discinfo",
            "key_string": "7.3",
            "dir": "redhat7.3"
        },
        "redhat7.4": {
            "key_file": ".discinfo",
            "key_string": "7.4",
            "dir": "redhat7.4"
        },
        "redhat7.5": {
            "key_file": ".discinfo",
            "key_string": "7.5",
            "dir": "redhat7.5"
        },
        "rhvh4.1": {
            "key_file": ".discinfo",
            "key_string": "RHVH 4.1",
            "dir": "rhvh4.1"
        },
        "esxi6.7": {
            "key_file": ".discinfo",
            "key_string": "Version: 6.7.0",
            "dir": "esxi6.7"
        },
        "esxi6.5": {
            "key_file": ".DISCINFO",
            "key_string": "Version: 6.5.0",
            "dir": "esxi6.5"
        },
        "esxi6.0": {
            "key_file": ".DISCINFO",
            "key_string": "Version: 6.0.0",
            "dir": "esxi6.0"
        },
        "ubuntu18.04" : {
            "key_file": ".disk/info",
            "key_string": "Bionic Beaver",
            "dir": "ubuntu18.04"
        },
        "win2012r2": {
            "key_file": "sources/idwbinfo.txt",
            "key_string": "winblue_rtm",
            "dir": "win2012r2"
        },
        "win2016": {
            "key_file": "sources/idwbinfo.txt",
            "key_string": "rs1_release",
            "dir": "win2016"
        }
    }
