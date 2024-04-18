"""DynamoDB Callback Handler:
Defines the LambdaHandler class for handling DynamoDB events.
This module contains the LambdaHandler class, which handles DynamoDB events
triggered by changes to the database. Upon receiving an event,
it extracts relevant data, such as extracted text, and
sends a POST request to a callback URL with the extracted text
included in the request body.
"""
import logging
import asyncio
import aiohttp
from aiohttp import ClientSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class LambdaHandler:
    """Asynchronously sends a POST request."""
    @staticmethod
    async def async_post_request(callback_url: str, payload: dict, headers: dict) -> str:
        async with ClientSession() as session, session.post(
                callback_url, json=payload, headers=headers, timeout=10) as response:
            return await response.text()

    def lambda_handler(self, event, context) -> None:
        """Lambda function handler."""
        logger.info(f"{event=}")
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
                    # Run an asynchronous post request and wait for its completion.
                    loop = asyncio.get_event_loop()
                    response = loop.run_until_complete(self.async_post_request(callback_url, payload, headers))
                    response.raise_for_status()
                    logger.info(f"POST response: {response.text}")
                except aiohttp.ClientError as e:
                    logger.exception(f"Error making POST call: {e}")
        except KeyError as e:
            logger.exception(f"KeyError: {e}. Event data: {event}")


def handle(event, context) -> None:
    """Handles the AWS Lambda invocation."""
    handler = LambdaHandler()
    handler.lambda_handler(event, context)
