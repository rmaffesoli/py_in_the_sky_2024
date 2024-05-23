import logging
import argparse

import environment

from trigger import claude_api_trigger
from dam_api.write_metadata import attach_metadata, attach_additional_tags
import tagging_ai


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main(changelist):
    file_process_dict: dict = claude_api_trigger.gather_file_process_list(changelist)

    logger.info(
        f"Processing changelist {changelist}. {len(file_process_dict['file_list'])} files to process."
    )

    ai_results = tagging_ai.process_changelist(file_process_dict)

    for result in ai_results:
        attach_metadata(
            result["depot_path"], "image description", result["description"]
        )
        attach_additional_tags(result["depot_path"], result["tags"])

    logger.info(ai_results)
    return ai_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("changelist")

    parsed_args = parser.parse_args()
    main(parsed_args.changelist)
