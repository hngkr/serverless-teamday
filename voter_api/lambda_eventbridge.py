import json
from http import HTTPStatus
from typing import Any, Dict

from aws_lambda_powertools.logging.logger import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

logger: Logger = Logger(service='lambda_eventbridge')

config = Config(
    retries = {
        'max_attempts': 5,
        'mode': 'standard'
    }
)


def process_message_lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    logger.debug("Received event from bus", extra={'event': event})

    return {'statusCode': HTTPStatus.OK,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'success', 'event': event})}
