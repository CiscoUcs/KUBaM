# Class with constant variables
class Const(object):
    KUBAM_CFG = "/kubam/kubam.yaml"
    API_ROOT = "/api/v1"
    API_ROOT2 = "/api/v2"
    KUBAM_DIR = "/kubam/"
    KUBAM_SHARE_DIR = "/usr/share/kubam/"
    BASE_IMG = KUBAM_SHARE_DIR + "/stage1/ks.img"
    TEMPLATE_DIR = KUBAM_SHARE_DIR + "/templates/"
    CATALOG = {  # Catalog of supported operating systems
        'centos7.3': ["generic", "k8s master", "k8s node"],
        'centos7.4': ["generic", "k8s master", "k8s node"],
        'redhat7.2': ["generic", "k8s master", "k8s node"],
        'redhat7.3': ["generic", "k8s master", "k8s node"],
        'redhat7.4': ["generic", "k8s master", "k8s node"],
        'esxi6.0': ["generic"],
        'esxi6.5': ["generic"],
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
        "esxi6.5": {
            "key_file": ".DISCINFO",
            "key_string": "Version: 6.5.0",
            "dir": "esxi6.5"
        },
        "esxi6.0": {
            "key_file": ".DISCINFO",
            "key_string": "Version: 6.0.0",
            "dir": "esxi6.0"
        }
    }