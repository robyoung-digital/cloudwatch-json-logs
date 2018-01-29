# CloudWatch JSON Logs

A command line tool for querying over JSON logs in CloudWatch.


## Installation

```
> pip install git+https://github.com/robyoung-digital/cloudwatch-json-logs.git
```

## Usage

```
> aws-vault exec <aws-role> -- cjl -s 30m <log-group> '<filter>'
```
