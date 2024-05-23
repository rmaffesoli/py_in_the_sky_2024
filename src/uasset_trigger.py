from pathlib import Path
import logging

from P4 import P4, P4Exception

from uasset_analyzer import UassetReader
import tempfile


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

p4 = P4()
p4.connect()


def main(changelist):
    description = get_changelist_description(changelist)
    if not description:
        return
    files = filter_files(description)
    if not files:
        return

    logger.info(f"Analyzing {len(files)} files")
    results = analyze_files(files, changelist)
    logger.info(results)
    return results


def get_changelist_description(changelist):
    try:
        description = p4.run("describe", "-s", changelist)[0]
    except P4Exception as e:
        logger.error(f"Failed to get changelist description: {e}")
        return None

    return description


def filter_files(description):
    file_list = []
    for i, depot_file in enumerate(description["depotFile"]):
        # Skip files that are not uasset or are ExternalActors or ExternalObjects
        if not depot_file.endswith(".uasset") or "__External" in depot_file:
            continue
        action = description["action"][i]
        if "delete" in action:
            continue
        file_list.append(f"{depot_file}")

    return file_list


def analyze_files(files, changelist):
    results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        for depot_path in files:
            path = Path(depot_path)
            sub_path = Path(*path.parts[1:])
            p4.run("print", "-o", temp_path / sub_path, f"{depot_path}@{changelist}")
            uasset_type = None
            saved_by_version = None
            compatible_with_version = None
            try:
                uasset = UassetReader(temp_path / sub_path)
                uasset_type = (
                    uasset.thumbnails[0].get("AssetClassName", None)
                    if uasset.thumbnails
                    else None
                )
                saved_by_version = uasset.header["SavedByEngineVersion"]
                compatible_with_version = uasset.header["CompatibleWithEngineVersion"]
            except Exception as err:
                logger.error(f"Failed to analyze {depot_path}: {err}")
            results.append(
                {
                    "change": changelist,
                    "depot_path": depot_path,
                    "uasset_type": uasset_type,
                    "saved_by_version": saved_by_version,
                    "compatible_with_version": compatible_with_version,
                }
            )
    return results


if __name__ == "__main__":
    main(998)
