"""DynamoDB Callback Handler: Defines the LambdaHandler class for handling DynamoDB events.

This module contains the LambdaHandler class, which handles DynamoDB events triggered by changes
to the database. Upon receiving an event, it extracts relevant data, such as extracted text, and
sends a POST request to a callback URL with the extracted text included in the request body.
"""

from lambda_handlers.handlers.lambda_handler import LambdaContext, Event
from requests.exceptions import RequestException

from asyncio import run
from aiohttp import ClientSession


class LambdaHandler:
    """Asynchronously sends a POST request."""
    @staticmethod
    async def async_post_request(callback_url, payload, headers):
        async with ClientSession() as session:
            async with session.post(callback_url, json=payload, headers=headers, timeout=10) as response:
                return await response.text()

    def lambda_handler(self, event: Event, context: LambdaContext) -> None:
        """Lambda function handler."""
        try:
            extracted_text = event["Records"][0]["dynamodb"]["NewImage"]["extracted_text"]["S"]
            callback_url = event["Records"][0]["dynamodb"]["NewImage"]["callback_url"]["S"]
            if extracted_text:
                payload = {
                    "extracted_text": extracted_text
                }
                headers = {
                    "Content-Type": "application/json"
                }
                try:
                    response = run(self.async_post_request(callback_url, payload, headers))
                    response.raise_for_status()
                    print("POST response:", response.text)
                except RequestException as e:
                    print("Error making POST call:", e)
        except KeyError as e:
            print("KeyError:", e, "Event data:", event)


def handle(event: Event, context: LambdaContext) -> None:
    """Handles the AWS Lambda invocation."""
    handler = LambdaHandler()
    handler.lambda_handler(event, context)
