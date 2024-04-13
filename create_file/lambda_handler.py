import json
import os
from typing import Any, Optional
from uuid import uuid4

from boto3.exceptions import Boto3Error
from lambda_handlers.handlers.lambda_handler import Event, LambdaContext
from botocore.exceptions import ClientError
import boto3
import validators


class LambdaHandler:
    def __init__(self, table_name: Optional[str]):
        if table_name is None:
            raise ValueError("DynamoDB table name is not configured")
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def write_to_dynamodb(self, callback_url: str, file_id: str) -> None:
        try:
            self.table.put_item(
                Item={
                    'fileid': file_id,
                    'callback_url': callback_url,
                }
            )
        except ClientError as e:
            print(f"Error writing to DynamoDB: {e}")
            raise

    def lambda_handler(self, event: Event, context: LambdaContext) -> dict[str, Any]:
        try:
            callback_url = event["body"]
            # Check if the callback_url is a valid URL
            if not validators.url(callback_url):
                return {
                    'statusCode': 400,
                    'body': json.dumps({"error": "Invalid URL"}),
                }
            file_id = uuid4().hex
            presigned_url = self.s3.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': 'perfsysstorage',
                    'Key': file_id
                },
                ExpiresIn=3600
            )

            self.write_to_dynamodb(callback_url, file_id)
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
        except Boto3Error as e:
            print(f"Boto3Error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({"error": "Internal server error"}),
            }
        except Exception as e:
            print(f"Unhandled error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({"error": "Internal server error"}),
            }


def handle(event: Event, context: LambdaContext) -> dict[str, Any]:
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    handler = LambdaHandler(table_name)
    return handler.lambda_handler(event, context)
