import json
from typing import Any
from uuid import uuid4
from lambda_handlers.handlers.lambda_handler import Event, LambdaContext
from botocore.exceptions import ClientError
import boto3
import validators


def write_to_dynamodb(callback_url: str, file_id: str) -> None:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('files-table')
    try:
        table.put_item(
            Item={
                'fileid': file_id,
                'callback_url': callback_url,
            }
        )
    except ClientError as e:
        print(f"Error writing to DynamoDB: {e}")
        raise


def lambda_handler(event: Event, context: LambdaContext) -> dict[str, Any]:
    try:
        callback_url = event["body"]
        # Check if the callback_url is a valid URL
        if not validators.url(callback_url):
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Invalid URL"}),
            }
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
    except KeyError as e:
        print(f"KeyError: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps({"error": "Invalid request"}),
        }
    except Exception as e:
        print(f"Unhandled error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": "Internal server error"}),
        }
