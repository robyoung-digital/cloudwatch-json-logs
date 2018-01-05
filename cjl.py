"""
This is the top
"""
import re
import datetime
import json
import pytz

from docopt import docopt
import boto3
import dateutil.parser


def parse_time(t):
    if t:
        match = re.match(r'(\d+)(m|h|d)', t)
        if match:
            unit = {
                'm': 'minutes',
                'h': 'hours',
                'd': 'days',
            }[match.group(2)]
            kwargs = {unit: int(match.group(1))}

            stamp = datetime.datetime.utcnow() - datetime.timedelta(**kwargs)
            return int(stamp.timestamp() * 1000)
        else:
            raise NotImplemented()


def parse_filter(filter):
    if filter:
        result = '{ '
        result += re.sub(
            r'( |^|\()(\w+)\s?(=|!=|<|>|<=|>=| IS| NOT)',
            r'\1$.\2\3',
            filter
        )
        result += ' }'

        return result


def load_fields(fields):
    fields = fields or 'aws.timestamp_py,service,log_type,message'

    return fields.split(',')


def parse_event(event):
    event['message'] = json.loads(event['message'])

    output = event.pop('message')
    if 'timestamp' in output:
        output['timestamp'] = dateutil.parser.parse(output['timestamp'])
        output['timestamp'] = output['timestamp'].replace(tzinfo=pytz.UTC)

    output = {
        **output,
        **{f'aws.{key}': value for key, value in event.items()}
    }

    output['aws.timestamp_py'] = datetime.datetime.fromtimestamp(
        output['aws.timestamp'] / 1000
    )
    return output


def stream_events(paginator):
    for page in paginator:
        for event in page['events']:
            yield parse_event(event)


def main():
    """CloudWatch JSON Logs

    Usage:
      cjl [-hf -s <start> -e <end>] [-r|-o <fields>] <log_group> [<filter>]

    Options:
      -h --help                      Show this screen
      -f --force-order               Load all events and sort before outputing
      -r --raw                       Raw JSON output
      -s <start> --start=<start>     Start time [default: 6h]
      -e <end> --end=<end>           End time
      -o <fields> --output=<fields>  Output fields to use eg. 'field1,field2'

    Time formats:
      Times can be either ISO8601 or relative.
      If they are an ISO8601 start will use the start of the ISO8601 period
      and end will use the end.
      eg.
      --start=2018-01-01 --end=2018-01-02 is equivalent to
      --start=2018-01-01T00:00:00Z --end=2018-01-03T00:00:00Z
      If relative it should be an integer followed my a unit specifier.
      Valid unit specifiers are m for minute, h for hour, d for day
      eg. 6h is six hours back

    Output fields:
      The output fields are listed out in the order they should be displayed.

    Examples:
      cjl -s 6h myloggroup 'service=agent-service && request_id=blahblah'
    """
    arguments = docopt(main.__doc__, version='0.0.1')
    fields = load_fields(arguments['--output'])

    client = boto3.client('logs')
    paginator = client.get_paginator('filter_log_events')

    kwargs = {
        'logGroupName': arguments['<log_group>'],
        'startTime': parse_time(arguments['--start']),
        'endTime': parse_time(arguments['--end']),
        'filterPattern': parse_filter(arguments['<filter>']),
        'interleaved': True
    }
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    p = paginator.paginate(**kwargs)

    events = stream_events(p)
    if arguments['--force-order']:
        events = sorted(events, key=lambda event: event['timestamp'])
    for event in events:
        values = [
            str(event.get(field, '')) for field in fields
        ]
        print('\t'.join(values))
