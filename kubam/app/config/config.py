# Class with constant variables
class Const(object):
    KUBAM_CFG = "/kubam/kubam.yaml"
    API_ROOT = "/api/v1"
    API_ROOT2 = "/api/v2"
    KUBAM_DIR = "/kubam/"
    KUBAM_SHARE_DIR = "/usr/share/kubam/"
    BASE_IMG = KUBAM_SHARE_DIR + "/stage1/ks.img"
    TEMPLATE_DIR = KUBAM_SHARE_DIR + "/templates/"
    CATALOG = {
        'centos7.3': ["generic", "k8s master", "k8s node"],
        'centos7.4': ["generic", "k8s master", "k8s node"],
        'redhat7.2': ["generic", "k8s master", "k8s node"],
        'redhat7.3': ["generic", "k8s master", "k8s node"],
        'redhat7.4': ["generic", "k8s master", "k8s node"],
        'esxi6.0': ["generic"],
        'esxi6.5': ["generic"],
    }
