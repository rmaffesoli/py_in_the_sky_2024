import asyncio
import json
import logging

from . import aws_claude

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

claude = aws_claude.ClaudeHaiku()


def process_changelist(file_process_dict: dict):
    items = []
    for file in file_process_dict["file_list"]:
        message = json.dumps(
            {
                "changelist_description": file_process_dict["desc"],
                "filepath": file["depot_path"].split("@")[0],
            }
        )
        items.append(
            {
                "depot_path": file["depot_path"],
                "message": message,
                "b64image": file["thumb"],
                "image_type": file["thumb_type"],
            }
        )
    output = []

    async def _process_items(items, output):
        tasks = [_invoke_async(item) for item in items]
        results = await asyncio.gather(*tasks)
        output.extend(results)

    asyncio.run(_process_items(items, output))

    total_cost = sum([result["cost"] for result in output])
    logger.info(f"Total Cost: ${total_cost}")

    return output


async def _invoke_async(item):
    response = claude.invoke(item["message"], item["b64image"], item["image_type"])
    response["depot_path"] = item["depot_path"]
    return response
