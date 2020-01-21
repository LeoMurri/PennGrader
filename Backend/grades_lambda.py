import sys
sys.path.append('/opt')
import os
import boto3
import json
import dill
import ast
import base64
import shutil
import time
import pandas as pd 

from boto3 import resource
from boto3.dynamodb.conditions import Key, Attr


# Dynamo Config
dynamo_resource = resource('dynamodb')
dynamo = boto3.client('dynamodb')
METADATA_TABLE   = 'HomeworksMetadata'
TEST_CASES_TABLE = 'HomeworksTestCases'
GRADEBOOK_TABLE  = 'Gradebook'

# Return Codes
SUCCESS = 200
ERROR   = 400

# Request Types
STUDENT_REQUEST = 'STUDENT_GRADE'
ALL_STUDENTS_REQUEST = 'ALL_STUDENTS_GRADES'

    
def lambda_handler(event, context):
    try:
        body = parse_event(event)
        homework_id = body['homework_id']
        print(homework_id)
        deadline, max_daily_submissions, max_score = get_homework_metadata(homework_id)
        if body['request_type'] == ALL_STUDENTS_REQUEST:
            validate_secret_key(body['secret_key'])
            all_grades = get_grades(homework_id)
            response = (all_grades, deadline)
            return build_http_response(SUCCESS,serialize(response))
        elif body['request_type'] == STUDENT_REQUEST:
            student_id = body['student_id']
            grades = get_grades(homework_id, student_id)
            response = (grades, deadline, max_daily_submissions, max_score)
        return build_http_response(SUCCESS,serialize(response))
    except Exception as exception:
        return build_http_response(ERROR, exception)
        

def parse_event(event):
    try:
        return ast.literal_eval(event['body'])
    except:
        raise Exception('Malformed payload.')
      
        
def validate_secret_key(secret_key):
    try:
        response = dynamo.get_item(TableName = 'Classes', Key={'secret_key': {'S': secret_key}})
        return response['Item']['course_id']['S']
    except:
        raise Exception('Secret key is incorrect.')


def get_homework_metadata(homework_id):
    try:
        response = dynamo.get_item(TableName = METADATA_TABLE, Key={'homework_id': {'S': homework_id}})
        return response['Item']['deadline']['S'], \
               response['Item']['max_daily_submissions']['S'], \
               response['Item']['total_score']['S']
    except:
        raise Exception('Homework ID was not found.')


def get_grades(homework_id, student_id = None):
    table = dynamo_resource.Table(GRADEBOOK_TABLE)
    if student_id is not None:
        filtering_exp = Key('homework_id').eq(homework_id) & Attr('student_submission_id').begins_with(student_id)
    else:
        filtering_exp = Key('homework_id').eq(homework_id)
    response = table.scan(FilterExpression=filtering_exp)
    items = response.get('Items')
    return items
    
    
def serialize(obj):
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8") 
    
    
def build_http_response(status_code, message):
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
