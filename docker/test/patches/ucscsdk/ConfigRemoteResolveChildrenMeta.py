"""This module contains the meta information of ConfigResolveChildren ExternalMethod."""

from ..ucsccoremeta import MethodMeta, MethodPropertyMeta

method_meta = MethodMeta("ConfigRemoteResolveChildren", "configRemoteResolveChildren", "Version142b")

prop_meta = {
    "class_id": MethodPropertyMeta("ClassId", "classId", "NamingClassId", "Version142b", "InputOutput", False),
    "cookie": MethodPropertyMeta("Cookie", "cookie", "Xs:string", "Version142b", "InputOutput", False),
    "in_dn": MethodPropertyMeta("InDn", "inDn", "ReferenceObject", "Version142b", "Input", False),
    "in_domain_id": MethodPropertyMeta("InDomainId", "inDomainId", "ReferenceObject", "Version142b", "Input", False),
    "in_filter": MethodPropertyMeta("InFilter", "inFilter", "FilterFilter", "Version142b", "Input", True),
    "in_hierarchical": MethodPropertyMeta("InHierarchical", "inHierarchical", "Xs:string", "Version142b", "Input", False),
    "in_include_props": MethodPropertyMeta("InIncludeProps", "inIncludeProps", "Xs:string", "Version142b", "Input", False),
    "in_return_count_only": MethodPropertyMeta("InReturnCountOnly", "inReturnCountOnly", "Xs:string", "Version142b", "Input", False),
    "out_configs": MethodPropertyMeta("OutConfigs", "outConfigs", "ConfigSet", "Version142b", "Output", True),
    "out_count": MethodPropertyMeta("OutCount", "outCount", "Xs:unsignedInt", "Version142b", "Output", False),
}

prop_map = {
    "classId": "class_id",
    "cookie": "cookie",
    "inDn": "in_dn",
    "inDomainId": "in_domain_id",
    "inFilter": "in_filter",
    "inHierarchical": "in_hierarchical",
    "inIncludeProps": "in_include_props",
    "inReturnCountOnly": "in_return_count_only",
    "outConfigs": "out_configs",
    "outCount": "out_count",
}

