import logging

from trigger import claude_api_trigger
import tagging_ai


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main(changelist):
    file_process_dict: dict = claude_api_trigger.gather_file_process_list(changelist)

    logger.info(
        f"Processing changelist {changelist}. {len(file_process_dict['file_list'])} files to process."
    )

    ai_results = tagging_ai.process_changelist(file_process_dict)

    logger.info(ai_results)
    return ai_results


if __name__ == "__main__":
    main(1007)
