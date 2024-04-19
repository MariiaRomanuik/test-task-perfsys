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
from aiohttp import ClientSession, ClientResponseError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class LambdaHandler:
    """Asynchronously sends a POST request."""

    @staticmethod
    async def async_post_request(callback_url: str, payload: dict, headers: dict) -> str:
        async with ClientSession() as session, session.post(
                callback_url, json=payload, headers=headers, timeout=10) as response:
            try:
                response.raise_for_status()
            except ClientResponseError as e:
                logger.exception(f"HTTP error: {e.status}")
                raise e
            return await response.text()

    def lambda_handler(self, event, context) -> None:
        """Lambda function handler."""
        logger.info(f"{event=}")
        try:
            new_image_data = event["Records"][0]["dynamodb"]["NewImage"]
            extracted_text = new_image_data.get("extracted_text", {}).get("S")
            callback_url = new_image_data.get("callback_url", {}).get("S")

            if not extracted_text:
                logger.error("No extracted text found in the event data")
                return

            if not callback_url:
                logger.error("No callback URL found in the event data")
                return
            callback_url = new_image_data["callback_url"]["S"]
            if extracted_text and callback_url:
                payload = {
                    "extracted_text": extracted_text
                }
                headers = {
                    "Content-Type": "application/json"
                }
                try:
                    # Run an asynchronous post request and wait for its completion.
                    print(f"Sending POST request to: {callback_url} with payload: {payload}")
                    loop = asyncio.get_event_loop()
                    response = loop.run_until_complete(self.async_post_request(callback_url, payload, headers))
                    print(f"POST response: {response}")

                except aiohttp.ClientError as e:
                    logger.exception(f"Error making POST call: {e}")

        except KeyError as e:
            logger.exception(f"KeyError: {e}. Event data: {event}")


def handle(event, context) -> None:
    """Handles the AWS Lambda invocation."""
    handler = LambdaHandler()
    handler.lambda_handler(event, context)
