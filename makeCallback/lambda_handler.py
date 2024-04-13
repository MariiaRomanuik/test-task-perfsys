import json
import requests
from lambda_handlers.handlers.lambda_handler import LambdaContext, Event
from requests import RequestException


def lambda_handler(event: Event, context: LambdaContext) -> None:
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
                response = requests.post(callback_url, data=json.dumps(payload), headers=headers)
                print("POST response:", response.text)
            except RequestException as e:
                print("Error making POST call:", e)
    except KeyError as e:
        print("KeyError:", e)
