"""Converts JSON representations of XML from the format used by Harpo990 to the format used by Polytropos."""
import copy
from datetime import datetime

def convert(json_in: dict) -> dict:
    parent_dict, local_dict = _convert(json_in, "")
    return local_dict

def _convert(json_in: dict, parent: str) -> (dict, dict):
    parent_dict = {}
    local_dict = copy.deepcopy(json_in)

    if isinstance(json_in, dict):
        for key in json_in:
            if isinstance(json_in[key], str) or isinstance(json_in[key], int) or isinstance(json_in[key], datetime):
                if key.startswith("@"):
                    parent_dict[parent + key] = json_in[key]
                    del local_dict[key]
                elif key == "_":
                    parent_dict[parent] = json_in[key]
                    del local_dict[key]
            elif isinstance(json_in[key], dict):
                _parent_dict, _local_dict = _convert(json_in[key], key)
                if _local_dict:
                    local_dict[key] = _local_dict
                else:
                    del local_dict[key]
                local_dict.update(_parent_dict)
            elif isinstance(json_in[key], list):
                ret_list = []
                for el in json_in[key]:
                    _, _local_dict = _convert(el, "")
                    ret_list.append(_local_dict)
                local_dict[key] = ret_list
            else:
                raise TypeError

    return parent_dict, local_dict



