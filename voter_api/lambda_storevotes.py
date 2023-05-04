import os
import json
import boto3
import base64
from http import HTTPStatus
from typing import Any, Dict

from aws_lambda_powertools.logging.logger import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

logger: Logger = Logger(service='lambda_storevotes')

config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'standard'
    }
)

votes_table_name = os.environ['VOTES_TABLE_NAME']
votes_eventbus_name = os.environ['VOTES_EVENTBUS_NAME']

dynamodb = boto3.resource("dynamodb", config=config)
votes_table = dynamodb.Table(votes_table_name)

events = boto3.client('events', config=config)


def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    logger.set_correlation_id(context.aws_request_id)
    logger.debug("Received event", extra={'event': event})

    for record in event['Records']:
        base64_payload = record['kinesis']['data']
        data = json.loads(base64.b64decode(base64_payload))

        if 'message' in data:
            deliver_vote_with_message_to_eventbridge(data)

        update_and_increase_item(votes_table, {'id': f'{data["phoneNo"]}#{data["vote"]}'}, {})

    return {'statusCode': HTTPStatus.OK,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'success', 'event': event})}


def deliver_vote_with_message_to_eventbridge(data: Dict) -> None:
    events.put_events(
        Entries=[
            {
                'Detail': json.dumps(data),
                'DetailType': 'voteMessageReceived',
                'Resources': [
                    data['message'],
                ],
                'Source': 'voteMessageReceived',
                'EventBusName': votes_eventbus_name
            }
        ]
    )


def update_and_increase_item(table: dynamodb.Table, item_key: Dict, attributes: Dict, increment: int = 1) -> Dict:
    """
    Update item or create new. If the item already exists, return the previous value and
    increase the counter: update_counter.
    """
    # Init update-expression
    update_expression = "SET"

    # Build expression-attribute-names, expression-attribute-values, and the update-expression
    expression_attribute_names = {}
    expression_attribute_values = {}
    for key, value in attributes.items():
        update_expression += f' #{key} = :{key},'  # Notice the "#" to solve issue with reserved keywords
        expression_attribute_names[f'#{key}'] = key
        expression_attribute_values[f':{key}'] = value

    # Add counter start and increment attributes
    expression_attribute_values[':_start'] = 0
    expression_attribute_values[':_inc'] = increment

    # Finish update-expression with our counter
    update_expression += " vote_counter = if_not_exists(vote_counter, :_start) + :_inc"

    return table.update_item(
        Key=item_key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="NONE"
    )
