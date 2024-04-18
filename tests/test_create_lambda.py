import unittest
from unittest.mock import MagicMock, patch
from create_file.lambda_handler import LambdaHandler


class TestLambdaHandler(unittest.TestCase):
    def setUp(self):
        self.handler = LambdaHandler("test_table", "test_bucket", "us-east-1")

    # @patch('boto3.client')
    # @patch('boto3.resource')
    # def test_write_to_dynamodb(self, mock_resource):
    #     table_mock = MagicMock()
    #     mock_resource.return_value.Table.return_value = table_mock
    #
    #     file_id = "test_file_id"
    #     callback_url = "test_callback_url"
    #     self.handler.write_to_dynamodb(callback_url, file_id)
    #
    #     table_mock.put_item.assert_called_once_with(Item={'fileid': file_id, 'callback_url': callback_url})
    #
    # @patch('boto3.client')
    # def test_lambda_handler_success(self, mock_client):
    #     mock_generate_presigned_url = MagicMock(return_value="test_presigned_url")
    #     mock_client.return_value.generate_presigned_url = mock_generate_presigned_url
    #
    #     event = {"body": "test_callback_url"}
    #     context = MagicMock()
    #
    #     response = self.handler.lambda_handler(event, context)
    #
    #     self.assertEqual(response['statusCode'], 200)
    #     self.assertIn('presigned_url', response['body'])

    def test_lambda_handler_missing_callback_url(self):
        event = {}
        context = MagicMock()

        response = self.handler.lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('error', response['body'])


if __name__ == '__main__':
    unittest.main()
