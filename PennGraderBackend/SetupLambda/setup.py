import boto3
import json
import base64
import time
import ast

ERROR        = 400
SUCCESS      = 200
IS_EXCEPTION = True

# Dynamo connection
s3 = boto3.client('s3')

def lambda_handler(payload, context):
