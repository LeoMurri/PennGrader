"""
    The grades_lambda is the AWS lambda class that will handle grade-related events. Its primary responsibility
    is to take in an event, parse out key details, such as which homework it's relevant to and whether an
    individual student or all students, then return grading details for that homework.

    The basic flow is:

    event happens   =>  lambda_handler is invoked   =>  dynamo DB is updated w/ submission & score
                        > Examine event
                        > Determine scope (single vs.
                            all students)
                        > Return http response
"""

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
    """ This lambda handler is meant to take in an event and context, then:

        1. Parse out the event details, then get the ID of the homework: body, homework_id
        2. Get all associated metadata for the homework: deadline, max_daily_submissions, max_score
        3. Check the request type:
           > ALL_STUDENTS_REQUEST:  validate the secret, then retrieve the grades and return http response of
                                    (all_grades, deadline)
           > STUDENT_REQUEST:       retrieve a single student's grade for an assignment, return http response of
                                    (grades, deadline, max_daily_submissions, max_score)
    """
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
    """ Simple helper method to parse an event as a dict.
    Returns: entire event
    """
    try:
        return ast.literal_eval(event['body'])
    except:
        raise Exception('Malformed payload.')
      
        
def validate_secret_key(secret_key):
    """ Simple method to confirm that the secret_key passed in is valid
    """
    try:
        response = dynamo.get_item(TableName = 'Classes', Key={'secret_key': {'S': secret_key}})
        return response['Item']['course_id']['S']
    except:
        raise Exception('Secret key is incorrect.')


def get_homework_metadata(homework_id):
    """ Retrieves the metadata for a homework, including deadline, max_daily_subimssions, and the total_score
    """
    try:
        response = dynamo.get_item(TableName = METADATA_TABLE, Key={'homework_id': {'S': homework_id}})
        return response['Item']['deadline']['S'], \
               response['Item']['max_daily_submissions']['S'], \
               response['Item']['total_score']['S']
    except:
        raise Exception('Homework ID was not found.')


def get_grades(homework_id, student_id = None):
    """ Retrieve the grades for a given homework using the student's ID. This will hit the
    dynamo DB and pull down the student's current score on a particular assignment.

    Note: if student_id is None, grades for all students are returned
    """
    table = dynamo_resource.Table(GRADEBOOK_TABLE)
    if student_id is not None:
        filtering_exp = Key('homework_id').eq(homework_id) & Attr('student_submission_id').begins_with(student_id)
    else:
        filtering_exp = Key('homework_id').eq(homework_id)
    response = table.scan(FilterExpression=filtering_exp)
    items = response.get('Items')
    return items
    
    
def serialize(obj):
    """ Simple helper method to encode a serialized object

    Code is duplicated here. Possibly because the other file may not always be
    accessible?
    """
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8") 
    
    
def build_http_response(status_code, message):
    """ Build formatted http response as string

    Code is duplicated here. Possibly because the other file may not always be
    accessible?
    """
    return { 
        'statusCode': status_code,
        'body': str(message),
        'headers': {
            'Content-Type': 'application/json',
        }
    }
