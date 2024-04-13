from typing import Optional

import boto3
from botocore.exceptions import ClientError
from lambda_handlers.handlers.lambda_handler import Event, LambdaContext


s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('files-table')


def create_dynamodb_item(file_id: str, text: str) -> None:
    try:
        table.put_item(
            Item={'fileid': file_id, 'extracted_text': text}
        )
    except ClientError as e:
        print(f"Error creating DynamoDB item: {e}")

def update_dynamodb_item(file_id: str, text: str) -> None:
    try:
        table.update_item(
            Key={'fileid': file_id},
            UpdateExpression='SET extracted_text = :val',
            ExpressionAttributeValues={':val': text}
        )
    except ClientError as e:
        print(f"Error updating DynamoDB item: {e}")

def get_dynamodb_item(file_id: str) -> Optional[str]:
    try:
        response = table.get_item(Key={'fileid': file_id})
        return response.get('Item')
    except ClientError as e:
        print(f"Error getting DynamoDB item: {e}")
        return None

def get_bucket_and_key(event: Event) -> tuple[str, str]:
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        return bucket, key
    except KeyError as e:
        print(f"KeyError in getting bucket and key: {e}")
        return None, None

def lambda_handler(event: Event, context: LambdaContext) -> None:
    try:
        # Get the bucket and key from the S3 event
        bucket, file_id = get_bucket_and_key(event)

        response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': bucket, 'Name': file_id}}
        )

        # Extract text from the response
        text = ''
        for item in response['Blocks']:
            if item['BlockType'] == 'LINE':
                text += item['Text'] + '\n'

        # Check if the record with file_id already exists in DynamoDB
        existing_record = get_dynamodb_item(file_id)

        if existing_record:
            # If the record exists, update it with the extracted text
            update_dynamodb_item(file_id, text)
        else:
            # If the record does not exist, create a new record with the extracted text
            create_dynamodb_item(file_id, text)
    except Exception as e:
        print(f"Unhandled error: {e}")
