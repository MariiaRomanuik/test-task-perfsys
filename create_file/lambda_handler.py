"""Lambda Handler Module:
Defines the LambdaHandler class for handling AWS Lambda events.

This module contains the LambdaHandler class, which is responsible for handling AWS Lambda events
and performing operations such as writing to DynamoDB and generating presigned URLs for S3 objects.
"""

import json
import os
from typing import Any, Optional
from uuid import uuid4

from boto3.exceptions import Boto3Error
from lambda_handlers.handlers.lambda_handler import Event, LambdaContext
from botocore.exceptions import ClientError
import boto3
import validators
import logging
logger = logging.getLogger()


class LambdaHandler:
    def __init__(self, table_name: Optional[str]) -> None:
        if table_name is None:
            raise ValueError("DynamoDB table name is not configured")
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def write_to_dynamodb(self, callback_url: str, file_id: str) -> None:
        """Writes data to DynamoDB."""
        try:
            self.table.put_item(
                Item={
                    'fileid': file_id,
                    'callback_url': callback_url,
                }
            )
        except ClientError as e:
            logger.exception(f"Error writing to DynamoDB: {e}")
            raise

    def lambda_handler(self, event: Event, context: LambdaContext) -> dict[str, Any]:
        """Lambda function handler."""
        try:
            callback_url = event.get("body")
            if not callback_url:
                raise KeyError("Callback URL not found in the event body")

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
            logger.exception(f"KeyError: {e}")
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Invalid request"}),
            }
        except Boto3Error as e:
            logger.exception(f"Boto3Error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({"error": "Internal server error"}),
            }
        except Exception as e:
            logger.exception(f"Unhandled error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({"error": "Internal server error"}),
            }


def handle(event: Event, context: LambdaContext) -> dict[str, Any]:
    """Handles the AWS Lambda invocation."""
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    handler = LambdaHandler(table_name)
    return handler.lambda_handler(event, context)
