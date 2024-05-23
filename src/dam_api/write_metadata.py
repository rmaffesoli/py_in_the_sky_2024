#!/usr/bin/env python
from __future__ import print_function

import os
import requests


SERVER_ADDRESS = os.environ.get('DAM_SERVER_ADDRESS')
ACCOUNT_KEY = os.environ.get('DAM_ACCOUNT_KEY')


def get_or_create_metadata_field(field_name):
    metadata_field_url = "{}/api/company/file_attribute_templates".format(SERVER_ADDRESS)
    
    all_metadata_params = {
        'account_key': ACCOUNT_KEY,
    }
        
    all_metadata_response = requests.get(
        metadata_field_url, 
        params=all_metadata_params,
    )

    if all_metadata_response.status_code > 299:
        print('request failed')
        return
    
    all_metadata = all_metadata_response.json()
    
    image_description_field = [_ for _ in all_metadata['results'] if _['name'] == field_name]

    if image_description_field:
        image_description_field = image_description_field[0]
    else:
        add_metadata_field_params = {
            'account_key': ACCOUNT_KEY,
            "name": field_name,
            "type": "text",
            "available_values":[],
            "hidden": False
        }
        
        add_metadata_field_response = requests.post(
            metadata_field_url, 
            json=add_metadata_field_params,
        )

        image_description_field = add_metadata_field_response.json()

    return image_description_field


def attach_metadata(selected_asset, field_name, value):

    image_description_field = get_or_create_metadata_field(field_name)

    add_asset_metadata_url = "{}/api/p4/batch/custom_file_attributes".format(SERVER_ADDRESS)
    
    add_asset_metadata_body = {
        'account_key': ACCOUNT_KEY,
        'paths':[
            {
                'path': selected_asset
            }
        ],
        'create': [
            {
                'uuid': image_description_field['uuid'],
                'value': value
            }
        ]
    }
        
    if '@' in selected_asset:
        asset_path, asset_identifier = selected_asset.split('@')
        add_asset_metadata_body['paths'][0]['path'] = asset_path
        add_asset_metadata_body['paths'][0]['identifier'] = asset_identifier

    add_asset_metadata_response = requests.put(
        add_asset_metadata_url, 
        json=add_asset_metadata_body,
    )

    print(add_asset_metadata_response)
    try:
        print(add_asset_metadata_response.json())
    except:
        print('no metadata json')

def attach_additional_tags(selected_asset, tags):
    if not tags:
        return
    
    add_asset_tags_url = "{}/api/p4/batch/tags".format(SERVER_ADDRESS)
    add_asset_tags_body = {
        'account_key': ACCOUNT_KEY,
        'paths':[
            {
                'path': selected_asset
            }
        ],
        'create_auto': tags,

    }
        
    if '@' in selected_asset:
        asset_path, asset_identifier = selected_asset.split('@')
        add_asset_tags_body['paths'][0]['path'] = asset_path
        add_asset_tags_body['paths'][0]['identifier'] = asset_identifier

    add_asset_tags_response = requests.put(
        add_asset_tags_url, 
        json=add_asset_tags_body,
    )

    print(add_asset_tags_response)
    try:
        print(add_asset_tags_response.json())
    except:
        print('no tags json')
