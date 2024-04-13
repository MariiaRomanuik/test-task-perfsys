"""S3 Text Extractor: Handles Lambda events triggered by S3 uploads, extracts text using Textract,
and stores it in DynamoDB.

This module defines the LambdaHandler class, which manages Lambda events triggered by S3 uploads.
It uses Textract to extract text from uploaded files and stores the extracted text in DynamoDB.
"""
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from lambda_handlers.handlers.lambda_handler import Event, LambdaContext


class LambdaHandler:
    def __init__(self, table_name: Optional[str]):
        """Initialize the LambdaHandler object with the specified DynamoDB table name."""
        if not table_name:
            raise ValueError("DynamoDB table name is not configured")
        self.s3 = boto3.client('s3')
        self.textract = boto3.client('textract')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def create_dynamodb_item(self, file_id: str, text: str) -> None:
        """Create a new item in the DynamoDB table."""
        try:
            self.table.put_item(
                Item={'fileid': file_id, 'extracted_text': text}
            )
        except ClientError as e:
            print(f"Error creating DynamoDB item: {e}")

    def update_dynamodb_item(self, file_id: str, text: str) -> None:
        """Update an existing item in the DynamoDB table."""
        try:
            self.table.update_item(
                Key={'fileid': file_id},
                UpdateExpression='SET extracted_text = :val',
                ExpressionAttributeValues={':val': text}
            )
        except ClientError as e:
            print(f"Error updating DynamoDB item: {e}")

    def get_dynamodb_item(self, file_id: str) -> Optional[str]:
        """Retrieve an item from the DynamoDB table."""
        try:
            response = self.table.get_item(Key={'fileid': file_id})
            return response.get('Item')
        except ClientError as e:
            print(f"Error getting DynamoDB item: {e}")
            return None

    @staticmethod
    def get_bucket_and_key(event: Event) -> Optional[tuple[str, str]]:
        """Extract S3 bucket and key from the event."""
        try:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            return bucket, key
        except KeyError as e:
            print(f"KeyError in getting bucket and key: {e}")
            return None

    def lambda_handler(self, event: Event, context: LambdaContext) -> None:
        """Handle Lambda event triggered by file uploads to S3."""
        try:
            # Get the bucket and key from the S3 event
            bucket, file_id = self.get_bucket_and_key(event)

            response = self.textract.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': file_id}}
            )

            # Extract text from the response
            text = ''.join(item['Text'] + '\n' for item in response['Blocks'] if item['BlockType'] == 'LINE')

            # Check if the record with file_id already exists in DynamoDB
            existing_record = self.get_dynamodb_item(file_id)

            if existing_record:
                # If the record exists, update it with the extracted text
                self.update_dynamodb_item(file_id, text)
            else:
                # If the record does not exist, create a new record with the extracted text
                self.create_dynamodb_item(file_id, text)
        except Exception as e:
            print(f"Unhandled error: {e}")


def handle(event: Event, context: LambdaContext) -> None:
    """Handles the AWS Lambda invocation."""
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    handler = LambdaHandler(table_name)
    handler.lambda_handler(event, context)
