"""
    The grades_lambda is the AWS lambda class that will handle grade-related events. Its primary responsibility
    is to take in an event, parse out key details, such as which homework it's relevant to and whether an
    individual student or all students, then return grading details for that homework.

    The basic flow is:

    event happens   =>  lambda_handler is invoked   =>  dynamo DB is updated w/ submission & score
                        > Examine event
                        > Determine intent
                        > Attempt to act on it
                        > Provide status response
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
import pandas as pd

# Dynamo Config
dynamo = boto3.client('dynamodb')
CLASSES_TABLE    = 'Classes'
METADATA_TABLE   = 'HomeworksMetadata'
TEST_CASES_TABLE = 'HomeworksTestCases'

# Return Codes
SUCCESS = 200
ERROR   = 400

# Request types
HOMEWORK_ID_REQUEST     = 'GET_HOMEWORK_ID'
UPDATE_METADATA_REQUEST = 'UPDATE_METADATA'
UPDATE_TESTS_REQUEST    = 'UPDATE_TESTS'
ADD_NEW_COURSE_REQUEST  = 'ADD_NEW_COURSE'


def lambda_handler(event, context):
    """ This lambda handler is meant to take in an event and context, then:

        1. Parse out the homework details: homework_number, secret_key, request_type, payload
        2. Overwrite secret_key and homework_id with their textual versions
        3. Determine which type of request is inbound
            > HOMEWORK_ID_REQUEST:      return the homework ID in string form
            > UPDATE_METADATA_REQUEST:  update the assignment metadata in the dynamo db
            > UPDATE_TESTS_REQUEST:     update the test cases in the dynamo db
    """
    try:
        homework_number, secret_key, request_type, payload = parse_event(event)
        secret_key  = get_course_id(secret_key)
        homework_id = get_homework_id(secret_key, homework_number)

        if request_type == HOMEWORK_ID_REQUEST:
            response = str(homework_id)
        elif request_type == UPDATE_METADATA_REQUEST:
            update_metadata(homework_id, payload)
            response  = 'Success! Metadata updated.\n\n'
            response += 'Total HW Points: {}\n'.format(payload['total_score'])
            response += 'Deadline: {}\n'.format(pd.to_datetime(payload['deadline']))
            response += 'Max daily submissions per test case: {}\n'.format(payload['max_daily_submissions'])
        elif request_type ==  UPDATE_TESTS_REQUEST:
            libraries = get_additional_libraries(payload['libraries'])
            test_cases = payload['test_cases'] 
            update_tests(homework_id, test_cases, libraries)
            response = 'Success: Test cases updated successfully.'
        elif request_type == ADD_NEW_COURSE_REQUEST:
            add_course(payload['secret_key'], payload['course_id'])
            response = 'Success: Course created successfully.'
        return build_http_response(SUCCESS, response)
    except Exception as exception:
        return build_http_response(ERROR, exception)


def parse_event(event):
    """ Simple helper method to parse an event as a dict.
    Returns: (homework_number, secret_key, request_type, payload)

    Payload should contain metadata
    """
    try:
        body = ast.literal_eval(event['body'])
        return body['homework_number'],  \
               body['secret_key'], \
               body['request_type'],  \
               deserialize(body['payload'])
    except:
        raise Exception('Malformed payload.')


def get_course_id(secret_key):
    """ Returns the course ID based on a secret key. Response would look something like: CIS545_Spring_2019
    """
    try:
        response = dynamo.get_item(TableName = CLASSES_TABLE, Key={'secret_key': {'S': secret_key}})
        return response['Item']['course_id']['S']
    except:
        raise Exception('Secret key is incorrect.')


def get_homework_id(course_id, homework_number):
    """ Helper function to get the unique key of a given homework based on where it falls in the
     assignment schedule of a course. Gets appended to the course_id, then returned in long string
     in the fashion of: CIS545_Spring_2019_HW1
    """
    return '{}_HW{}'.format(course_id, homework_number)


def add_course(secret_key, course_id):
    """ Function to create a new course with an ID and secret
    """
    try:
        db_entry = {
            'TableName': CLASSES_TABLE,
            'Item': {
                'secret_key': {
                    'S': secret_key
                },
                'course_id': {
                    'S': course_id
                }
            }
        }
        dynamo.put_item(**db_entry)
    except Exception as e:
        raise Exception('ERROR: Could not create new course. {}'.format(e))


def update_metadata(homework_id, payload):
    """ Function to configure the metadata of a homework. The actual setup
    of the metadata is contained in the payload, but must be in the form:

    {
        max_daily_submissions: -1,
        total_score: -1,
        deadline: ...
    }

    Once parsed, it gets added to the DB or updated if already in existence
    """
    try:
        db_entry = {
            'TableName': METADATA_TABLE,
            'Item': {
                'homework_id': {
                    'S': homework_id
                },
                'max_daily_submissions' : {
                    'S' : str(payload['max_daily_submissions'])
                },
                'total_score' : {
                    'S':str(payload['total_score'])
                    
                },
                'deadline' : {
                    'S':str(payload['deadline'])
                }
            }
        }
        dynamo.put_item(**db_entry)
    except Exception as exception:
        raise Exception('Metadata upload failed. Try again in a bit or ask an admin.')  


def update_tests(homework_id, test_cases, libraries):
    """ This adds a test case to the dynamo DB to be returned later in grading
    """
    try:
        db_entry = {
            'TableName': TEST_CASES_TABLE,
            'Item': {
                'homework_id': {
                    'S': homework_id
                },
                'test_cases': {
                    'S': serialize(test_cases)
                },
                'libraries' : {
                    'S' : serialize(libraries)
                }
            }
        }
        dynamo.put_item(**db_entry)
    except Exception as exception:
        raise Exception('Test cases upload failed. Try again in a bit or ask an admin.')  


def get_additional_libraries(libraries): # TO-FINISH #
    """ Appears unfinished per comment, but imports libraries required for use in grading
    """
    try:
        packages = libraries['packages']
        imports = libraries['imports']
        functions = libraries['functions']
        
        for package in packages:
            if package not in globals() and 'penngrader' not in package:
                print('Importing base package: ' + package)
                globals()[package] = __import__(package, globals(), locals(), ['*'])
        
        for package, shortname in imports:
            if shortname not in globals() and 'penngrader' not in package:
                print('Importing: ' + package + ' as ' + shortname)
                globals()[shortname] = __import__(package, globals(), locals(), ['*'])
        
        for package, function_name in functions:
            print('Importing function: ' + function_name + ' from ' + package)
            globals()[function_name] = eval(package + "." + function_name)
    except Exception as exception:
        error_message = '[{}] is not currently supported. '.format(str(exception).split("'")[1])
        error_message += 'Reset Jupyter runtime to clear imported modules.'
        raise Exception(error_message)
    return libraries


def serialize(obj):
    """ Simple helper method to encode a serialized object

    Code is duplicated here. Possibly because the other file may not always be
    accessible?
    """
    byte_serialized = dill.dumps(obj, recurse = True)
    return base64.b64encode(byte_serialized).decode("utf-8") 
    

def deserialize(obj):
    """ Simple helper method to decode a base64 encoded object

    Code is duplicated here. Possibly because the other file may not always be
    accessible?
    """
    byte_decoded = base64.b64decode(obj)
    return dill.loads(byte_decoded)
    

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
    
    
# SAVING THIS HERE FOR LIBS FUNCTION, I SHALL GET TO IT SOON
# s3 = boto3.client('s3')
# def install_libraries(libraries):
#     os.system('rm -r /tmp/*')
#     print(os.system('mkdir /tmp/additional_libs'))
#     for package, nickname in libraries:
#         print(os.system('du -sh /tmp'))
#         os.system('pip install ' + package +  ' -t /tmp/additional_libs/')
#     shutil.make_archive("/tmp/" + 'libs' , 'zip', '/tmp/additional_libs/')
#     s3.upload_file('/tmp/' + 'libs' + '.zip','penngrader-libraries',  'libs.zip')
