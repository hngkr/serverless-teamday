import json
from http import HTTPStatus
from typing import Any, Dict

from aws_lambda_powertools.logging.logger import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

logger: Logger = Logger(service='lambda_api')

config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'standard'
    }
)


def start_lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    logger.debug("Received event", extra={'event': event})
    return {'statusCode': HTTPStatus.OK,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'success', 'event': event})}


def stop_lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    logger.debug("Received event", extra={'event': event})
    return {'statusCode': HTTPStatus.OK,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'success', 'event': event})}
