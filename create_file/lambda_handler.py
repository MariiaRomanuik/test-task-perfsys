import json
import boto3


def write_to_dynamodb(callback_url, presigned_url):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('files-table')
    table.put_item(
        Item={
            'fileid': '1',
            'callback_url': callback_url,
            'presigned_url': presigned_url
        }
    )


def lambda_handler(event):
    callback_url = event["body"]
    s3_client = boto3.client('s3')
    presigned_url = s3_client.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': 'perfsysstorage',
            'Key': 'file_name'
        },
        ExpiresIn=3600
    )

    write_to_dynamodb(callback_url, presigned_url)

    return {
        'statusCode': 200,
        'body': json.dumps(presigned_url)
    }