# -*- coding: utf-8 -*-
import os
import sys
import random
import tempfile
import string
import binascii
import argparse

from PIL import Image

from pathlib import Path

from P4 import P4, P4Exception


p4 = P4()
p4.user = 'rmaffesoli'
p4.port = 'ssl:helix:1666'
p4.connect()


def gather_file_attrs(depot_path: str, action: str):
    file_attr_dict = {
        'depot_path': depot_path,
        'action': action
    }

    return file_attr_dict

def gather_changelist_attrs(description):
    attr_dict = {
        "changelist": description.get('change'),
        "user": description.get('user'),
        "client": description.get('client'),
        "desc": description.get('desc'),
        "status": description.get('status'),
        "time": description.get('time'),
        "file_list": []
    }

    return attr_dict


def get_random_word(length=12):
    return "".join(random.sample(string.ascii_letters, length))


def main(changelist):
    description = p4.run_describe(changelist)
    if not description:
        return
    description  = description[0]
    attribute_dict = gather_changelist_attrs(description)
    
    for i, depot_file in enumerate(description["depotFile"]):
        action = description['action'][i]
        if 'delete' not in action:
            file_result = gather_file_attrs(f"{depot_file}@{changelist}", action)
            attribute_dict['file_list'].append(file_result)

    print(attribute_dict)
if __name__ == "__main__" :
    main(158)