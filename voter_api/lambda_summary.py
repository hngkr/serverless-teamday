import os
import re
import sys
import json
import six
import boto3
import decimal
import datetime
from http import HTTPStatus
from typing import Any, Dict
from collections import defaultdict

from aws_lambda_powertools.logging.logger import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

logger: Logger = Logger(service='lambda_summary')

config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'standard'
    }
)

dynamodb = boto3.resource("dynamodb", config=config)

summary_table_name = os.environ.get('SUMMARY_TABLE_NAME', '')


def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    logger.debug("Received event", extra={'event': event})

    votes_summary = defaultdict(int)

    for record in event['Records']:
        if 'dynamodb' in record:
            if record.get('eventName', '') in ['INSERT', 'MODIFY']:
                if 'NewImage' in record['dynamodb']:
                    change_item_dynamodb = record['dynamodb']['NewImage']
                    change_item = loads(change_item_dynamodb)
                    vote_counter = change_item['vote_counter']
                    vote = change_item['vote']
                    if vote_counter < 6:
                        votes_summary[vote] += 1

    for vote, count in votes_summary.items():
        update_and_increase_item(summary_table_name,
                                 {'id': str(vote)},
                                 {'updated_at': datetime.datetime.now().isoformat()},
                                 increment=count)

    return {'statusCode': HTTPStatus.OK,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'message': 'success', 'event': event})}


def object_hook(dct):
    """ DynamoDB object hook to return python values """
    try:
        # First - Try to parse the dct as DynamoDB parsed
        if 'BOOL' in dct:
            return dct['BOOL']
        if 'S' in dct:
            val = dct['S']
            try:
                return datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S.%f')
            except:
                return str(val)
        if 'SS' in dct:
            return list(dct['SS'])
        if 'N' in dct:
            if re.match("^-?\d+?\.\d+?$", dct['N']) is not None:
                return float(dct['N'])
            else:
                try:
                    return int(dct['N'])
                except:
                    return int(dct['N'])
        if 'B' in dct:
            return str(dct['B'])
        if 'NS' in dct:
            return set(dct['NS'])
        if 'BS' in dct:
            return set(dct['BS'])
        if 'M' in dct:
            return dct['M']
        if 'L' in dct:
            return dct['L']
        if 'NULL' in dct and dct['NULL'] is True:
            return None
    except:
        return dct

    # In a Case of returning a regular python dict
    for key, val in six.iteritems(dct):
        if isinstance(val, six.string_types):
            try:
                dct[key] = datetime.datetime.strptime(val, '%Y-%m-%dT%H:%M:%S.%f')
            except:
                # This is a regular Basestring object
                pass

        if isinstance(val, decimal.Decimal):
            if val % 1 > 0:
                dct[key] = float(val)
            elif six.PY3:
                dct[key] = int(val)
            elif val < sys.maxsize:
                dct[key] = int(val)
            else:
                dct[key] = int(val)

    return dct


def loads(s, as_dict=False, *args, **kwargs):
    """ Loads dynamodb json format to a python dict.
        :param s - the json string or dict (with the as_dict variable set to True) to convert
        :returns python dict object
    """
    if as_dict or (not isinstance(s, six.string_types)):
        s = json.dumps(s)
    kwargs['object_hook'] = object_hook
    return json.loads(s, *args, **kwargs)


def update_and_increase_item(table_name: str, item_key: Dict, attributes: Dict, increment: int = 1) -> Dict:
    """
    Update item or create new. If the item already exists, return the previous value and
    increase the counter: update_counter.
    """
    table = dynamodb.Table(table_name)

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
