import json
from typing import Any
from uuid import uuid4
from lambda_handlers.handlers.lambda_handler import Event, LambdaContext

import boto3


def write_to_dynamodb(callback_url: str, file_id: str) -> None:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('files-table')
    table.put_item(
        Item={
            'fileid': file_id,
            'callback_url': callback_url,
        }
    )


def lambda_handler(event: Event, context: LambdaContext) -> dict[str, Any]:
    callback_url = event["body"]  # TODO: check if it is a valid url
    s3_client = boto3.client('s3')
    file_id = uuid4().hex
    presigned_url = s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': 'perfsysstorage',
            'Key': file_id
        },
        ExpiresIn=3600
    )

    write_to_dynamodb(callback_url, file_id)
    return {
        'statusCode': 200,
        'body': json.dumps(presigned_url),
    }
