"""Lambda Handler Module:
Defines the LambdaHandler class for handling AWS Lambda events.

This module contains the LambdaHandler class, which is responsible for handling AWS Lambda events
and performing operations such as writing to DynamoDB and generating presigned URLs for S3 objects.
"""

import json
import os
from typing import Any
from uuid import uuid4

from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError
import boto3
import validators
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class UUIDGenerationError(Exception):
    """Exception raised when UUID generation fails."""


class LambdaHandler:
    def __init__(self, table_name: str, bucket_name: str, region: str) -> None:
        self.region = region
        self.s3 = boto3.client(
            's3', region_name=region,
            config=boto3.session.Config(signature_version='s3v4', read_timeout=1000),
            verify=False
        )
        self.dynamodb = boto3.resource('dynamodb')
        self.bucket_name = bucket_name
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

    def lambda_handler(self, event, context) -> dict[str, Any]:
        """Lambda function handler."""
        try:
            callback_url = event.get("body")
            if not callback_url:
                logger.error("Callback URL not found in the event body")

                return {
                    'statusCode': 400,
                    'body': json.dumps({"error": "Callback URL not found in the event body"})
                }

            # # Check if the callback_url is a valid URL
            if not validators.url(callback_url):
                return {
                    'statusCode': 400,
                    'body': json.dumps({"error": "Invalid URL"}),
                }

            file_id = self.generate_file_id()
            presigned_url = self.s3.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_id
                },
                ExpiresIn=3600
            )
            logger.info(f"{presigned_url=}")

            self.write_to_dynamodb(callback_url, file_id)
            return {
                'statusCode': 200,
                'body': json.dumps({"presigned_url": presigned_url}),
            }
        except KeyError as e:
            logger.exception(f"KeyError: {e}")
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Invalid request"}),
            }
        except ClientError as e:
            logger.exception(f"ClientError: {e}")
            return {'statusCode': 500,
                    'body': json.dumps({"error": "AWS Client error"}),
                    }
        except Boto3Error as e:
            logger.exception(f"Boto3Error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({"error": "Boto3 error"}),
                }

    @staticmethod
    def generate_file_id() -> str:
        try:
            file_id = uuid4().hex
        except (TypeError, ValueError) as e:
            message = f"Failed to generate UUID: {e}"
            logger.exception(message)
            raise UUIDGenerationError(message) from e
        return file_id


def handle(event, context) -> dict[str, Any]:
    """Handles the AWS Lambda invocation."""
    region = os.environ.get("REGION_NAME")
    if not region:
        raise EnvironmentError("REGION_NAME environment variable is required")
    bucket_name = os.environ.get("BUCKET_NAME")
    if not bucket_name:
        raise EnvironmentError("BUCKET_NAME environment variable is required")
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    if not table_name:
        raise EnvironmentError("DYNAMODB_TABLE_NAME environment variable is required")
    handler = LambdaHandler(table_name, bucket_name, region)
    return handler.lambda_handler(event, context)
