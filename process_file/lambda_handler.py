import boto3

s3 = boto3.client('s3')
textract = boto3.client('textract')


def lambda_handler(event):
    # Get the bucket and key from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    response = textract.detect_document_text(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}}
    )

    # Extract text from the response
    text = ''
    for item in response['Blocks']:
        if item['BlockType'] == 'LINE':
            text += item['Text'] + '\n'

    return {
        'statusCode': 200,
        'body': text
    }
