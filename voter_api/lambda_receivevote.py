import os
import json
import boto3
from http import HTTPStatus
from typing import Any, Dict

from aws_lambda_powertools.logging.logger import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

logger: Logger = Logger(service='lambda_receivevote')

config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'standard'
    }
)

kinesis_client = boto3.client('kinesis', config=config)

votes_inputstream_arn = os.environ.get('VOTES_INPUTSTREAM_ARN', '')


def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    logger.set_correlation_id(context.aws_request_id)
    logger.info("Received event", extra={'event': event})

    kinesis_record = {}
    if 'body' in event:
        kinesis_record = json.loads(event['body'])
        kinesis_record['sourceIp'] = event['requestContext']['http']['sourceIp']
        kinesis_record['awsRequestId'] = context.aws_request_id

        partition_key = str(kinesis_record.get('phoneNo', context.aws_request_id))

        kinesis_client.put_record(
            StreamName=votes_inputstream_arn,
            Data=json.dumps(kinesis_record),
            PartitionKey=partition_key
        )

    return {'statusCode': HTTPStatus.OK,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'success', 'kinesis_record': kinesis_record})}
