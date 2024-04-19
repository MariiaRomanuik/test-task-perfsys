"""
This module defines the LambdaHandler class, which handles HTTP requests triggered by API Gateway,
retrieves Textract results for specified files from DynamoDB, and returns the results as a JSON response.
"""
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class LambdaHandler:
    def __init__(self, table_name: str) -> None:
        """Initialize the LambdaHandler object."""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name
        self.table = self.dynamodb.Table(self.table_name)

    def lambda_handler(self, event, context):
        try:
            logger.info(f"{event=}")
            # Retrieve fileid from the path parameters
            fileid = event['pathParameters']['fileid']

            # Retrieve textract results for the specified file from DynamoDB
            response = self.table.get_item(
                Key={
                    'fileid': fileid
                }
            )

            # Check if the file exists in DynamoDB
            if 'Item' in response:
                logger.info(f"Item : {response['Item']}")
                # Return the textract results as JSON response
                return {
                    "statusCode": 200,
                    "body": json.dumps(response['Item'])
                }
            else:
                # Return 404 if the file is not found
                logger.error(f"File with file id: {fileid} not found")
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": "File not found"})
                }
        except KeyError:
            # Return 400 if 'pathParameters' or 'fileid' key is missing
            logger.exception("KeyError: 'pathParameters' or 'fileid' not found")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid request: 'fileid' not found in path parameters"})
            }
        except ClientError as e:
            # Return 500 if DynamoDB ClientError occurs
            logger.exception(f"DynamoDB ClientError: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Internal server error"})
            }


def handle(event, context):
    """Handles the AWS Lambda invocation."""
    table_name = os.environ.get("DYNAMODB_TABLE_NAME")
    if not table_name:
        raise EnvironmentError("DYNAMODB_TABLE_NAME environment variable is required")
    handler = LambdaHandler(table_name)
    return handler.lambda_handler(event, context)
