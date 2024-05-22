# -*- coding: utf-8 -*-

import time
import base64
import json
import logging

from P4 import P4, P4Exception


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

p4 = P4()
p4.connect()


def gather_file_attrs(depot_path: str, action: str):
    file_attributes = p4.run("fstat", "-Oae", depot_path)
    logger.debug(str(file_attributes))
    hex_preview_attr = file_attributes[0].get("attr-preview")
    hex_thumb_attr = file_attributes[0].get("attr-thumb")

    if not hex_preview_attr:
        return

    preview_image = bytes.fromhex(hex_preview_attr)
    preview_image_type = get_image_type(preview_image)
    preview_base64 = base64.b64encode(preview_image)

    thumb_image = bytes.fromhex(hex_thumb_attr)
    thumb_image_type = get_image_type(thumb_image)
    thumb_base64 = base64.b64encode(thumb_image)

    file_attr_dict = {
        "depot_path": depot_path,
        "action": action,
        "preview": preview_base64,
        "preview_type": preview_image_type,
        "thumb": thumb_base64,
        "thumb_type": thumb_image_type,
    }

    return file_attr_dict


def get_image_type(image_data):
    if image_data.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):
        return "image/png"
    elif image_data.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg"
    else:
        return "unknown"


def gather_changelist_attrs(description):
    attr_dict = {
        "changelist": description.get("change"),
        "user": description.get("user"),
        "client": description.get("client"),
        "desc": description.get("desc"),
        "status": description.get("status"),
        "time": description.get("time"),
        "file_list": [],
    }

    return attr_dict


def gather_file_process_list(changelist):
    description = p4.run_describe(changelist)
    if not description:
        return
    description = description[0]
    attribute_dict = gather_changelist_attrs(description)

    attempts = {}
    completed = []
    failed = []

    for i, depot_file in enumerate(description["depotFile"]):
        action = description["action"][i]
        file_result = None
        if depot_file not in attempts:
            attempts[depot_file] = 1

        if "delete" not in action:
            while depot_file not in completed and attempts[depot_file] < 5:
                file_result = gather_file_attrs(f"{depot_file}@{changelist}", action)
                if not file_result:
                    attempts[depot_file] += 1
                    time.sleep(3)
                else:
                    logger.debug("did it")
                    completed.append(depot_file)
                    attribute_dict["file_list"].append(file_result)
            if not file_result:
                failed.append(depot_file)

    logger.info(f"Attempts {attempts}")
    logger.info(f"completed {completed}")
    logger.info(f"failed {failed}")
    return attribute_dict


def set_default(obj):
    """
    Converts any set to a list type object.
    """
    if isinstance(obj, set):
        return list(obj)
    elif isinstance(obj, bytes):
        return obj.decode("utf-8")

    return obj


def write_json(data_dict, output_path, sort_keys=False):
    """
    Writes a dictionary into a json file.
    """
    with open(output_path, "w") as outfile:
        json.dump(
            data_dict, outfile, default=set_default, indent=4, sort_keys=sort_keys
        )


def main(changelist):
    file_process_dict = gather_file_process_list(changelist)
    write_json(
        file_process_dict,
        "E:/repos/py_in_the_sky_2024/examples/trigger_example_{}.json".format(
            changelist
        ),
    )


if __name__ == "__main__":
    main(961)  # good image
