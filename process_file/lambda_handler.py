import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from lambda_handlers.handlers.lambda_handler import Event, LambdaContext


class LambdaHandler:
    def __init__(self, table_name: Optional[str]):
        if not table_name:
            raise ValueError("DynamoDB table name is not configured")
        self.s3 = boto3.client('s3')
        self.textract = boto3.client('textract')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def create_dynamodb_item(self, file_id: str, text: str) -> None:
        try:
            self.table.put_item(
                Item={'fileid': file_id, 'extracted_text': text}
            )
        except ClientError as e:
            print(f"Error creating DynamoDB item: {e}")

    def update_dynamodb_item(self, file_id: str, text: str) -> None:
        try:
            self.table.update_item(
                Key={'fileid': file_id},
                UpdateExpression='SET extracted_text = :val',
                ExpressionAttributeValues={':val': text}
            )
        except ClientError as e:
            print(f"Error updating DynamoDB item: {e}")

    def get_dynamodb_item(self, file_id: str) -> Optional[str]:
        try:
            response = self.table.get_item(Key={'fileid': file_id})
            return response.get('Item')
        except ClientError as e:
            print(f"Error getting DynamoDB item: {e}")
            return None

    @staticmethod
    def get_bucket_and_key(event: Event) -> tuple[Optional[str], Optional[str]]:
        try:
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']
            return bucket, key
        except KeyError as e:
            print(f"KeyError in getting bucket and key: {e}")
            return None, None

    def lambda_handler(self, event: Event, context: LambdaContext) -> None:
        try:
            # Get the bucket and key from the S3 event
            bucket, file_id = self.get_bucket_and_key(event)

            response = self.textract.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': file_id}}
            )

            # Extract text from the response
            text = ''
            for item in response['Blocks']:
                if item['BlockType'] == 'LINE':
                    text += item['Text'] + '\n'

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
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    handler = LambdaHandler(table_name)
    handler.lambda_handler(event, context)
