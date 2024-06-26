"""S3 Text Extractor:
Handles Lambda events triggered by S3 uploads,
extracts text using Textract, and stores it in DynamoDB.
This module defines the LambdaHandler class, which manages Lambda events triggered by S3 uploads.
It uses Textract to extract text from uploaded files and stores the extracted text in DynamoDB.
"""
import os
from typing import Optional, Any

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class LambdaHandler:
    """Manages Lambda events for S3 uploads, text extraction, and DynamoDB storage."""

    def __init__(self, table_name: str, region: str, bucket_name: str) -> None:
        """Initialize the LambdaHandler object with the specified DynamoDB table name."""
        self.region = region
        self.bucket_name = bucket_name
        self.s3 = boto3.client(
            's3', region_name=self.region, config=boto3.session.Config(signature_version='s3v4', read_timeout=1000)
        )
        self.textract = boto3.client('textract')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def create_dynamodb_item(self, file_id: str, text: str) -> None:
        """Create a new item in the DynamoDB table."""
        try:
            self.table.put_item(
                Item={'fileid': file_id, 'extracted_text': text}
            )
            print(f"Created a new item in the DynamoDB table file_id: {file_id}")
        except ClientError as e:
            logger.exception(f"Error creating DynamoDB item: {e}")

    def update_dynamodb_item(self, file_id: str, extracted_text: str) -> None:
        """Update an existing item in the DynamoDB table."""
        try:
            self.table.update_item(
                Key={'fileid': file_id},
                UpdateExpression='SET extracted_text = :extracted_text',
                ExpressionAttributeValues={':extracted_text': extracted_text}
            )
            print(f"Updated an existing item in the DynamoDB table file_id: {file_id}")
        except ClientError as e:
            logger.exception(f"Error updating DynamoDB item: {e}")

    def get_dynamodb_item(self, file_id: str) -> Optional[str]:
        """Retrieve an item from the DynamoDB table."""
        try:
            response = self.table.get_item(Key={'fileid': file_id})
            print(f"Retrieved an item from the DynamoDB table file_id: {file_id}")
            return response.get('Item')
        except ClientError as e:
            logger.exception(f"Error getting DynamoDB item: {e}")
            return None

    @staticmethod
    def get_bucket_and_key(event) -> Optional[tuple[str, str]]:
        """Extract S3 bucket and key from the event."""
        try:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            return bucket, key
        except KeyError as e:
            logger.exception(f"KeyError in getting bucket and key: {e}")
            return None

    @staticmethod
    def extract_text_from_response(response: Any) -> str:
        return '\n'.join(item.get("Text", "") for item in response['Blocks'] if item['BlockType'] == 'LINE')

    def lambda_handler(self, event, context) -> None:
        """Handle Lambda event triggered by file uploads to S3."""
        print(f"Received event: {event}")
        try:
            # Get the bucket and key from the S3 event
            bucket_data = self.get_bucket_and_key(event)
            if bucket_data is None:
                logger.error("Bucket and Key cannot be None.")
                return
            bucket, file_id = bucket_data

            response = self.textract.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': file_id}}
            )

            # Extract text from the response
            print(f"{response=}")
            text = self.extract_text_from_response(response)
            print(f"Extraction: {text}")

            # Check if the record with file_id already exists in DynamoDB
            existing_record = self.get_dynamodb_item(file_id)

            if existing_record:
                # If the record exists, update it with the extracted text
                self.update_dynamodb_item(file_id, text)
            else:
                # If the record does not exist, create a new record with the extracted text
                self.create_dynamodb_item(file_id, text)
        except (ClientError, KeyError) as e:
            print(f"Error: {e}")
            logger.exception(f"Unhandled error: {e}")


def handle(event, context) -> None:
    """Handles the AWS Lambda invocation."""
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    if not table_name:
        raise EnvironmentError("DYNAMODB_TABLE_NAME environment variable is required")
    region = os.environ.get("REGION_NAME")
    if not region:
        raise EnvironmentError("REGION_NAME environment variable is required")
    bucket_name = os.environ.get("BUCKET_NAME")
    if not bucket_name:
        raise EnvironmentError("BUCKET_NAME environment variable is required")
    handler = LambdaHandler(table_name, region, bucket_name)
    handler.lambda_handler(event, context)
