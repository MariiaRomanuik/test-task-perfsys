import boto3

s3 = boto3.client('s3')
textract = boto3.client('textract')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('files-table')


def create_dynamodb_item(file_id, text):
    table.put_item(
        Item={'fileid': file_id, 'extracted_text': text}
    )


def update_dynamodb_item(file_id, text):
    table.update_item(
        Key={'fileid': file_id},
        UpdateExpression='SET extracted_text = :val',
        ExpressionAttributeValues={':val': text}
    )


def get_dynamodb_item(file_id):
    response = table.get_item(Key={'fileid': file_id})
    return response.get('Item')


def get_bucket_and_key(event):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    return bucket, key


def lambda_handler(event, lambda_context):
    # Get the bucket and key from the S3 event
    bucket, key = get_bucket_and_key(event)

    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
    )

    # Extract text from the response
    text = ''
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            text += item['Text'] + '\n'

        # Get the file_id from the key (assuming file_id is part of the key)
        file_id = key.split('/')[0]

        # Check if the record with file_id already exists in DynamoDB
        existing_record = get_dynamodb_item(file_id)

        if existing_record:
            # If the record exists, update it with the extracted text
            update_dynamodb_item(file_id, text)
        else:
            # If the record does not exist, create a new record with the extracted text
            create_dynamodb_item(file_id, text)

