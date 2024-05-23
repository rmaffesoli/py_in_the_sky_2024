# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Shows how to run a multimodal prompt with Anthropic Claude (on demand) and InvokeModel.
"""

import json
import logging
import base64
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


INPUT_TOKEN_PRICE = 0.00000025
OUTPUT_TOKEN_PRICE = 0.00000125


DEFAULT_SYSTEM_PROMPT = """Look at the thumbnail image of this digital asset as well as any extra information provided such as file name, path, changelist description, and asset type, to create a list of tags for searching and categorizing, as well as a short description of the image so that a user could understand it without seeing the image.

Use your existing knowledge of naming conventions, folder structures, thumbnail generation, and how artists write changelist descriptions when submitting their work. Use your judgement to determine which pieces of information apply to this thumbnail and what tags and description will be most helpful for searchability later on.

Tags should be sorted in order of confidence. Put your best tags at the top. If the user tells you the file type and it is not obvious from the file extension, be sure to include it as a tag. For example, Unreal Engine assets are all .uasset files but they have many different types, like "BlueprintGeneratedClass", "Texture2D", "StaticMesh", "SkeletalMesh", etc. Do not guess about the file type if you are not sure. For example, in image is not necessarily a texture, so don't tag it as such unless you are sure.

The output should be in JSON format with the keys "tags" and "description"

Here are some examples:

<output>
{
    "tags": [
        "building",
        "castle",
        "medieval",
        "cartoon",
        "fantasy"
    ],
    "description": "A cartoon style medieval castle with a moat and drawbridge. Mountains are in the background."
}
</output>

<output>
{
    "tags": [
        "StaticMesh",
        "desk",
        "wooden",
        "executive",
        "office",
    ],
    "description": "A 3D model of a wooden executive desk with large drawers."
}
</output>

<output>
{
    "tags": [
        "Texture2D",
        "bricks",
        "wall",
        "weathered",
        "damaged",
        "dirty",
        "old"
    ],
    "description": "A weathered and damaged brick wall texture with dirt and grime. The bricks are old and some are missing."
}
</output>
"""


class ClaudeHaiku:
    def __init__(self):
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        self.bedrock_runtime = boto3.client(service_name="bedrock-runtime")
        self.max_tokens = 1024
        self.system_prompt = self._find_system_prompt_file(DEFAULT_SYSTEM_PROMPT)

    def _find_system_prompt_file(self, default_prompt):
        """
        Searches for a file called system_prompt.txt and returns its path if found.
        Returns:
            str: The path of the system_prompt.txt file if found, otherwise an empty string.
        """
        current_dir = Path.cwd()
        for file in current_dir.glob("**/system_prompt.txt"):
            return file.read_text()
        return default_prompt

    def invoke(self, message, b64image, image_type):
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_type,
                            "data": (
                                b64image.decode("utf-8")
                                if isinstance(b64image, bytes)
                                else b64image
                            ),
                        },
                    },
                    {"type": "text", "text": message},
                ],
            }
        ]
        response = self._invoke_model(messages)
        try:
            response_message = json.loads(response["content"][0]["text"])
            input_cost = response["usage"]["input_tokens"] * INPUT_TOKEN_PRICE
            output_cost = response["usage"]["output_tokens"] * OUTPUT_TOKEN_PRICE
            logger.info(f"Total Cost: ${input_cost + output_cost}")
            response_message["cost"] = input_cost + output_cost
            return response_message

        except json.JSONDecodeError as err:
            message = err.response["Error"]["Message"]
            logger.error("Response was not valid JSON: %s", message)

    def _invoke_model(self, messages):
        """
        Invokes a model with a multimodal prompt.
        Args:
            bedrock_runtime: The Amazon Bedrock boto3 client.
            model_id (str): The model ID to use.
            messages (JSON) : The messages to send to the model.
            max_tokens (int) : The maximum  number of tokens to generate.
        Returns:
            None.
        """

        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "system": self.system_prompt,
                "messages": messages,
            }
        )

        response = self.bedrock_runtime.invoke_model(body=body, modelId=self.model_id)
        response_body = json.loads(response.get("body").read())

        return response_body


def main():
    """
    Entrypoint for Anthropic Claude multimodal prompt example.
    """

    claude = ClaudeHaiku()
    input_image = "examples/SM_Chair47.uasset.png"
    input_text = json.dumps(
        {
            "filepath": "//demo_interiors_stream/library/mainline/SM_Chair47.uasset",
            "filetype": "StaticMesh",
            "changelist_description": "Copied sm_chair47.uasset from //demo_interiors_stream/unreal_library/mainline/library/content/tmchairsandtablespack1/chairsandtables/chairs/chair47",
        }
    )

    # Read reference image from file and encode as base64 strings.
    with open(input_image, "rb") as image_file:
        content_image = base64.b64encode(image_file.read()).decode("utf8")

    res = claude.invoke(input_text, content_image, "image/png")
    logger.info(res)
    print(res)
    return res


if __name__ == "__main__":
    main()
