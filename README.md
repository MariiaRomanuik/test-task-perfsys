# Text Extraction API

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Description

Text Extraction API is a serverless application built on AWS that handles file processing tasks. It includes AWS Lambda functions triggered by S3 events, DynamoDB for storing metadata, and an API Gateway endpoint for interacting with the application.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Installation

To deploy the project locally, follow these steps:

1. Clone the repository: `git clone https://github.com/MariiaRomanuik/test-task-perfsys.git`
2. Navigate to the project directory: `cd test-task-perfsys`
3. Install dependencies: `npm install`
4. Deploy the project: `serverless deploy`

## Usage

After deployment, you can use the following endpoints:

- POST /files: Upload a file to trigger processing.
- GET /files/{fileid}: Retrieve processed file information.


## License

    This project is licensed under the terms of the MIT license.

